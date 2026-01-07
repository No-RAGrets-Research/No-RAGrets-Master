/**
 * AnnotatedView - Displays document content from Docling JSON with clickable text/figures
 */

import { useEffect, useState, useRef } from "react";
import { DoclingRenderer } from "./DoclingRenderer";
import { loadDoclingData, parseDoclingDocument, type DoclingText, type DoclingPicture, type DoclingTable, type ParsedDocument } from "@/utils/docling";
import { getRelationsByText, getRelationsByLocation, getRelationsByFigure, getRelationsByTable, getRelationSourceSpan } from "@/services/api/relations";
import type { Relation } from "@/types";

export interface SelectedContent {
  type: 'text' | 'figure' | 'table';
  preview: string;
  imageData?: string; // For figures - base64 data URL
  tableData?: DoclingTable; // For tables - Docling table object
}

interface AnnotatedViewProps {
  paperFilename: string;
  pdfUrl?: string;
  onRelationsUpdate?: (relations: Relation[], selectedContent: SelectedContent | null) => void;
  onLoadingChange?: (loading: boolean) => void;
  highlightRelation?: {
    pages?: number[]; // Page numbers where relation appears
    subject: string;
    predicate: string;
    object: string;
  };
}

export function AnnotatedView({ paperFilename, pdfUrl, onRelationsUpdate, onLoadingChange, highlightRelation }: AnnotatedViewProps) {
  const [parsedDoc, setParsedDoc] = useState<ParsedDocument | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedBlock, setSelectedBlock] = useState<DoclingText | DoclingPicture | DoclingTable | null>(null);
  const [selectedSentences, setSelectedSentences] = useState<Set<string>>(new Set());
  const [isLocating, setIsLocating] = useState(false); // Track auto-scroll in progress
  const [isApproximateMatch, setIsApproximateMatch] = useState(false); // Track if match is approximate
  
  // Track which relation we've already searched for to prevent infinite loops
  const processedRelationRef = useRef<string | null>(null);

  console.log('[AnnotatedView] Initializing with:', { paperFilename, pdfUrl, highlightRelation });

  useEffect(() => {
    async function loadDocument() {
      try {
        setLoading(true);
        setError(null);

        // Load and parse docling JSON
        const doclingData = await loadDoclingData(paperFilename);
        const parsed = parseDoclingDocument(doclingData);

        console.log('[AnnotatedView] Document parsed:', {
          totalItems: parsed.items.length,
          pictures: parsed.pictures.length,
          texts: parsed.texts.length,
          tables: parsed.tables.length
        });

        setParsedDoc(parsed);
      } catch (err) {
        console.error("Failed to load docling document:", err);
        setError(err instanceof Error ? err.message : "Failed to load document");
      } finally {
        setLoading(false);
      }
    }

    loadDocument();
  }, [paperFilename]);

  // Clear highlight when highlightRelation is removed
  useEffect(() => {
    if (!highlightRelation) {
      console.log('[AnnotatedView] Highlight relation cleared, removing selection');
      setSelectedBlock(null);
      setSelectedSentences(new Set());
      setIsApproximateMatch(false); // Reset approximate match flag
      processedRelationRef.current = null; // Reset so it can be searched again if needed
    }
  }, [highlightRelation]);

  // Handle programmatic relation highlighting from navigation
  useEffect(() => {
    if (!highlightRelation || !parsedDoc) {
      return;
    }

    // Create a unique key for this relation to prevent duplicate searches
    const relationKey = `${highlightRelation.subject}|${highlightRelation.predicate}|${highlightRelation.object}`;
    
    // Skip if we've already processed this exact relation
    if (processedRelationRef.current === relationKey) {
      console.log('[AnnotatedView] Skipping duplicate search for:', relationKey);
      return;
    }

    console.log('[AnnotatedView] Auto-searching for relation:', highlightRelation);
    processedRelationRef.current = relationKey;

    const searchForRelation = async () => {
      if (onLoadingChange) {
        onLoadingChange(true);
      }

      try {
        const paperId = paperFilename; // Use the current paper filename for filtering
        let targetRelation = null;
        
        // Try multiple search strategies since backend text search can be inconsistent
        const searchStrategies = [
          highlightRelation.subject,    // Try subject first
          highlightRelation.object,      // Try object if subject fails
          highlightRelation.predicate,   // Try predicate as last resort
        ];

        for (const searchText of searchStrategies) {
          console.log('[AnnotatedView] Searching for:', searchText);
          const relations = await getRelationsByText(searchText);
          console.log('[AnnotatedView] Found', relations.length, 'relations matching search');

          // Filter to only relations from THIS paper
          const relationsFromThisPaper = relations.filter(r => r.source_paper === paperId);
          console.log('[AnnotatedView] Found', relationsFromThisPaper.length, 'relations from this paper:', paperId);

          // Look for exact match
          targetRelation = relationsFromThisPaper.find(r =>
            r.subject.name === highlightRelation.subject &&
            r.predicate === highlightRelation.predicate &&
            r.object.name === highlightRelation.object
          );

          if (targetRelation) {
            console.log('[AnnotatedView] ✓ Found exact relation using search term:', searchText);
            break; // Found it, stop searching
          }
        }

        // FALLBACK: If exact match not found, try finding ANY relation between subject and object
        if (!targetRelation) {
          console.log('[AnnotatedView] Exact match failed, trying fallback: any relation between subject and object');
          
          for (const searchText of [highlightRelation.subject, highlightRelation.object]) {
            const relations = await getRelationsByText(searchText);
            const relationsFromThisPaper = relations.filter(r => r.source_paper === paperId);
            
            // Look for any relation that has matching subject AND object (ignore predicate)
            targetRelation = relationsFromThisPaper.find(r =>
              (r.subject.name === highlightRelation.subject && r.object.name === highlightRelation.object) ||
              (r.subject.name === highlightRelation.object && r.object.name === highlightRelation.subject) // Try reversed
            );
            
            if (targetRelation) {
              console.log('[AnnotatedView] ✓ Found relation with matching entities (different predicate):', targetRelation.predicate);
              break;
            }
          }
        }

        // FINAL FALLBACK: Search by page if we have page numbers
        if (!targetRelation && highlightRelation.pages && highlightRelation.pages.length > 0) {
          console.log('[AnnotatedView] Text search failed, trying page-based search for pages:', highlightRelation.pages);
          
          for (const pageNum of highlightRelation.pages) {
            const pageRelations = await getRelationsByLocation(paperId, pageNum);
            console.log('[AnnotatedView] Found', pageRelations.length, 'relations on page', pageNum);
            
            // Look for exact match on this page
            targetRelation = pageRelations.find(r =>
              r.subject.name === highlightRelation.subject &&
              r.predicate === highlightRelation.predicate &&
              r.object.name === highlightRelation.object
            );
            
            if (targetRelation) {
              console.log('[AnnotatedView] ✓ Found exact relation via page search');
              break;
            }
            
            // If still no exact match, try matching just subject and object
            if (!targetRelation) {
              targetRelation = pageRelations.find(r =>
                (r.subject.name === highlightRelation.subject && r.object.name === highlightRelation.object) ||
                (r.subject.name === highlightRelation.object && r.object.name === highlightRelation.subject)
              );
              
              if (targetRelation) {
                console.log('[AnnotatedView] ✓ Found relation via page search (different predicate):', targetRelation.predicate);
                break;
              }
            }
          }
        }

        if (targetRelation) {
          console.log('[AnnotatedView] ✓ Found exact relation, highlighting it');
          
          // Reset approximate match flag since we found exact match
          setIsApproximateMatch(false);
          
          // Fetch the source span to get the docling_ref and text evidence
          try {
            const sourceSpan = await getRelationSourceSpan(targetRelation.id);
            console.log('[AnnotatedView] Source span:', {
              docling_ref: sourceSpan.source_span.docling_ref,
              text: sourceSpan.source_span.text_evidence.substring(0, 100) + '...',
              chunk_id: sourceSpan.source_span.location.chunk_id
            });

            const evidenceText = sourceSpan.source_span.text_evidence;
            
            // Update sidebar with relation info
            if (onRelationsUpdate) {
              onRelationsUpdate([targetRelation], {
                type: 'text',
                preview: evidenceText.substring(0, 200) + (evidenceText.length > 200 ? '...' : '')
              });
            }

            // HIGHLIGHT & SCROLL: Use docling_ref for direct DOM selection
            if (sourceSpan.source_span.docling_ref) {
              console.log('[AnnotatedView] Using docling_ref for direct lookup:', sourceSpan.source_span.docling_ref);
              
              // Determine element type from docling_ref
              const refType = sourceSpan.source_span.docling_ref.split('/')[1]; // 'texts', 'pictures', or 'tables'
              let matchingElement = null;
              
              // Find the matching element based on type
              if (refType === 'texts') {
                matchingElement = parsedDoc.texts.find(t => t.self_ref === sourceSpan.source_span.docling_ref);
              } else if (refType === 'pictures') {
                matchingElement = parsedDoc.pictures.find(p => p.self_ref === sourceSpan.source_span.docling_ref);
              } else if (refType === 'tables') {
                matchingElement = parsedDoc.tables.find(t => t.self_ref === sourceSpan.source_span.docling_ref);
              }
              
              if (matchingElement) {
                console.log('[AnnotatedView] Found matching element:', matchingElement.self_ref);
                setSelectedBlock(matchingElement);
                setIsLocating(true); // Show "Locating..." indicator
                
                // Simplified scroll with shorter delays since direct lookup is fast
                const scrollToElement = (retries = 0, maxRetries = 3) => {
                  setTimeout(() => {
                    const element = document.querySelector(`[data-docling-ref="${sourceSpan.source_span.docling_ref}"]`);
                    if (element) {
                      console.log('[AnnotatedView] Scrolling to element:', sourceSpan.source_span.docling_ref);
                      element.scrollIntoView({ 
                        behavior: 'smooth', 
                        block: 'center' 
                      });
                      setIsLocating(false); // Hide indicator after successful scroll
                    } else if (retries < maxRetries) {
                      console.log(`[AnnotatedView] Element not ready yet, retrying... (${retries + 1}/${maxRetries})`);
                      scrollToElement(retries + 1, maxRetries);
                    } else {
                      console.warn('[AnnotatedView] Could not find DOM element after retries:', sourceSpan.source_span.docling_ref);
                      setIsLocating(false); // Hide indicator even if failed
                    }
                  }, retries === 0 ? 100 : 300); // Short initial delay, longer for retries
                };
                
                scrollToElement();
              } else {
                console.warn('[AnnotatedView] No matching element found for docling_ref:', sourceSpan.source_span.docling_ref);
                setIsLocating(false);
              }
            } else {
              console.warn('[AnnotatedView] No docling_ref available, falling back to text matching');
              
              // FALLBACK: Use text matching if docling_ref not available (legacy support)
              const matchingTexts = parsedDoc.texts.filter(t => {
                const textContent = t.text.trim();
                const evidenceStart = evidenceText.substring(0, 100).trim();
                
                // Direct substring match
                if (evidenceText.includes(textContent) || textContent.includes(evidenceStart)) {
                  return true;
                }
                
                // Split into sentences and check overlap
                const sentences = evidenceText.split(/[.!?]+/).filter(s => s.trim().length > 20);
                for (const sentence of sentences) {
                  const cleanSentence = sentence.trim();
                  if (cleanSentence && textContent.includes(cleanSentence.substring(0, 30))) {
                    return true;
                  }
                  if (cleanSentence && cleanSentence.includes(textContent.substring(0, 30))) {
                    return true;
                  }
                }
                
                return false;
              });

              console.log('[AnnotatedView] Found', matchingTexts.length, 'matching text blocks via fallback');
              
              if (matchingTexts.length > 0) {
                const firstMatch = matchingTexts[0];
                setSelectedBlock(firstMatch);
                setIsLocating(true);
                
                const scrollToElement = (retries = 0, maxRetries = 3) => {
                  setTimeout(() => {
                    const element = document.querySelector(`[data-docling-ref="${firstMatch.self_ref}"]`);
                    if (element) {
                      console.log('[AnnotatedView] Scrolling to matched text block:', firstMatch.self_ref);
                      element.scrollIntoView({ 
                        behavior: 'smooth', 
                        block: 'center' 
                      });
                      setIsLocating(false);
                    } else if (retries < maxRetries) {
                      scrollToElement(retries + 1, maxRetries);
                    } else {
                      console.warn('[AnnotatedView] Could not find DOM element after retries:', firstMatch.self_ref);
                      setIsLocating(false);
                    }
                  }, retries === 0 ? 100 : 300);
                };
                
                scrollToElement();
              } else {
                console.warn('[AnnotatedView] No matching text blocks found via fallback');
                setIsLocating(false);
              }
            }
          } catch (spanErr) {
            console.error('[AnnotatedView] Failed to fetch source span:', spanErr);
            
            // Fallback: just show the relation without source text
            if (onRelationsUpdate) {
              onRelationsUpdate([targetRelation], {
                type: 'text',
                preview: `${highlightRelation.subject} → ${highlightRelation.predicate} → ${highlightRelation.object}`
              });
            }
          }
        } else {
          console.warn('[AnnotatedView] ✗ Could not find exact relation match');
          console.warn('[AnnotatedView] Looking for:', {
            subject: highlightRelation.subject,
            predicate: highlightRelation.predicate,
            object: highlightRelation.object,
            paper: paperFilename
          });
          console.warn('[AnnotatedView] Tried search terms:', [
            highlightRelation.subject,
            highlightRelation.object,
            highlightRelation.predicate
          ]);
          
          // FALLBACK: Try to find approximate location
          console.log('[AnnotatedView] Attempting approximate match fallback...');
          
          let approximateBlock = null;
          let fallbackMessage = '';
          
          // Strategy 1: Find any text block mentioning the subject or object
          const subjectLower = highlightRelation.subject.toLowerCase();
          const objectLower = highlightRelation.object.toLowerCase();
          
          const mentioningBlocks = parsedDoc.texts.filter(t => {
            const textLower = t.text.toLowerCase();
            return textLower.includes(subjectLower) || textLower.includes(objectLower);
          });
          
          if (mentioningBlocks.length > 0) {
            approximateBlock = mentioningBlocks[0]; // Take first match
            const mentionedEntity = mentioningBlocks[0].text.toLowerCase().includes(subjectLower) 
              ? highlightRelation.subject 
              : highlightRelation.object;
            fallbackMessage = `Could not find exact relation in this paper. Scrolled to text mentioning "${mentionedEntity}". The relation may exist in the graph but not be extracted from this specific paper, or entity names might differ.`;
            console.log('[AnnotatedView] Found text block mentioning entity:', mentionedEntity);
          }
          
          // Strategy 2: If no text mentions found and we have pages, scroll to that page
          if (!approximateBlock && highlightRelation.pages && highlightRelation.pages.length > 0) {
            const targetPage = highlightRelation.pages[0];
            // Find first text block on that page
            const pageBlocks = parsedDoc.texts.filter(t => {
              const prov = t.prov.find(p => p.page_no === targetPage);
              return !!prov;
            });
            
            if (pageBlocks.length > 0) {
              approximateBlock = pageBlocks[0];
              fallbackMessage = `Could not find exact relation in this paper. Scrolled to page ${targetPage} where the relation is expected. Please search manually for the mentioned entities.`;
              console.log('[AnnotatedView] Found text block on target page:', targetPage);
            }
          }
          
          if (approximateBlock) {
            setIsApproximateMatch(true);
            setSelectedBlock(approximateBlock);
            setIsLocating(true);
            
            // Show approximate match info in sidebar
            if (onRelationsUpdate) {
              onRelationsUpdate([], {
                type: 'text',
                preview: `⚠️ Approximate Location\n\n${fallbackMessage}\n\n📍 Preview: ${approximateBlock.text.substring(0, 200)}${approximateBlock.text.length > 200 ? '...' : ''}`
              });
            }
            
            // Scroll to approximate location
            const scrollToElement = (retries = 0, maxRetries = 3) => {
              setTimeout(() => {
                const element = document.querySelector(`[data-docling-ref="${approximateBlock.self_ref}"]`);
                if (element) {
                  console.log('[AnnotatedView] Scrolling to approximate location:', approximateBlock.self_ref);
                  element.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'center' 
                  });
                  setIsLocating(false);
                } else if (retries < maxRetries) {
                  scrollToElement(retries + 1, maxRetries);
                } else {
                  console.warn('[AnnotatedView] Could not find DOM element for approximate match');
                  setIsLocating(false);
                }
              }, retries === 0 ? 100 : 300);
            };
            
            scrollToElement();
          } else {
            console.warn('[AnnotatedView] No approximate match found either');
            
            // Show error in sidebar
            if (onRelationsUpdate) {
              onRelationsUpdate([], {
                type: 'text',
                preview: `❌ Relation Not Found\n\nCould not locate:\n"${highlightRelation.subject}" → "${highlightRelation.predicate}" → "${highlightRelation.object}"\n\nThis relation exists in the knowledge graph but may not be present in this specific paper, or the entity names may differ between the graph and paper text.`
              });
            }
          }
        }
      } catch (err) {
        console.error('[AnnotatedView] Failed to search for relation:', err);
      } finally {
        if (onLoadingChange) {
          onLoadingChange(false);
        }
      }
    };

    searchForRelation();
  }, [highlightRelation, parsedDoc]); // Removed onRelationsUpdate and onLoadingChange from deps

  // Handle sentence selection (multi-select)
  const handleSentenceClick = async (sentence: string, _textBlock: DoclingText) => {
    const trimmed = sentence.trim();
    
    setSelectedSentences(prev => {
      const newSet = new Set(prev);
      if (newSet.has(trimmed)) {
        // Deselect if already selected
        newSet.delete(trimmed);
      } else {
        // Add to selection
        newSet.add(trimmed);
      }
      
      // Trigger search with updated selection
      const allSelectedText = Array.from(newSet).join(' ');
      if (newSet.size > 0) {
        searchRelationsForText(allSelectedText, newSet.size);
      } else {
        // Clear relations if no sentences selected
        if (onRelationsUpdate) {
          onRelationsUpdate([], null);
        }
      }
      
      return newSet;
    });
  };
  
  // Search for relations based on selected text
  const searchRelationsForText = async (text: string, sentenceCount: number) => {
    if (onLoadingChange) {
      onLoadingChange(true);
    }
    
    try {
      const relations = await getRelationsByText(text);
      console.log('[AnnotatedView] Found relations for selected text:', relations.length);
      
      if (onRelationsUpdate) {
        const preview = sentenceCount === 1 
          ? (text.length > 100 ? text.substring(0, 100) + '...' : text)
          : `${sentenceCount} sentences selected`;
        
        onRelationsUpdate(relations, {
          type: 'text',
          preview: preview
        });
      }
    } catch (err) {
      console.error('[AnnotatedView] Failed to fetch relations:', err);
      if (onRelationsUpdate) {
        onRelationsUpdate([], null);
      }
    } finally {
      if (onLoadingChange) {
        onLoadingChange(false);
      }
    }
  };

  const handleTextClick = async (text: DoclingText) => {
    console.log("Text clicked:", text);
    
    // Toggle selection - if already selected, deselect it
    if (selectedBlock?.self_ref === text.self_ref) {
      setSelectedBlock(null);
      setSelectedSentences(new Set()); // Clear any sentence selections too
      if (onRelationsUpdate) {
        onRelationsUpdate([], null);
      }
      return;
    }
    
    setSelectedBlock(text);
    setSelectedSentences(new Set()); // Clear sentence selections when clicking text block
    
    if (onLoadingChange) {
      onLoadingChange(true);
    }
    
    try {
      // Use the full filename as paper ID (backend expects the full filename with .pdf)
      const paperId = paperFilename;
      
      let relations: Relation[] = [];
      
      // Strategy: Get all relations on the page
      // Relations are typically extracted at sentence/passage level, not entire text blocks
      // So we want to show all relations from this page when a text block is clicked
      if (text.prov.length > 0) {
        try {
          const pageNum = text.prov[0].page_no;
          
          // Get all relations on this page
          relations = await getRelationsByLocation(paperId, pageNum);
          console.log('[AnnotatedView] Relations on page', pageNum, ':', relations.length);
        } catch (err) {
          console.error('[AnnotatedView] Location search failed:', err);
        }
      }
      
      // Update parent component
      if (onRelationsUpdate) {
        const preview = text.text.length > 100 
          ? text.text.substring(0, 100) + '...' 
          : text.text;
        onRelationsUpdate(relations, {
          type: 'text',
          preview: preview
        });
      }
    } catch (err) {
      console.error('[AnnotatedView] Failed to fetch relations for text:', err);
      if (onRelationsUpdate) {
        onRelationsUpdate([], null);
      }
    } finally {
      if (onLoadingChange) {
        onLoadingChange(false);
      }
    }
  };

  const handleFigureClick = async (picture: DoclingPicture, imageUrl: string | null) => {
    console.log("Figure clicked:", picture);
    
    // Toggle selection - if already selected, deselect it
    if (selectedBlock?.self_ref === picture.self_ref) {
      setSelectedBlock(null);
      setSelectedSentences(new Set()); // Clear any sentence selections too
      if (onRelationsUpdate) {
        onRelationsUpdate([], null);
      }
      return;
    }
    
    setSelectedBlock(picture);
    setSelectedSentences(new Set()); // Clear sentence selections when clicking figure
    
    if (onLoadingChange) {
      onLoadingChange(true);
    }
    
    try {
      // Use the full filename as paper ID (backend expects the full filename with .pdf)
      const paperId = paperFilename;
      
      // Construct figure ID from provenance
      // Format: page{N}_fig{M}
      // We'll need to determine the figure index on the page
      // For now, use a simplified approach
      if (picture.prov.length > 0) {
        const pageNum = picture.prov[0].page_no;
        // Extract index from self_ref like "#/pictures/5"
        const match = picture.self_ref.match(/\/pictures\/(\d+)$/);
        const figureIndex = match ? parseInt(match[1]) : 0;
        
        const figureId = `page${pageNum}_fig${figureIndex}`;
        
        try {
          let relations = await getRelationsByFigure(paperId, figureId);
          console.log('[AnnotatedView] Found relations for figure ID:', relations.length);
          
          // FALLBACK: If no figure-specific relations found, get all relations from the page
          if (relations.length === 0) {
            console.log('[AnnotatedView] No figure-specific relations, falling back to page:', pageNum);
            relations = await getRelationsByLocation(paperId, pageNum);
            console.log('[AnnotatedView] Found relations on page:', relations.length);
          }
          
          if (onRelationsUpdate) {
            onRelationsUpdate(relations, {
              type: 'figure',
              preview: `Figure from page ${pageNum}${relations.length > 0 ? ` (${relations.length} relations)` : ''}`,
              imageData: imageUrl || undefined // Pass the base64 image data URL
            });
          }
        } catch (err) {
          console.error('[AnnotatedView] Figure search failed:', err);
          if (onRelationsUpdate) {
            onRelationsUpdate([], {
              type: 'figure',
              preview: `Figure from page ${pageNum}`,
              imageData: imageUrl || undefined
            });
          }
        }
      }
    } catch (err) {
      console.error('[AnnotatedView] Failed to fetch relations for figure:', err);
      if (onRelationsUpdate) {
        onRelationsUpdate([], null);
      }
    } finally {
      if (onLoadingChange) {
        onLoadingChange(false);
      }
    }
  };

  const handleTableClick = async (table: DoclingTable) => {
    console.log("Table clicked:", table);
    
    // Toggle selection - if already selected, deselect it
    if (selectedBlock?.self_ref === table.self_ref) {
      setSelectedBlock(null);
      setSelectedSentences(new Set()); // Clear any sentence selections too
      if (onRelationsUpdate) {
        onRelationsUpdate([], null);
      }
      return;
    }
    
    setSelectedBlock(table);
    setSelectedSentences(new Set()); // Clear sentence selections when clicking table
    
    if (onLoadingChange) {
      onLoadingChange(true);
    }
    
    try {
      // Use the full filename as paper ID (backend expects the full filename with .pdf)
      const paperId = paperFilename;
      
      // Construct table ID from provenance and self_ref
      // Format: page{N}_table{M} where M is 0-based index from Docling
      // Example: self_ref="#/tables/0" on page 3 → "page3_table0"
      if (table.prov.length > 0) {
        const pageNum = table.prov[0].page_no;
        // Extract 0-based index from self_ref like "#/tables/2"
        const match = table.self_ref.match(/\/tables\/(\d+)$/);
        const tableIndex = match ? parseInt(match[1]) : 0;
        
        const tableId = `page${pageNum}_table${tableIndex}`;
        console.log('[AnnotatedView] Table click:', { paperId, self_ref: table.self_ref, pageNum, tableIndex, tableId });
        
        try {
          let relations = await getRelationsByTable(paperId, tableId);
          console.log('[AnnotatedView] Found relations for table ID:', relations.length);
          
          // FALLBACK: If no table-specific relations found, get all relations from the page
          if (relations.length === 0) {
            console.log('[AnnotatedView] No table-specific relations, falling back to page:', pageNum);
            relations = await getRelationsByLocation(paperId, pageNum);
            console.log('[AnnotatedView] Found relations on page:', relations.length);
          }
          
          if (onRelationsUpdate) {
            onRelationsUpdate(relations, {
              type: 'table',
              preview: `Table from page ${pageNum}${relations.length > 0 ? ` (${relations.length} relations)` : ''}`,
              tableData: table // Pass the entire Docling table object
            });
          }
        } catch (err) {
          console.error('[AnnotatedView] Table search failed:', err);
          if (onRelationsUpdate) {
            onRelationsUpdate([], {
              type: 'table',
              preview: `Table from page ${pageNum}`,
              tableData: table
            });
          }
        }
      }
    } catch (err) {
      console.error('[AnnotatedView] Failed to fetch relations for table:', err);
      if (onRelationsUpdate) {
        onRelationsUpdate([], null);
      }
    } finally {
      if (onLoadingChange) {
        onLoadingChange(false);
      }
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading document...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center max-w-md">
          <svg
            className="w-16 h-16 text-red-500 mx-auto mb-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Failed to Load Document
          </h3>
          <p className="text-gray-600 text-sm mb-4">{error}</p>
          <p className="text-xs text-gray-500">
            Make sure the docling JSON file exists at: /docling_json/{paperFilename.replace(/\.pdf$/i, ".json")}
          </p>
        </div>
      </div>
    );
  }

  if (!parsedDoc || parsedDoc.items.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <p className="text-gray-600">No content found in document</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto bg-gray-50 relative">
      {/* Enhanced loading overlay during auto-scroll */}
      {isLocating && (
        <>
          {/* Semi-transparent overlay to dim document and prevent interaction */}
          <div className="fixed inset-0 bg-black bg-opacity-30 z-40 animate-fade-in" />
          
          {/* Large prominent loading indicator */}
          <div className="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-50 animate-fade-in">
            <div className="bg-white rounded-2xl shadow-2xl p-8 flex flex-col items-center gap-4 min-w-[320px]">
              {/* Large spinner */}
              <div className="relative">
                <div className="animate-spin rounded-full h-16 w-16 border-4 border-blue-200"></div>
                <div className="animate-spin rounded-full h-16 w-16 border-4 border-blue-600 border-t-transparent absolute top-0 left-0"></div>
              </div>
              
              {/* Text */}
              <div className="text-center">
                <h3 className="text-xl font-semibold text-gray-900 mb-1">
                  Locating Relation
                </h3>
                <p className="text-sm text-gray-600 mb-2">
                  Finding and highlighting the text in the document...
                </p>
                <p className="text-xs font-medium text-blue-600 bg-blue-50 px-3 py-1 rounded-full inline-block">
                  ⏳ Please wait, don't scroll yet
                </p>
              </div>
              
              {/* Animated dots */}
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
              </div>
            </div>
          </div>
        </>
      )}
      
      <div className="max-w-3xl mx-auto bg-white shadow-sm">
        <DoclingRenderer
          items={parsedDoc.items}
          onTextClick={handleTextClick}
          onSentenceClick={handleSentenceClick}
          onFigureClick={handleFigureClick}
          onTableClick={handleTableClick}
          selectedBlock={selectedBlock}
          selectedSentences={selectedSentences}
          pdfUrl={pdfUrl}
          isApproximateMatch={isApproximateMatch}
        />
      </div>
    </div>
  );
}
