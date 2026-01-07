import { useState } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import type { BoundingBox } from '../../types';
import { BoundingBoxOverlay } from './BoundingBoxOverlay';

// Configure PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

interface PDFViewerProps {
  filename: string;
  bboxes?: Array<{ page: number; bbox: BoundingBox }>;
  onTextSelect?: (selection: { text: string; pageNumber: number }) => void;
  onPageChange?: (pageNumber: number) => void;
}

export const PDFViewer = ({ filename, bboxes = [], onTextSelect, onPageChange }: PDFViewerProps) => {
  const [numPages, setNumPages] = useState<number>(0);
  const [pageNumber, setPageNumber] = useState<number>(1);
  const [scale, setScale] = useState<number>(1.2);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [pageSize, setPageSize] = useState<{ width: number; height: number }>({ width: 0, height: 0 });

  // Construct the PDF path - files are in /papers directory relative to public folder
  // Strip "Copy of " prefix and 8-digit timestamp suffix from the filename
  // Handles patterns like: "...202320251115.pdf" -> "...2023.pdf" or "...20251113.pdf" -> "....pdf"
  const cleanFilename = filename
    .replace(/^Copy of /, '')  // Remove "Copy of " prefix
    .replace(/(\d{8})(\.pdf)$/, '$2');  // Remove last 8 digits (timestamp) before .pdf
  const pdfPath = `/papers/${cleanFilename}`;

  const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages);
    setLoading(false);
    setError(null);
  };

  const onDocumentLoadError = (error: Error) => {
    console.error('Error loading PDF:', error);
    setError('Failed to load PDF. Please check if the file exists.');
    setLoading(false);
  };

  const goToPrevPage = () => {
    const newPage = Math.max(pageNumber - 1, 1);
    setPageNumber(newPage);
    onPageChange?.(newPage);
  };

  const goToNextPage = () => {
    const newPage = Math.min(pageNumber + 1, numPages);
    setPageNumber(newPage);
    onPageChange?.(newPage);
  };

  const zoomIn = () => {
    setScale((prev) => Math.min(prev + 0.2, 3));
  };

  const zoomOut = () => {
    setScale((prev) => Math.max(prev - 0.2, 0.5));
  };

  const resetZoom = () => {
    setScale(1.2);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-3 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-4">
          {/* Page navigation */}
          <div className="flex items-center gap-2">
            <button
              onClick={goToPrevPage}
              disabled={pageNumber <= 1}
              className="px-3 py-1 text-sm font-medium text-gray-700 dark:text-gray-200 bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <span className="text-sm text-gray-600 dark:text-gray-300">
              Page {pageNumber} of {numPages || '...'}
            </span>
            <button
              onClick={goToNextPage}
              disabled={pageNumber >= numPages}
              className="px-3 py-1 text-sm font-medium text-gray-700 dark:text-gray-200 bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>

          {/* Zoom controls */}
          <div className="flex items-center gap-2 border-l border-gray-300 dark:border-gray-600 pl-4">
            <button
              onClick={zoomOut}
              className="px-3 py-1 text-sm font-medium text-gray-700 dark:text-gray-200 bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600"
            >
              −
            </button>
            <button
              onClick={resetZoom}
              className="px-3 py-1 text-sm font-medium text-gray-700 dark:text-gray-200 bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600"
            >
              {Math.round(scale * 100)}%
            </button>
            <button
              onClick={zoomIn}
              className="px-3 py-1 text-sm font-medium text-gray-700 dark:text-gray-200 bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600"
            >
              +
            </button>
          </div>
        </div>

        <div className="text-sm text-gray-600 dark:text-gray-300">
          {filename}
        </div>
      </div>

      {/* PDF Display */}
      <div className="flex-1 overflow-auto bg-gray-100 dark:bg-gray-900 p-4">
        <div className="flex justify-center items-start min-h-full">
          {loading && (
            <div className="text-gray-600 dark:text-gray-400">Loading PDF...</div>
          )}
          {error && (
            <div className="text-red-600 dark:text-red-400">
              {error}
              <div className="text-sm mt-2">Path: {pdfPath}</div>
            </div>
          )}
          <div className="relative">
            <Document
              file={pdfPath}
              onLoadSuccess={onDocumentLoadSuccess}
              onLoadError={onDocumentLoadError}
              loading={<div className="text-gray-600 dark:text-gray-400">Loading document...</div>}
            >
              <div style={{ position: 'relative' }}>
                <Page
                  pageNumber={pageNumber}
                  scale={scale}
                  renderTextLayer={false}
                  renderAnnotationLayer={false}
                  className="shadow-lg"
                  onLoadSuccess={(page) => {
                    setPageSize({
                      width: page.width,
                      height: page.height,
                    });
                  }}
                />
                {/* Bounding Box Overlay */}
                {pageSize.width > 0 && bboxes.length > 0 && (
                  <BoundingBoxOverlay
                    bboxes={bboxes}
                    currentPage={pageNumber}
                    scale={scale}
                    pageWidth={pageSize.width}
                    pageHeight={pageSize.height}
                  />
                )}
              </div>
            </Document>
          </div>
        </div>
      </div>
    </div>
  );
};
