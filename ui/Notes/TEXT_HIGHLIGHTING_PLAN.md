# Text-Based Highlighting Implementation Plan

## Problem

Current bounding box approach has issues:

- API bbox coordinates are rough/misaligned
- Different PDF coordinate systems (TOPLEFT vs BOTTOMLEFT)
- Doesn't scale well with zoom
- Manual coordinate translation is error-prone

## Solution: Text-Based Highlighting + Area Selection

Use `react-pdf-highlighter` library to search for and highlight text directly in the PDF, **plus support for rectangular area selection for figures/images**.

## Key Features Confirmed

1. **Text-based highlighting**OKOK - The library's core strength, searches for text in PDF
2. **Area/Image highlighting**OKOK - **CONFIRMED!** Supports rectangular area selection for figures/images
   - Hold Alt/Option key + click and drag to create area highlight
   - Uses `AreaHighlight` component (separate from text `Highlight`)
   - Takes screenshot of selected area and stores as base64 PNG
   - Creates draggable/resizable bounding boxes with `react-rnd` library
   - Stores `content.image` (base64 PNG) instead of `content.text`
   - Example in demo: highlighting code blocks, diagrams, figures
3. **Multi-highlight support**OKOK - Can show many highlights simultaneously
4. **Scroll to highlight**OKOK - Built-in navigation
5. **Custom styling**OKOK - Configurable highlight colors and styles

## Implementation Strategy

### Phase 1: Install & Setup (30 min)

1. **Install library**

   ```bash
   npm install react-pdf-highlighter
   ```

2. **Import CSS**

   ```typescript
   import "react-pdf-highlighter/dist/style.css";
   ```

3. **Replace PDFViewer component** with PdfHighlighter from library

### Phase 2: Text Search & Highlight (1-2 hours)

When user clicks a relation:

1. **Get source text** from API

   - Already have: `/api/relations/{id}/source-span` endpoint
   - Returns: `source_span.text` - the actual sentence/text where relation was found

2. **Search for text in PDF**

   - Use react-pdf-highlighter's text search
   - Find all occurrences of the source text
   - Highlight the matching text

3. **Fallback to bbox if needed**
   - If text search fails (OCR issues, different encoding)
   - Fall back to current bbox approach

### Phase 3: Enhanced Features (2-3 hours)

1. **Multi-highlight support**

   - Show all relations on current page highlighted at once
   - Color-code by entity type
   - Click to see which relation

2. **Scroll to highlight**

   - When clicking relation, auto-scroll PDF to that location
   - Navigate between page if needed

3. **Hover preview**
   - Hover over highlighted text to see relation details
   - Tooltip showing subjectOK†’ predicateOK†’ object

## API Integration Points

### Existing Endpoints We'll Use

1. **Get relation provenance**

   - `GET /api/relations/{id}/provenance`
   - Returns: pages, section, bbox_data

2. **Get source span** (KEY!)
   - `GET /api/relations/{id}/source-span`
   - Returns: `source_span.text` - the actual extracted text
   - This is what we'll search for in the PDF

### Data Flow

```
User clicks relation
 OK†
Fetch source-span API
 OK†
Get source_span.text
 OK†
Search for text in PDF using react-pdf-highlighter
 OK†
Highlight all matches
 OK†
Scroll to first match
```

## Benefits Over Current Approach

1.OKOK **Accurate** - Finds exact text, not approximate coordinates
2.OKOK **Scalable** - Works at any zoom level
3.OKOK **Robust** - Library handles PDF quirks
4.OKOK **Better UX** - Can highlight actual words, not just boxes
5.OKOK **Multi-page** - Can highlight same entity across pages
6.OKOK **Persistent** - Can save highlight positions

## Implementation Notes

### react-pdf-highlighter Key Features

- Built on PDF.js (same as current setup)
- Text layer support (selectable text)
- Image highlights (for figures)
- Popover support (for relation details)
- Scroll-to-highlight
- Custom styling

### Migration Path

1. Keep current PDFViewer for now
2. Create new `PdfHighlighterView` component
3. Test side-by-side
4. Switch when ready
5. Remove old bounding box code

## Code Structure

```
src/components/pdf-viewer/
 OK””€”€ PDFViewer.tsx (keep for fallback)
 OK””€”€ PdfHighlighterView.tsx (NEW - main component)
 OK””€”€ HighlightPopup.tsx (NEW - shows relation on hover)
 OK”””€”€ useTextHighlighting.ts (NEW - search logic)
```

## Next Steps

1. Install react-pdf-highlighter
2. Create proof-of-concept with one relation
3. Test text search accuracy
4. Implement full integration
5. Add multi-highlight support
6. Polish UI/UX

## Estimated Timeline

- Basic text highlighting: 2-3 hours
- Full integration: 4-6 hours
- Polish & testing: 2-3 hours
- **Total: 8-12 hours**

## Alternative: Hybrid Approach

If text search has issues with some PDFs:

1. Try text search first (primary)
2. Fall back to bbox if text not found (fallback)
3. Show indicator which method was used
4. Let user toggle between methods
