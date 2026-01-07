import { useState, useEffect, useRef } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import { usePapers, usePaperEntities } from '../hooks/usePaperData';
import { useRelationProvenance } from '../hooks/useRelationSearch';
import { PDFViewer } from '../components/pdf-viewer';
import { ViewModeToggle } from '../components/pdf-viewer/ViewModeToggle';
import { AnnotatedView, type SelectedContent } from '../components/annotated-view/AnnotatedView';
import { EntityTypeBadge } from '../components/entities';
import { RelationDetail } from '../components/relations';
import { RubricReviewModal } from '../components/review/RubricReviewModal';
import { reviewText, reviewFigure, reviewTable, reviewFullPaper } from '../services/api/review';
import type { EntityType, Relation } from '../types';
import type { RubricName, ReviewResponse } from '../types/review';
import { RUBRIC_OPTIONS } from '../types/review';

// Navigation state type for relation highlighting
interface HighlightRelationState {
  pages: number[];
  section?: string;
  subject: string;
  predicate: string;
  object: string;
}

export const PaperView = () => {
  const { id } = useParams<{ id: string }>();
  const location = useLocation();
  const navigate = useNavigate();
  const { data: papers, isLoading, error } = usePapers();
  const decodedId = decodeURIComponent(id || '');
  
  // Try to match by id first, then by filename as fallback
  const paper = papers?.find(p => 
    p.id === decodedId || p.filename === decodedId
  );
  
  // Debug logging
  console.log('[PaperView] URL id:', id);
  console.log('[PaperView] Decoded id:', decodedId);
  console.log('[PaperView] Available papers:', papers?.map(p => ({ id: p.id, filename: p.filename })));
  console.log('[PaperView] Found paper:', paper);
  
  // Ref for dropdown to handle click outside
  const dropdownRef = useRef<HTMLDivElement>(null);
  
  // Fetch entities and relations for this paper
  const { data: entitiesData, isLoading: entitiesLoading } = usePaperEntities(
    paper?.id || '',
    undefined,
    !!paper
  );

  // State for view mode and selected relation
  const [viewMode, setViewMode] = useState<'reference' | 'annotated'>('reference');
  const [selectedRelation, setSelectedRelation] = useState<Relation | null>(null);
  
  // State for selection-based relations (from annotated view clicks)
  const [selectionRelations, setSelectionRelations] = useState<Relation[]>([]);
  const [selectedContent, setSelectedContent] = useState<SelectedContent | null>(null);
  const [isLoadingSelection, setIsLoadingSelection] = useState(false);
  
  // State for rubric review
  const [showReviewModal, setShowReviewModal] = useState(false);
  const [showRubricDropdown, setShowRubricDropdown] = useState(false);
  const [selectedRubric, setSelectedRubric] = useState<RubricName | null>(null);
  const [rubricReview, setRubricReview] = useState<ReviewResponse | null>(null);
  const [isReviewLoading, setIsReviewLoading] = useState(false);
  const [reviewError, setReviewError] = useState<string | null>(null);
  const [selectedTextForReview, setSelectedTextForReview] = useState<string>('');
  const [selectedContentForReview, setSelectedContentForReview] = useState<SelectedContent | null>(null);
  
  // State for full paper review
  const [showFullPaperDropdown, setShowFullPaperDropdown] = useState(false);
  const fullPaperDropdownRef = useRef<HTMLDivElement>(null);
  
  // State for relation highlighting from navigation
  const [highlightRelation, setHighlightRelation] = useState<HighlightRelationState | null>(null);
  
  // Fetch provenance for selected relation
  const { data: provenanceData } = useRelationProvenance(
    selectedRelation?.id || '',
    !!selectedRelation
  );
  
  // Only display relations when something is selected (no auto-population from page)
  const displayRelations = selectedContent ? selectionRelations : [];
  const displayTitle = selectedContent 
    ? "Relations in Selection" 
    : "Relations";
  
  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowRubricDropdown(false);
      }
      if (fullPaperDropdownRef.current && !fullPaperDropdownRef.current.contains(event.target as Node)) {
        setShowFullPaperDropdown(false);
      }
    };
    
    if (showRubricDropdown || showFullPaperDropdown) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [showRubricDropdown, showFullPaperDropdown]);
  
  // Handle incoming navigation from graph view to highlight a specific relation
  useEffect(() => {
    const highlightState = location.state as { highlightRelation?: HighlightRelationState } | null;
    
    if (!highlightState?.highlightRelation || !paper) {
      return;
    }
    
    const { pages, subject, predicate, object: obj } = highlightState.highlightRelation;
    
    console.log('[PaperView] Highlighting relation from navigation:', {
      pages,
      subject,
      predicate,
      object: obj
    });
    
    // Switch to annotated view
    setViewMode('annotated');
    
    // Set the highlight relation state - AnnotatedView will handle the search
    setHighlightRelation({
      pages,
      subject,
      predicate,
      object: obj
    });
    
    // Clear the navigation state so it doesn't re-trigger on re-renders
    window.history.replaceState({}, document.title);
  }, [location.state, paper]);
  
  // Callback for annotated view to update relations based on selection
  const handleRelationsUpdate = (relations: Relation[], content: SelectedContent | null) => {
    setSelectionRelations(relations);
    setSelectedContent(content);
    
    // If relations are cleared (user closed sidebar), clear the highlight
    if (relations.length === 0 && highlightRelation) {
      console.log('[PaperView] Relations cleared, removing highlight');
      setHighlightRelation(null);
    }
    
    // Store the content data for review
    if (content) {
      setSelectedTextForReview(content.preview);
      setSelectedContentForReview(content); // Store full content object with image/table data
    }
    // Clear review state when new content is selected
    setShowReviewModal(false);
    setRubricReview(null);
    setReviewError(null);
    setShowRubricDropdown(false);
  };
  
  // Clear selection handler
  const handleClearSelection = () => {
    setSelectedContent(null);
    setSelectionRelations([]);
    setHighlightRelation(null); // Clear the blue highlight
    // Also clear review state when selection is cleared
    setShowReviewModal(false);
    setRubricReview(null);
    setReviewError(null);
  };
  
  // Review button click - toggle dropdown
  const handleReviewClick = () => {
    setShowRubricDropdown(!showRubricDropdown);
  };
  
  // Rubric selection and review execution
  const handleRubricSelect = async (rubricName: RubricName) => {
    setShowRubricDropdown(false);
    setSelectedRubric(rubricName);
    setShowReviewModal(true);
    setIsReviewLoading(true);
    setReviewError(null);
    setRubricReview(null);
    
    if (!selectedContentForReview) {
      setReviewError('No content selected for review');
      setIsReviewLoading(false);
      return;
    }
    
    try {
      let review: ReviewResponse;
      
      console.log('[PaperView] Starting review:', {
        contentType: selectedContentForReview.type,
        rubric: rubricName,
        hasImageData: !!selectedContentForReview.imageData,
        hasTableData: !!selectedContentForReview.tableData
      });
      
      // Route to appropriate API based on content type
      if (selectedContentForReview.type === 'text') {
        const textToReview = selectedTextForReview || selectedContentForReview.preview || '';
        review = await reviewText(textToReview, rubricName);
      } else if (selectedContentForReview.type === 'figure') {
        if (!selectedContentForReview.imageData) {
          throw new Error('Figure image data not available. Please wait for the figure to load.');
        }
        review = await reviewFigure(selectedContentForReview.imageData, rubricName);
      } else if (selectedContentForReview.type === 'table') {
        if (!selectedContentForReview.tableData) {
          throw new Error('Table data not available');
        }
        review = await reviewTable(selectedContentForReview.tableData, rubricName);
      } else {
        throw new Error(`Unsupported content type: ${selectedContentForReview.type}`);
      }
      
      console.log('[PaperView] Review received:', review);
      setRubricReview(review);
    } catch (err) {
      console.error('[PaperView] Review failed:', err);
      setReviewError(err instanceof Error ? err.message : 'Failed to generate review. Please try again.');
    } finally {
      setIsReviewLoading(false);
    }
  };
  
  // Full paper review button click - toggle dropdown
  const handleFullPaperReviewClick = () => {
    setShowFullPaperDropdown(!showFullPaperDropdown);
  };
  
  // Full paper rubric selection and review execution
  const handleFullPaperRubricSelect = async (rubricName: RubricName) => {
    if (!paper) return;
    
    setShowFullPaperDropdown(false);
    setSelectedRubric(rubricName);
    setShowReviewModal(true);
    setIsReviewLoading(true);
    setReviewError(null);
    setRubricReview(null);
    
    try {
      console.log('[PaperView] Starting full paper review:', {
        paper: paper.filename,
        rubric: rubricName
      });
      
      const review = await reviewFullPaper(paper.filename, rubricName);
      
      console.log('[PaperView] Full paper review received:', review);
      setRubricReview(review);
    } catch (err) {
      console.error('[PaperView] Full paper review failed:', err);
      setReviewError(err instanceof Error ? err.message : 'Failed to generate review. Please try again.');
    } finally {
      setIsReviewLoading(false);
    }
  };
  
  // Retry review
  const handleReviewRetry = () => {
    if (selectedRubric) {
      handleRubricSelect(selectedRubric);
    }
  };
  
  // Handle "View in Graph" button click
  const handleViewInGraph = () => {
    if (!selectedRelation) return;
    
    console.log('[PaperView] Navigating to graph with relation:', {
      subject: selectedRelation.subject.name,
      predicate: selectedRelation.predicate,
      object: selectedRelation.object.name
    });
    
    // Navigate to graph view with entity and predicate info
    navigate('/graph', {
      state: {
        loadRelation: {
          subjectId: selectedRelation.subject.id,
          subjectName: selectedRelation.subject.name,
          predicate: selectedRelation.predicate,
          objectId: selectedRelation.object.id,
          objectName: selectedRelation.object.name,
        }
      }
    });
  };
  
  // Close review modal
  const handleReviewClose = () => {
    setShowReviewModal(false);
    setRubricReview(null);
    setReviewError(null);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-gray-600 dark:text-gray-400">Loading paper...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-red-600 dark:text-red-400">Error: {error.message}</p>
      </div>
    );
  }

  if (!paper) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-gray-600 dark:text-gray-400">Paper not found</p>
      </div>
    );
  }

  return (
    <div className="h-full relative bg-white dark:bg-gray-900">
      <div className="h-full flex flex-row">
        {/* Main Content Section */}
        <div className="flex-1 h-full flex flex-col min-w-0 bg-gray-50 dark:bg-gray-800">
          {/* View Mode Toggle */}
          <div className="p-4 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 flex items-center gap-4 shrink-0">
            <div className="flex-shrink-0">
              <ViewModeToggle mode={viewMode} onModeChange={setViewMode} />
            </div>
            <div className="flex-1 min-w-0">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white truncate">
                {paper.title || paper.filename}
              </h2>
            </div>
            
            {/* Full Paper Review Button */}
            <div className="relative flex-shrink-0" ref={fullPaperDropdownRef}>
              <button
                onClick={handleFullPaperReviewClick}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Review Full Paper
              </button>
              
              {/* Rubric Dropdown for Full Paper */}
              {showFullPaperDropdown && (
                <div className="absolute right-0 mt-2 w-64 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-50">
                  <div className="p-2">
                    <div className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase px-2 py-1">
                      Select Rubric
                    </div>
                    {RUBRIC_OPTIONS.map((rubric) => (
                      <button
                        key={rubric.value}
                        onClick={() => handleFullPaperRubricSelect(rubric.value)}
                        className="w-full text-left px-3 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
                      >
                        <div className="font-medium text-gray-900 dark:text-white">
                          {rubric.label}
                        </div>
                        <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                          {rubric.description}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Conditional View Based on Mode */}
          <div className="flex-1 overflow-hidden">
            {viewMode === 'reference' ? (
              <PDFViewer 
                filename={paper.filename}
                bboxes={provenanceData?.bbox_data || []}
              />
            ) : (
              <AnnotatedView
                paperFilename={paper.filename}
                pdfUrl={`/papers/${paper.filename}`}
                onRelationsUpdate={handleRelationsUpdate}
                onLoadingChange={setIsLoadingSelection}
                highlightRelation={highlightRelation || undefined}
              />
            )}
          </div>
        </div>

        {/* Entity Panel Section */}
        <div className="w-80 lg:w-96 h-full shrink-0 flex flex-col bg-white dark:bg-gray-800 border-l border-gray-200 dark:border-gray-700">
          <div className="p-6 overflow-y-auto flex-1">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Entities & Relations
            </h3>
        
        {entitiesLoading ? (
          <p className="text-sm text-gray-600 dark:text-gray-400">Loading entities...</p>
        ) : (
          <>
            <div className="space-y-4 mb-6">
              <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  <span className="font-medium text-gray-900 dark:text-white">{paper.total_entities}</span> entities extracted
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  <span className="font-medium text-gray-900 dark:text-white">{paper.total_relations}</span> relations found
                </p>
              </div>
            </div>

            {/* Entity Type Breakdown */}
            {entitiesData && entitiesData.entities && entitiesData.entities.length > 0 && (
              <div className="space-y-3">
                <h4 className="text-sm font-semibold text-gray-900 dark:text-white">
                  Entities by Type
                </h4>
                {(() => {
                  // Group entities by type
                  const entityCounts = entitiesData.entities.reduce((acc, entity) => {
                    acc[entity.type] = (acc[entity.type] || 0) + 1;
                    return acc;
                  }, {} as Record<string, number>);

                  // Sort by count descending
                  const sortedTypes = Object.entries(entityCounts)
                    .sort(([, a], [, b]) => b - a);

                  return sortedTypes.map(([type, count]) => (
                    <EntityTypeBadge key={type} type={type as EntityType} count={count} />
                  ));
                })()}
              </div>
            )}

            {/* Selection Header (when content is selected) - shown regardless of relations */}
            {selectedContent && (
              <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
                <div className="mb-4 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="text-xs text-gray-600 dark:text-gray-400 mb-1">
                        Selected Content
                      </div>
                      <div className="text-sm font-medium text-gray-900 dark:text-white break-words">
                        {selectedContent.preview}
                      </div>
                      {isLoadingSelection ? (
                        <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                          Loading relations...
                        </div>
                      ) : (
                        <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                          {selectionRelations.length} relation{selectionRelations.length !== 1 ? 's' : ''} found
                        </div>
                      )}
                    </div>
                    <div className="flex flex-shrink-0 gap-2">
                      {/* Review Button - show for text, figures, and tables */}
                      <div className="relative" ref={dropdownRef}>
                        <button
                          onClick={handleReviewClick}
                          className="px-3 py-1.5 bg-purple-600 hover:bg-purple-700 text-white text-sm font-medium rounded transition-colors"
                          aria-label="Review with rubric"
                        >
                          Review
                        </button>
                        
                        {/* Rubric Dropdown */}
                        {showRubricDropdown && (
                          <div className="absolute right-0 mt-2 w-64 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-[100]">
                            <div className="p-2">
                              <div className="text-xs font-semibold text-gray-700 dark:text-gray-300 px-2 py-1 mb-1">
                                Select Rubric
                                </div>
                                {RUBRIC_OPTIONS.map((rubric) => (
                                  <button
                                    key={rubric.value}
                                    onClick={() => handleRubricSelect(rubric.value)}
                                    className="w-full text-left px-3 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
                                  >
                                    <div className="font-medium text-sm text-gray-900 dark:text-white">
                                      {rubric.label}
                                    </div>
                                    <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                                      {rubric.description}
                                    </div>
                                  </button>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      
                      <button
                        onClick={handleClearSelection}
                        className="flex-shrink-0 p-1 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                        aria-label="Clear selection"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Relations List - only shown when relations exist */}
            {displayRelations.length > 0 && (
              <div className={selectedContent ? "space-y-3" : "mt-6 pt-6 border-t border-gray-200 dark:border-gray-700 space-y-3"}>
                
                <h4 className="text-sm font-semibold text-gray-900 dark:text-white">
                  {displayTitle} ({displayRelations.length})
                </h4>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {displayRelations.map((relation) => (
                    <button
                      key={relation.id}
                      onClick={() => setSelectedRelation(relation)}
                      className="w-full text-left p-3 bg-gray-50 dark:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600 rounded transition-colors border border-transparent hover:border-purple-300 dark:hover:border-purple-600"
                    >
                      <div className="space-y-1">
                        <div className="flex items-baseline gap-2">
                          <span className="text-xs text-gray-500 dark:text-gray-400">Subject:</span>
                          <span className="text-sm font-medium text-gray-900 dark:text-white truncate">
                            {relation.subject.name}
                          </span>
                        </div>
                        <div className="flex items-baseline gap-2">
                          <span className="text-xs text-gray-500 dark:text-gray-400">Predicate:</span>
                          <span className="text-sm font-semibold text-purple-600 dark:text-purple-400 truncate">
                            {relation.predicate}
                          </span>
                        </div>
                        <div className="flex items-baseline gap-2">
                          <span className="text-xs text-gray-500 dark:text-gray-400">Object:</span>
                          <span className="text-sm font-medium text-gray-900 dark:text-white truncate">
                            {relation.object.name}
                          </span>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}
            
            {/* Empty state for selection with no relations */}
            {selectedContent && !isLoadingSelection && selectionRelations.length === 0 && (
              <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
                <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg">
                  <div className="flex items-start justify-between gap-2 mb-4">
                    <div className="flex-1 min-w-0">
                      <div className="text-xs text-gray-600 dark:text-gray-400 mb-1">
                        Selected Content
                      </div>
                      <div className="text-sm font-medium text-gray-900 dark:text-white break-words">
                        {selectedContent.preview}
                      </div>
                    </div>
                    <button
                      onClick={handleClearSelection}
                      className="flex-shrink-0 p-1 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                      aria-label="Clear selection"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                  <p className="text-sm text-gray-500 dark:text-gray-400 italic">
                    No relations found for this selection
                  </p>
                </div>
              </div>
            )}

            {/* Selected Relation Detail */}
            {selectedRelation && (
              <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
                <RelationDetail
                  relation={selectedRelation}
                  onClose={() => setSelectedRelation(null)}
                  onViewInGraph={handleViewInGraph}
                />
              </div>
            )}

            <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
              <p className="text-sm text-gray-500 dark:text-gray-400 italic">
                {viewMode === 'annotated' 
                  ? 'Click on sentences, figures, or tables to see their relations.'
                  : 'Click on text in the PDF to see detailed entity and relation information.'}
              </p>
            </div>
          </>
        )}
        </div>
      </div>
      </div>
      
      {/* Rubric Review Modal - outside main container for proper z-index */}
      <RubricReviewModal
        isOpen={showReviewModal}
        selectedContent={selectedContentForReview}
        review={rubricReview}
        loading={isReviewLoading}
        error={reviewError}
        onClose={handleReviewClose}
        onRetry={handleReviewRetry}
      />
    </div>
  );
};
