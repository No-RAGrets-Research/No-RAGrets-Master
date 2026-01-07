/**
 * RubricReviewModal - Modal component for displaying rubric review results
 */

import { useEffect } from 'react';
import type { ReviewResponse } from '@/types/review';
import type { SelectedContent } from '../annotated-view/AnnotatedView';

interface RubricReviewModalProps {
  isOpen: boolean;
  selectedContent: SelectedContent | null;
  review: ReviewResponse | null;
  loading: boolean;
  error: string | null;
  onClose: () => void;
  onRetry: () => void;
}

export function RubricReviewModal({
  isOpen,
  selectedContent,
  review,
  loading,
  error,
  onClose,
  onRetry
}: RubricReviewModalProps) {
  // Close modal on Escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  // Get rubric label from rubric_name (e.g., "rubric1_methodology" -> "Methodology")
  const getRubricLabel = (rubricName?: string): string => {
    if (!rubricName) return 'Rubric';
    const match = rubricName.match(/rubric\d+_(.+)/);
    if (match) {
      return match[1].charAt(0).toUpperCase() + match[1].slice(1);
    }
    return rubricName;
  };

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/50 dark:bg-black/70"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="relative w-full max-w-3xl max-h-[90vh] bg-white dark:bg-gray-800 rounded-lg shadow-2xl flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              {review?.rubric_name ? `${getRubricLabel(review.rubric_name)} Review` : 'Rubric Review'}
            </h2>
            {review?.metadata && (
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                {review.metadata.provider} - {review.metadata.model}
              </p>
            )}
          </div>
          <button
            onClick={onClose}
            className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            aria-label="Close"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Selected Content Context */}
          {selectedContent && (
            <div className="mb-6 p-4 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
              <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                Selected Content:
              </h3>
              
              {/* Show different preview based on content type */}
              {selectedContent.type === 'text' && (
                <p className="text-sm text-gray-600 dark:text-gray-400 italic">
                  "{selectedContent.preview.length > 300 ? selectedContent.preview.substring(0, 300) + '...' : selectedContent.preview}"
                </p>
              )}
              
              {selectedContent.type === 'figure' && selectedContent.imageData && (
                <div className="flex flex-col items-center">
                  <img 
                    src={selectedContent.imageData} 
                    alt="Selected figure"
                    className="max-w-full max-h-64 w-auto h-auto object-contain rounded border border-gray-300 dark:border-gray-600"
                  />
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">{selectedContent.preview}</p>
                </div>
              )}
              
              {selectedContent.type === 'table' && (
                <div>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">{selectedContent.preview}</p>
                  {selectedContent.tableData?.data && (
                    <div className="text-xs text-gray-600 dark:text-gray-400 bg-white dark:bg-gray-800 p-3 rounded border border-gray-200 dark:border-gray-700 overflow-x-auto">
                      <div className="font-mono">
                        <p><strong>Rows:</strong> {selectedContent.tableData.data.num_rows}</p>
                        <p><strong>Columns:</strong> {selectedContent.tableData.data.num_cols}</p>
                        <p className="mt-2 text-gray-500">Table structure passed to API for analysis</p>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Loading State */}
          {loading && (
            <div className="flex flex-col items-center justify-center py-12">
              <div className="w-16 h-16 border-4 border-purple-200 dark:border-purple-900 border-t-purple-600 dark:border-t-purple-400 rounded-full animate-spin mb-4" />
              <p className="text-gray-600 dark:text-gray-400 text-center">
                Analyzing with rubric...
                <br />
                <span className="text-sm text-gray-500 dark:text-gray-500">
                  This may take ~30 seconds
                </span>
              </p>
            </div>
          )}

          {/* Error State */}
          {error && !loading && (
            <div className="flex flex-col items-center justify-center py-12">
              <div className="w-16 h-16 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center mb-4">
                <svg className="w-8 h-8 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <p className="text-red-600 dark:text-red-400 font-semibold mb-2">
                Review Failed
              </p>
              <p className="text-gray-600 dark:text-gray-400 text-center mb-6 max-w-md">
                {error}
              </p>
              <div className="flex gap-3">
                <button
                  onClick={onRetry}
                  className="px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-colors"
                >
                  Retry
                </button>
                <button
                  onClick={onClose}
                  className="px-6 py-2 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-900 dark:text-white rounded-lg font-medium transition-colors"
                >
                  Close
                </button>
              </div>
            </div>
          )}

          {/* Review Content */}
          {review && !loading && !error && (
            <div>
              {(review.review || review.response) ? (
                <div className="whitespace-pre-wrap text-gray-800 dark:text-gray-200 leading-relaxed">
                  {review.review || review.response}
                </div>
              ) : (
                <div className="text-center py-8">
                  <p className="text-red-600 dark:text-red-400 mb-4">No review text in response</p>
                  <details className="text-left">
                    <summary className="cursor-pointer text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300">
                      Show raw response (for debugging)
                    </summary>
                    <pre className="mt-2 p-4 bg-gray-100 dark:bg-gray-900 rounded text-xs overflow-auto">
                      {JSON.stringify(review, null, 2)}
                    </pre>
                  </details>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        {review && !loading && !error && (
          <div className="p-6 border-t border-gray-200 dark:border-gray-700 flex justify-end">
            <button
              onClick={onClose}
              className="px-6 py-2 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-900 dark:text-white rounded-lg font-medium transition-colors"
            >
              Close
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
