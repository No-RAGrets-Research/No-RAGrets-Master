/**
 * DoclingRenderer - Renders document content from Docling JSON
 */

import { useEffect, useRef, useState } from "react";
import type { DoclingItem, DoclingText, DoclingPicture, DoclingTable } from "@/utils/docling";
import { extractFigureFromPDF } from "@/utils/pdfFigureExtractor";

function cn(...classes: (string | boolean | undefined)[]) {
  return classes.filter(Boolean).join(" ");
}

interface DoclingRendererProps {
  items: DoclingItem[];
  onTextClick?: (text: DoclingText) => void;
  onSentenceClick?: (sentence: string, textBlock: DoclingText) => void;
  onFigureClick?: (picture: DoclingPicture, imageUrl: string | null) => void;
  onTableClick?: (table: DoclingTable) => void;
  selectedBlock?: DoclingText | DoclingPicture | DoclingTable | null;
  selectedSentences?: Set<string>;
  pdfUrl?: string;
  isApproximateMatch?: boolean; // If true, use different styling for approximate matches
}

export function DoclingRenderer({
  items,
  onTextClick,
  onSentenceClick,
  onFigureClick,
  onTableClick,
  selectedBlock,
  selectedSentences,
  pdfUrl,
  isApproximateMatch = false,
}: DoclingRendererProps) {
  return (
    <div className="prose prose-lg max-w-none px-12 py-16">
      {items.map((item, index) => {
        switch (item.type) {
          case "text":
            return (
              <TextBlock
                key={`text-${index}`}
                text={item.data}
                onClick={onTextClick}
                onSentenceClick={onSentenceClick}
                isSelected={selectedBlock === item.data}
                selectedSentences={selectedSentences}
                isApproximateMatch={isApproximateMatch}
              />
            );
          case "picture":
            return (
              <FigurePlaceholder
                key={`picture-${index}`}
                picture={item.data}
                onClick={onFigureClick}
                isSelected={selectedBlock === item.data}
                pdfUrl={pdfUrl}
                isApproximateMatch={isApproximateMatch}
              />
            );
          case "table":
            return (
              <TablePlaceholder
                key={`table-${index}`}
                table={item.data}
                onClick={onTableClick}
                isSelected={selectedBlock === item.data}
                isApproximateMatch={isApproximateMatch}
              />
            );
          default:
            return null;
        }
      })}
    </div>
  );
}

interface TextBlockProps {
  text: DoclingText;
  onClick?: (text: DoclingText) => void;
  onSentenceClick?: (sentence: string, textBlock: DoclingText) => void;
  isSelected: boolean;
  selectedSentences?: Set<string>;
  isApproximateMatch?: boolean;
}

