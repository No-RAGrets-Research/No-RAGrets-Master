/**
 * Extract figure images from PDF using PDF.js
 */

import * as pdfjsLib from 'pdfjs-dist';
import type { DoclingProvenance } from './docling';

// Set worker source - use CDN like other PDF.js instances
if (typeof window !== 'undefined') {
  pdfjsLib.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjsLib.version}/build/pdf.worker.min.mjs`;
}

/**
 * Extract a figure region from a PDF page as a data URL
 * @param pdfUrl - URL to the PDF file
 * @param pageNumber - 1-indexed page number
 * @param bbox - Normalized bounding box (0-1 range)
 * @returns Data URL of the extracted figure image
 */
export async function extractFigureFromPDF(
  pdfUrl: string,
  pageNumber: number,
  bbox: DoclingProvenance['bbox']
): Promise<string> {
  try {
    console.log('[pdfFigureExtractor] Extracting figure:', { pdfUrl, pageNumber, bbox });
    
    // Load the PDF document
    const loadingTask = pdfjsLib.getDocument(pdfUrl);
    const pdf = await loadingTask.promise;
    console.log('[pdfFigureExtractor] PDF loaded successfully, total pages:', pdf.numPages);

    // Get the specific page
    const page = await pdf.getPage(pageNumber);
    console.log('[pdfFigureExtractor] Page loaded:', pageNumber);

    // Get page viewport at scale 2 for better quality
    const scale = 2.0;
    const viewport = page.getViewport({ scale });
    console.log('[pdfFigureExtractor] Viewport size:', { width: viewport.width, height: viewport.height });

    // Docling bbox is in PDF points (72 points per inch), NOT normalized 0-1
    // coord_origin can be BOTTOMLEFT or TOPLEFT
    // PDF.js uses TOPLEFT for canvas rendering
    
    let pixelBbox;
    if (bbox.coord_origin === 'BOTTOMLEFT') {
      // Convert BOTTOMLEFT to TOPLEFT coordinates
      // In BOTTOMLEFT: t is distance from bottom, b is distance from bottom (b < t)
      // In TOPLEFT: top is distance from top
      const pageHeightInPoints = viewport.height / scale; // Get actual page height in PDF points
      pixelBbox = {
        left: bbox.l * scale,
        top: (pageHeightInPoints - bbox.t) * scale,  // Convert bottom-origin to top-origin
        right: bbox.r * scale,
        bottom: (pageHeightInPoints - bbox.b) * scale,  // Convert bottom-origin to top-origin
      };
    } else {
      // TOPLEFT - use directly
      pixelBbox = {
        left: bbox.l * scale,
        top: bbox.t * scale,
        right: bbox.r * scale,
        bottom: bbox.b * scale,
      };
    }

    const width = pixelBbox.right - pixelBbox.left;
    const height = pixelBbox.bottom - pixelBbox.top;
    console.log('[pdfFigureExtractor] Figure dimensions:', { width, height, pixelBbox, originalBbox: bbox });

    // Create canvas for the extracted region
    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    const context = canvas.getContext('2d');

    if (!context) {
      throw new Error('Could not get canvas context');
    }

    // Render the full page to a temporary canvas
    const tempCanvas = document.createElement('canvas');
    tempCanvas.width = viewport.width;
    tempCanvas.height = viewport.height;
    const tempContext = tempCanvas.getContext('2d');

    if (!tempContext) {
      throw new Error('Could not get temp canvas context');
    }

    await page.render({
      canvasContext: tempContext,
      viewport: viewport,
      canvas: tempCanvas,
    }).promise;

    // Extract the figure region from the full page render
    context.drawImage(
      tempCanvas,
      pixelBbox.left, // source x
      pixelBbox.top, // source y
      width, // source width
      height, // source height
      0, // dest x
      0, // dest y
      width, // dest width
      height // dest height
    );

    // Convert to data URL
    const dataUrl = canvas.toDataURL('image/png');
    console.log('[pdfFigureExtractor] Figure extracted successfully, data URL length:', dataUrl.length);

    // Cleanup
    await pdf.destroy();

    return dataUrl;
  } catch (error) {
    console.error('[pdfFigureExtractor] Failed to extract figure from PDF:', error);
    throw error;
  }
}

/**
 * Preload multiple figures from a PDF
 * @param pdfUrl - URL to the PDF file
 * @param figures - Array of figure metadata with page and bbox
 * @returns Map of figure self_ref to data URL
 */
export async function preloadFigures(
  pdfUrl: string,
  figures: Array<{ self_ref: string; prov: DoclingProvenance[] }>
): Promise<Map<string, string>> {
  const figureMap = new Map<string, string>();

  for (const figure of figures) {
    if (figure.prov.length === 0) continue;

    try {
      const dataUrl = await extractFigureFromPDF(
        pdfUrl,
        figure.prov[0].page_no,
        figure.prov[0].bbox
      );
      figureMap.set(figure.self_ref, dataUrl);
    } catch (error) {
      console.error(`Failed to extract figure ${figure.self_ref}:`, error);
    }
  }

  return figureMap;
}
