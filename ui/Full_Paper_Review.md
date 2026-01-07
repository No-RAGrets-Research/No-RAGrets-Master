# Full Paper Review Feature

## Overview

The Full Paper Review feature allows users to evaluate an entire research paper against a specific rubric with a single click, without having to manually select text passages. This provides comprehensive feedback on aspects like methodology, reproducibility, rigor, data quality, presentation, and references.

## How It Works

### 1. **User Interface**

- A blue "Review Full Paper" button appears in the paper view toolbar next to the paper title
- Clicking the button reveals a dropdown menu with 6 rubric options:
  - **Methodology**: Evaluates methodological transparency and detail
  - **Reproducibility**: Assesses if experiments can be reproduced
  - **Rigor**: Checks statistical rigor and experimental design
  - **Data**: Reviews data presentation and availability
  - **Presentation**: Evaluates clarity and organization
  - **References**: Checks citation quality and completeness

### 2. **Data Flow**

When a user selects a rubric:

1. **Load Local Paper Data**

   - The system loads the paper's Docling JSON file from `public/docling_json/`
   - Docling is a document parsing library that converts PDFs into structured JSON
   - Example: `A. Priyadarsini et al. 2023.pdf` → `A. Priyadarsini et al. 2023.json`

2. **Extract Full Text**

   - The Docling JSON contains all text elements from the paper with structure:
     ```json
     {
       "texts": [
         {
           "self_ref": "#/texts/0",
           "text": "Introduction\n\nThis paper presents...",
           "label": "section_header",
           "prov": [{"page_no": 1, ...}]
         },
         ...
       ]
     }
     ```
   - The system extracts all text elements and joins them with double newlines
   - This preserves the document structure while creating a readable flow

3. **Send to Backend API**

   - **Endpoint**: `POST /api/review/rubric/{rubricName}`
   - **Request Body**:
     ```json
     {
       "text": "Full paper text content..."
     }
     ```
   - **Timeout**: 120 seconds (2 minutes) for processing
   - The backend uses OpenAI's GPT-4o-mini model to analyze the text

4. **Display Results**
   - The response includes:
     - Rubric name
     - Detailed evaluation with structured feedback
     - Metadata (provider: "openai", model: "gpt-4o-mini")
   - Results appear in a modal with:
     - Good Practices
     - Missing/Weak Points
     - Improvement Suggestions

### 3. **Technical Implementation**

**Frontend (React + TypeScript)**:

- `reviewFullPaper()` in `services/api/review.ts`:

  ```typescript
  export const reviewFullPaper = async (
    paperFilename: string,
    rubricName: RubricName
  ): Promise<ReviewResponse> => {
    // Load Docling JSON from local files
    const doclingData = await loadDoclingData(paperFilename);

    // Extract all text
    const fullText = doclingData.texts
      .map((textItem) => textItem.text)
      .join("\n\n");

    // Send to backend
    const response = await apiClient.post(
      `/api/review/rubric/${rubricName}`,
      { text: fullText },
      { timeout: 120000 }
    );

    return response.data;
  };
  ```

**Backend (FastAPI + OpenAI)**:

- Receives full text content
- Loads the appropriate rubric evaluation criteria
- Sends text + rubric to GPT-4o-mini
- Returns structured evaluation

### 4. **Performance**

- **Text Extraction**: < 1 second (local file read)
- **API Request**: 30-120 seconds depending on paper length
- **Total Time**: Typically 1-2 minutes for a full paper review
- **Timeout**: Set to 2 minutes to accommodate longer papers

### 5. **Error Handling**

The system handles several error cases:

- **Missing Docling JSON**: Shows error if paper hasn't been processed
- **Network Timeout**: 2-minute timeout with clear error message
- **API Errors**: Backend errors are caught and displayed to user
- **Loading States**: Shows spinner and blocks UI during processing

## Advantages Over Manual Selection

1. **Comprehensive Coverage**: Reviews the entire paper, not just selected passages
2. **Time Saving**: Single click instead of multiple text selections
3. **Consistency**: Applies rubric criteria uniformly across the whole document
4. **Context Preservation**: AI sees full paper context for better evaluation

## Usage Tips

- **Paper Length**: Longer papers (30+ pages) may approach the 2-minute timeout
- **Rubric Selection**: Choose the most relevant rubric for your evaluation needs
- **Results Review**: Read the structured feedback sections in order (Good → Weak → Suggestions)
- **Follow-up**: Use regular text selection reviews for deeper dives into specific sections

## Technical Notes

### Why Load Files Locally?

We initially tried sending the PDF filename to the backend to let it load the file directly, but encountered path configuration issues. Loading the Docling JSON locally solves this by:

- Using files already available in the frontend's public directory
- Avoiding backend file system dependencies
- Providing faster initial response (no backend file I/O)
- Allowing the frontend to cache/preload paper data

### Docling JSON Structure

The Docling format provides:

- Structured text with labels (headers, captions, body text)
- Page numbers and bounding boxes for each element
- Separate collections for texts, pictures, and tables
- References between elements (e.g., captions → figures)

This structure allows us to extract clean, ordered text that maintains the paper's logical flow while removing PDF artifacts.

## Future Enhancements

Potential improvements:

- **Progress Indicator**: Show progress percentage during long reviews
- **Section-Level Reviews**: Option to review individual sections
- **Comparison Mode**: Compare multiple rubric evaluations side-by-side
- **Export**: Download review results as PDF or Markdown
- **Batch Processing**: Queue multiple papers for review
- **Custom Rubrics**: Allow users to define their own evaluation criteria
