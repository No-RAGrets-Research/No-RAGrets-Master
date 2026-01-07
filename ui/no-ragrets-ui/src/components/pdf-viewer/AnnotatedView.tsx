import { useState, useEffect } from 'react';
import type { Relation, RelationSourceSpan } from '../../types';
import { getRelationSourceSpan } from '../../services/api';

interface AnnotatedViewProps {
  pdfUrl: string;
  relations: Relation[];
  onRelationClick?: (relation: Relation) => void;
  selectedRelation?: Relation | null;
}

interface TextSegment {
  text: string;
  relation?: Relation;
  isSubject?: boolean;
  isObject?: boolean;
}

interface AnnotatedSentence {
  fullText: string;
  segments: TextSegment[];
  relation: Relation;
}

interface Section {
  title: string;
  sentences: AnnotatedSentence[];
}

export const AnnotatedView = ({ pdfUrl, relations, onRelationClick, selectedRelation }: AnnotatedViewProps) => {
  const [sections, setSections] = useState<Section[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadSourceSpans = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        // Fetch source spans in batches to avoid overwhelming the browser
        const BATCH_SIZE = 10;
        const validResults: Array<{ relation: Relation; sourceSpan: RelationSourceSpan }> = [];
        
        for (let i = 0; i < relations.length; i += BATCH_SIZE) {
          const batch = relations.slice(i, i + BATCH_SIZE);
          const batchPromises = batch.map(relation => 
            getRelationSourceSpan(relation.id)
              .then(sourceSpan => ({ relation, sourceSpan }))
              .catch(err => {
                console.error(`Failed to fetch source span for ${relation.id}:`, err);
                return null;
              })
          );
          
          const batchResults = await Promise.all(batchPromises);
          const validBatchResults = batchResults.filter((r): r is { relation: Relation; sourceSpan: RelationSourceSpan } => r !== null);
          validResults.push(...validBatchResults);
          
          // Small delay between batches to prevent overwhelming the API
          if (i + BATCH_SIZE < relations.length) {
            await new Promise(resolve => setTimeout(resolve, 100));
          }
        }
        
        // Group by section
        const relationsBySection = validResults.reduce((acc, { relation, sourceSpan }) => {
          const section = relation.section || 'Document Content';
          if (!acc[section]) {
            acc[section] = [];
          }
          acc[section].push({ relation, sourceSpan });
          return acc;
        }, {} as Record<string, Array<{ relation: Relation; sourceSpan: RelationSourceSpan }>>);
        
        // Create sections with annotated sentences
        const processedSections: Section[] = Object.entries(relationsBySection).map(([sectionTitle, items]) => {
          const sentences: AnnotatedSentence[] = items.map(({ relation, sourceSpan }) => {
            const text = sourceSpan.source_span.text_evidence;
            const subjectPositions = sourceSpan.subject_positions || [];
            const objectPositions = sourceSpan.object_positions || [];
            
            // Create segments by splitting text at entity positions
            const positions = [
              ...subjectPositions.map(p => ({ ...p, type: 'subject' as const })),
              ...objectPositions.map(p => ({ ...p, type: 'object' as const })),
            ].sort((a, b) => a.start - b.start);
            
            const segments: TextSegment[] = [];
            let lastEnd = 0;
            
            positions.forEach(pos => {
              // Add text before this entity
              if (pos.start > lastEnd) {
                segments.push({
                  text: text.slice(lastEnd, pos.start),
                });
              }
              
              // Add the entity
              segments.push({
                text: text.slice(pos.start, pos.end),
                relation,
                isSubject: pos.type === 'subject',
                isObject: pos.type === 'object',
              });
              
              lastEnd = pos.end;
            });
            
            // Add remaining text
            if (lastEnd < text.length) {
              segments.push({
                text: text.slice(lastEnd),
              });
            }
            
            return {
              fullText: text,
              segments: segments.length > 0 ? segments : [{ text }],
              relation,
            };
          });
          
          return {
            title: sectionTitle,
            sentences,
          };
        });
        
        setSections(processedSections);
      } catch (err) {
        console.error('Error loading source spans:', err);
        setError('Failed to load relation context');
      } finally {
        setIsLoading(false);
      }
    };
    
    loadSourceSpans();
  }, [relations]);

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center bg-white dark:bg-gray-900">
        <p className="text-gray-600 dark:text-gray-400">Extracting document text...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full flex items-center justify-center bg-white dark:bg-gray-900">
        <p className="text-red-600 dark:text-red-400">{error}</p>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto bg-white dark:bg-gray-900 p-8">
      <div className="max-w-4xl mx-auto prose dark:prose-invert">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            Annotated Document View
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Document text with inline relation annotations
          </p>
        </div>

        {sections.map((section, sectionIdx) => (
          <div key={sectionIdx} className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4 border-b border-gray-300 dark:border-gray-700 pb-2">
              {section.title}
            </h2>
            
            <div className="space-y-4">
              {section.sentences.map((sentence, sentIdx) => (
                <p key={sentIdx} className="text-base leading-relaxed text-gray-800 dark:text-gray-200">
                  {sentence.segments.map((segment, segIdx) => {
                    const isSelected = selectedRelation?.id === segment.relation?.id;
                    
                    if (!segment.relation) {
                      // Plain text (not part of a relation)
                      return <span key={segIdx}>{segment.text}</span>;
                    }
                    
                    const baseClasses = "cursor-pointer transition-colors rounded px-0.5";
                    let colorClasses = "";
                    
                    if (segment.isSubject) {
                      colorClasses = isSelected 
                        ? "bg-blue-200 dark:bg-blue-800 text-blue-900 dark:text-blue-100 font-semibold" 
                        : "text-blue-600 dark:text-blue-400 hover:bg-blue-100 dark:hover:bg-blue-900/30 font-medium";
                    } else if (segment.isObject) {
                      colorClasses = isSelected
                        ? "bg-green-200 dark:bg-green-800 text-green-900 dark:text-green-100 font-semibold"
                        : "text-green-600 dark:text-green-400 hover:bg-green-100 dark:hover:bg-green-900/30 font-medium";
                    }
                    
                    return (
                      <span
                        key={segIdx}
                        className={`${baseClasses} ${colorClasses}`}
                        onClick={() => onRelationClick?.(segment.relation!)}
                      >
                        {segment.text}
                      </span>
                    );
                  })}
                </p>
              ))}
            </div>
          </div>
        ))}

        {sections.length === 0 && (
          <p className="text-center text-gray-500 dark:text-gray-400 py-8">
            No relations found in this paper
          </p>
        )}
      </div>
    </div>
  );
};
