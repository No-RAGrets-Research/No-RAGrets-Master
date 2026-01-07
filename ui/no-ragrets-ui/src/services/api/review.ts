/**
 * API service for Rubric Review endpoints
 */

import { apiClient } from './client';
import type { RubricName, ReviewResponse } from '@/types/review';
import type { DoclingTable } from '@/utils/docling';
import { loadDoclingData } from '@/utils/docling';

/**
 * Review selected text using a specific rubric
 * @param text - The text to review
 * @param rubricName - The rubric to apply
 * @returns Review response with evaluation
 */
export const reviewText = async (
  text: string,
  rubricName: RubricName
): Promise<ReviewResponse> => {
  // Text reviews with Ollama can take ~30 seconds
  const response = await apiClient.post<ReviewResponse>(
    `/api/review/rubric/${rubricName}`,
    { text },
    {
      timeout: 60000 // 1 minute for text processing
    }
  );
  return response.data;
};

/**
 * Review a figure using base64-encoded image data
 * @param imageData - Base64 data URL (e.g., "data:image/png;base64,...")
 * @param rubricName - The rubric to apply
 * @returns Review response with evaluation
 */
export const reviewFigure = async (
  imageData: string,
  rubricName: RubricName
): Promise<ReviewResponse> => {
  console.log('[reviewFigure] Sending request with rubric:', rubricName);
  console.log('[reviewFigure] Image data length:', imageData.length);
  
  // Vision models can take 60-120 seconds, so increase timeout
  const response = await apiClient.post<ReviewResponse>(
    `/api/review/figure`,
    {
      image_data: imageData,
      rubric: rubricName
    },
    {
      timeout: 180000 // 3 minutes for vision model processing
    }
  );
  
  console.log('[reviewFigure] Response received:', response.data);
  return response.data;
};

/**
 * Review a table using Docling table object
 * @param tableData - Docling table object with caption, text, data, etc.
 * @param rubricName - The rubric to apply
 * @returns Review response with evaluation
 */
export const reviewTable = async (
  tableData: DoclingTable,
  rubricName: RubricName
): Promise<ReviewResponse> => {
  // Table reviews may take longer for complex tables
  const response = await apiClient.post<ReviewResponse>(
    `/api/review/table`,
    {
      table_data: tableData,
      rubric: rubricName
    },
    {
      timeout: 120000 // 2 minutes for table processing
    }
  );
  return response.data;
};

/**
 * Review an entire paper using a specific rubric
 * Loads the paper text from local Docling JSON and sends it to the rubric endpoint
 * @param paperFilename - The filename of the paper to review (e.g., "A. Priyadarsini et al. 2023.pdf")
 * @param rubricName - The rubric to apply
 * @returns Review response with evaluation
 */
export const reviewFullPaper = async (
  paperFilename: string,
  rubricName: RubricName
): Promise<ReviewResponse> => {
  console.log('[reviewFullPaper] Reviewing paper:', paperFilename, 'with rubric:', rubricName);
  
  try {
    // Load the Docling JSON from local files
    console.log('[reviewFullPaper] Loading Docling data...');
    const doclingData = await loadDoclingData(paperFilename);
    
    // Extract all text from the document
    console.log('[reviewFullPaper] Extracting text from', doclingData.texts.length, 'text elements');
    const fullText = doclingData.texts
      .map(textItem => textItem.text)
      .join('\n\n');
    
    console.log('[reviewFullPaper] Extracted text length:', fullText.length, 'characters');
    
    // Send the full text to the rubric endpoint
    // Full paper reviews can take 1-2 minutes
    const response = await apiClient.post<ReviewResponse>(
      `/api/review/rubric/${rubricName}`,
      { text: fullText },
      {
        timeout: 120000 // 2 minutes for full paper processing
      }
    );
    
    console.log('[reviewFullPaper] Review completed successfully');
    return response.data;
  } catch (error) {
    console.error('[reviewFullPaper] Error:', error);
    throw error;
  }
};