function TextBlock({ text, onSentenceClick, isSelected, selectedSentences, isApproximateMatch = false }: TextBlockProps) {
  // Split text into sentences (simple split on . ! ? followed by space or end)
  const sentences = text.text.match(/[^.!?]+[.!?]+(?:\s|$)|[^.!?]+$/g) || [text.text];
  
  const handleSentenceClick = (e: React.MouseEvent, sentence: string) => {
    e.stopPropagation();
    if (onSentenceClick) {
      onSentenceClick(sentence.trim(), text);
    }
  };

  // Get page number from provenance
  const pageNumber = text.prov.length > 0 ? text.prov[0].page_no : null;
  
  // Choose highlight color based on match type
  const highlightClasses = isApproximateMatch
    ? "bg-yellow-50 border-l-4 border-yellow-500"
    : "bg-blue-100 border-l-4 border-blue-500";

  // Render based on label type
  if (text.label === "section_header") {
    return (
      <h2
        data-docling-ref={text.self_ref}
        className={cn(
          "transition-colors rounded px-2 py-1 relative group",
          "text-2xl font-bold mt-8 mb-4 text-gray-900",
          isSelected && highlightClasses
        )}
      >
        {onSentenceClick ? (
          sentences.map((sentence, idx) => {
            const trimmed = sentence.trim();
            const isSentenceSelected = selectedSentences?.has(trimmed);
            return (
              <span
                key={idx}
                onClick={(e) => handleSentenceClick(e, sentence)}
                className={cn(
                  "cursor-pointer transition-colors rounded px-1",
                  isSentenceSelected
                    ? "bg-yellow-200 border-b-2 border-yellow-500"
                    : "hover:bg-yellow-50"
                )}
              >
                {sentence}
              </span>
            );
          })
        ) : (
          text.text
        )}
        {pageNumber && (
          <span className="absolute right-2 top-1 text-xs text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity">
            p.{pageNumber}
          </span>
        )}
      </h2>
    );
  }

  if (text.label === "caption") {
    return (
      <figcaption
        data-docling-ref={text.self_ref}
        className={cn(
          "transition-colors rounded px-2 py-1 relative group",
          "text-sm italic text-gray-600 mt-2 mb-4",
          isSelected && highlightClasses
        )}
      >
        {onSentenceClick ? (
          sentences.map((sentence, idx) => {
            const trimmed = sentence.trim();
            const isSentenceSelected = selectedSentences?.has(trimmed);
            return (
              <span
                key={idx}
                onClick={(e) => handleSentenceClick(e, sentence)}
                className={cn(
                  "cursor-pointer transition-colors rounded px-1",
                  isSentenceSelected
                    ? "bg-yellow-200 border-b-2 border-yellow-500"
                    : "hover:bg-yellow-50"
                )}
              >
                {sentence}
              </span>
            );
          })
        ) : (
          text.text
        )}
        {pageNumber && (
          <span className="absolute right-2 top-1 text-xs text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity">
            p.{pageNumber}
          </span>
        )}
      </figcaption>
    );
  }

  if (text.label === "page_header" || text.label === "page_footer") {
    return (
      <div
        data-docling-ref={text.self_ref}
        className={cn(
          "transition-colors rounded px-2 py-1 relative group",
          "text-xs text-gray-400",
          text.label === "page_header" ? "mt-6 mb-2" : "mt-2 mb-6",
          isSelected && highlightClasses
        )}
      >
        {onSentenceClick ? (
          sentences.map((sentence, idx) => {
            const trimmed = sentence.trim();
            const isSentenceSelected = selectedSentences?.has(trimmed);
            return (
              <span
                key={idx}
                onClick={(e) => handleSentenceClick(e, sentence)}
                className={cn(
                  "cursor-pointer transition-colors rounded px-1",
                  isSentenceSelected
                    ? "bg-yellow-200 border-b-2 border-yellow-500"
                    : "hover:bg-yellow-50"
                )}
              >
                {sentence}
              </span>
            );
          })
        ) : (
          text.text
        )}
        {pageNumber && (
          <span className="absolute right-2 top-1 text-xs text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity">
            p.{pageNumber}
          </span>
        )}
      </div>
    );
  }

  // Default: regular text paragraph
  return (
    <p
      data-docling-ref={text.self_ref}
      className={cn(
        "transition-colors rounded px-2 py-1 relative group",
        "text-base leading-relaxed mb-4 text-gray-800",
        isSelected && highlightClasses
      )}
    >
      {onSentenceClick ? (
        sentences.map((sentence, idx) => {
          const trimmed = sentence.trim();
          const isSentenceSelected = selectedSentences?.has(trimmed);
          return (
            <span
              key={idx}
              onClick={(e) => handleSentenceClick(e, sentence)}
              className={cn(
                "cursor-pointer transition-colors rounded px-1",
                isSentenceSelected
                  ? "bg-yellow-200 border-b-2 border-yellow-500"
                  : "hover:bg-yellow-50"
              )}
            >
              {sentence}
            </span>
          );
        })
      ) : (
        text.text
      )}
      {pageNumber && (
        <span className="absolute right-2 top-1 text-xs text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity">
          p.{pageNumber}
        </span>
      )}
    </p>
  );
}

interface FigurePlaceholderProps {
  picture: DoclingPicture;
  onClick?: (picture: DoclingPicture, imageUrl: string | null) => void;
  isSelected: boolean;
  pdfUrl?: string;
  isApproximateMatch?: boolean;
}

