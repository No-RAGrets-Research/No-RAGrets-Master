import * as pdfjsLib from 'pdfjs-dist';
import type { TextItem } from 'pdfjs-dist/types/src/display/api';

pdfjsLib.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjsLib.version}/build/pdf.worker.min.mjs`;

export interface ExtractedTextItem {
  text: string;
  x: number;
  y: number;
  width: number;
  height: number;
  page: number;
}

export interface ExtractedPage {
  pageNumber: number;
  items: ExtractedTextItem[];
  width: number;
  height: number;
}

export const extractTextFromPDF = async (pdfUrl: string): Promise<ExtractedPage[]> => {
  const loadingTask = pdfjsLib.getDocument(pdfUrl);
  const pdf = await loadingTask.promise;
  
  const pages: ExtractedPage[] = [];
  
  for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) {
    const page = await pdf.getPage(pageNum);
    const textContent = await page.getTextContent();
    const viewport = page.getViewport({ scale: 1.0 });
    
    const items: ExtractedTextItem[] = textContent.items
      .filter((item): item is TextItem => 'str' in item)
      .map((item) => ({
        text: item.str,
        x: item.transform[4],
        y: item.transform[5],
        width: item.width,
        height: item.height,
        page: pageNum,
      }));
    
    pages.push({
      pageNumber: pageNum,
      items,
      width: viewport.width,
      height: viewport.height,
    });
  }
  
  return pages;
};

export const groupTextIntoLines = (items: ExtractedTextItem[]): string[] => {
  if (items.length === 0) return [];
  
  // Sort items by Y position (top to bottom), then X position (left to right)
  const sorted = [...items].sort((a, b) => {
    const yDiff = b.y - a.y; // Reverse Y because PDF coordinates
    if (Math.abs(yDiff) > 5) return yDiff;
    return a.x - b.x;
  });
  
  const lines: string[][] = [];
  let currentLine: ExtractedTextItem[] = [sorted[0]];
  let currentY = sorted[0].y;
  
  for (let i = 1; i < sorted.length; i++) {
    const item = sorted[i];
    
    // If Y position is significantly different, start a new line
    if (Math.abs(item.y - currentY) > 5) {
      lines.push(currentLine.map(i => i.text));
      currentLine = [item];
      currentY = item.y;
    } else {
      currentLine.push(item);
    }
  }
  
  if (currentLine.length > 0) {
    lines.push(currentLine.map(i => i.text));
  }
  
  return lines.map(line => line.join(' '));
};

export const groupTextIntoParagraphs = (lines: string[]): string[] => {
  const paragraphs: string[] = [];
  let currentParagraph: string[] = [];
  
  for (const line of lines) {
    const trimmed = line.trim();
    
    // Skip empty lines
    if (!trimmed) {
      if (currentParagraph.length > 0) {
        paragraphs.push(currentParagraph.join(' '));
        currentParagraph = [];
      }
      continue;
    }
    
    currentParagraph.push(trimmed);
  }
  
  if (currentParagraph.length > 0) {
    paragraphs.push(currentParagraph.join(' '));
  }
  
  return paragraphs;
};