function FigurePlaceholder({
  picture,
  onClick,
  isSelected,
  pdfUrl,
  isApproximateMatch = false,
}: FigurePlaceholderProps) {
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const figureRef = useRef<HTMLDivElement>(null);

  const handleClick = () => {
    if (onClick) {
      onClick(picture, imageUrl);
    }
  };

  const pageNumber = picture.prov.length > 0 ? picture.prov[0].page_no : null;
  
  // Choose highlight color based on match type
  const highlightClasses = isApproximateMatch
    ? "bg-yellow-50 border-l-4 border-yellow-500"
    : "bg-blue-100 border-l-4 border-blue-500";

  console.log('[FigurePlaceholder] Rendering figure:', {
    self_ref: picture.self_ref,
    pageNumber,
    hasProv: picture.prov.length > 0,
    pdfUrl,
    bbox: picture.prov[0]?.bbox
  });

  useEffect(() => {
    if (!pdfUrl || picture.prov.length === 0) {
      console.log('[FigurePlaceholder] Skipping figure extraction:', { 
        hasPdfUrl: !!pdfUrl, 
        hasProvenance: picture.prov.length > 0,
        self_ref: picture.self_ref 
      });
      return;
    }

    const element = figureRef.current;
    if (!element) {
      console.log('[FigurePlaceholder] No element ref yet');
      return;
    }

    console.log('[FigurePlaceholder] Setting up intersection observer for:', picture.self_ref);

    // Lazy load figure when it comes into view
    const observer = new IntersectionObserver(
      ([entry]) => {
        console.log('[FigurePlaceholder] Intersection observer triggered:', {
          isIntersecting: entry.isIntersecting,
          hasImageUrl: !!imageUrl,
          loading,
          error,
          self_ref: picture.self_ref
        });
        
        if (entry.isIntersecting && !imageUrl && !loading && !error) {
          console.log('[FigurePlaceholder] Starting figure extraction for:', picture.self_ref);
          setLoading(true);
          extractFigureFromPDF(
            pdfUrl,
            picture.prov[0].page_no,
            picture.prov[0].bbox
          )
            .then((dataUrl) => {
              console.log('[FigurePlaceholder] Figure extracted successfully:', picture.self_ref);
              setImageUrl(dataUrl);
              setLoading(false);
            })
            .catch((err) => {
              console.error("[FigurePlaceholder] Failed to extract figure:", picture.self_ref, err);
              setError(true);
              setLoading(false);
            });
        }
      },
      { rootMargin: "200px" } // Start loading when figure is 200px from viewport
    );

    observer.observe(element);

    return () => {
      observer.unobserve(element);
    };
  }, [pdfUrl, picture, imageUrl, loading, error]);

  return (
    <div
      ref={figureRef}
      className={cn(
        "my-6 border-2 rounded-lg cursor-pointer transition-colors",
        isSelected
          ? isApproximateMatch 
            ? "border-yellow-500 bg-yellow-50"
            : "border-blue-500 bg-blue-50"
          : imageUrl
          ? "border-gray-300 hover:border-blue-400"
          : "border-dashed border-gray-300 hover:border-blue-400 hover:bg-blue-50"
      )}
      onClick={handleClick}
    >
      {imageUrl ? (
        <div className="p-4 flex flex-col items-center">
          <img
            src={imageUrl}
            alt={`Figure from page ${pageNumber}`}
            className="max-w-full max-h-96 w-auto h-auto object-contain"
          />
          {pageNumber && (
            <p className="text-xs text-gray-500 mt-2">Page {pageNumber}</p>
          )}
        </div>
      ) : loading ? (
        <div className="flex items-center justify-center py-8 p-4">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-400 mx-auto mb-2"></div>
            <p className="text-sm text-gray-500">Loading figure...</p>
          </div>
        </div>
      ) : error ? (
        <div className="flex items-center justify-center py-8 text-red-500 p-4">
          <div className="text-center">
            <svg
              className="w-12 h-12 mx-auto mb-2"
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
            <p className="text-sm">Failed to load figure</p>
          </div>
        </div>
      ) : (
        <div className="flex items-center justify-center py-8 text-gray-500 p-4">
          <div className="text-center">
            <svg
              className="w-12 h-12 mx-auto mb-2 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
            <p className="text-sm font-medium">Figure</p>
            {pageNumber && (
              <p className="text-xs text-gray-400 mt-1">Page {pageNumber}</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

interface TablePlaceholderProps {
  table: DoclingTable;
  onClick?: (table: DoclingTable) => void;
  isSelected?: boolean;
  isApproximateMatch?: boolean;
}

function TablePlaceholder({ table, onClick, isSelected, isApproximateMatch = false }: TablePlaceholderProps) {
  const pageNumber = table.prov.length > 0 ? table.prov[0].page_no : null;
  const grid = table.data?.grid || [];

  const handleClick = () => {
    if (onClick) {
      onClick(table);
    }
  };
  
  // Choose highlight color based on match type
  const borderHighlight = isApproximateMatch ? "border-yellow-500" : "border-blue-500";
  const bgHighlight = isApproximateMatch ? "bg-yellow-50" : "bg-blue-50";

  // If no grid data, show placeholder
  if (grid.length === 0) {
    return (
      <div className="my-6 p-4 border-2 border-dashed border-gray-300 rounded-lg">
        <div className="flex items-center justify-center py-6 text-gray-500">
          <div className="text-center">
            <svg
              className="w-12 h-12 mx-auto mb-2 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
              />
            </svg>
            <p className="text-sm font-medium">Table</p>
            {pageNumber && (
              <p className="text-xs text-gray-400 mt-1">Page {pageNumber}</p>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "my-6 overflow-x-auto rounded-lg border-2 transition-colors max-w-full",
        isSelected
          ? `${borderHighlight} ${bgHighlight}`
          : "border-gray-300 hover:border-blue-400",
        onClick && "cursor-pointer"
      )}
      onClick={handleClick}
    >
      <div className="inline-block min-w-full align-middle">
        <table className="min-w-full divide-y divide-gray-300 text-xs">
          <tbody className="divide-y divide-gray-200 bg-white">
            {grid.map((row, rowIndex) => (
              <tr key={rowIndex} className="hover:bg-gray-50">
                {row.map((cell, cellIndex) => {
                  const isHeader = cell.column_header || cell.row_header;
                  const CellTag = isHeader ? 'th' : 'td';
                  
                  return (
                    <CellTag
                      key={cellIndex}
                      rowSpan={cell.row_span > 1 ? cell.row_span : undefined}
                      colSpan={cell.col_span > 1 ? cell.col_span : undefined}
                      className={cn(
                        "px-2 py-1.5 text-left align-top max-w-xs",
                        isHeader
                          ? "font-semibold text-gray-900 bg-gray-100"
                          : "text-gray-700",
                        cell.text === "" && "bg-gray-50"
                      )}
                    >
                      <div className="line-clamp-6 break-words">
                        {cell.text || '\u00A0'}
                      </div>
                    </CellTag>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {pageNumber && (
        <div className="px-3 py-1.5 bg-gray-50 border-t border-gray-200 text-xs text-gray-500">
          Table on page {pageNumber}
        </div>
      )}
    </div>
  );
}
