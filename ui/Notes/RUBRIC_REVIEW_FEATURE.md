# Rubric Review Feature - Implementation Plan

## Overview

Add the ability for users to select text in the annotated document view and run AI-powered rubric reviews on that selection. The review system evaluates text quality using 6 specialized rubrics.

## Feature Design

### 1. Trigger Button (Sidebar)

- When user selects text (sentences), a "Review with Rubric" button appears in the sidebar
- Located inside the blue "Selected Content" box, next to the X (close) button
- Prominent, significant button styling (primary blue or purple color)
- Single button that opens the rubric selector dropdown

### 2. Rubric Selection (Dropdown)

- Click the "Review with Rubric" button to open a dropdown menu
- Shows all 6 rubrics with clean labels:
  - Methodology
  - Reproducibility
  - Rigor
  - Data
  - Presentation
  - References
- User clicks one rubric to start the review

### 3. Results Display (Modal/Popup)

- Opens a centered modal overlay over the document
- Semi-transparent backdrop with document visible behind
- Responsive width (max-w-2xl or max-w-3xl, approximately 672-768px)
- Modal content includes:
  - Title: Selected rubric name (e.g., "Methodology Review")
  - The selected text snippet (for context)
  - The full rubric response (scrollable content area)
  - Close button (X in corner)
- Modal dismissed by clicking X or clicking outside backdrop
- Matches existing dark/light theme system

### 4. Loading State

- After selecting a rubric, show loading spinner in the modal
- Display message: "Analyzing with [Rubric] rubric... (~30 seconds)"
- Subtle animation to indicate processing
- Document remains visible and scrollable (but don't allow new text selection)

### 5. No Persistence

- When user selects new text, any previous review is discarded
- Clean slate for each new selection
- Simple and predictable behavior

### 6. Text Only (For Now)

- Only send the exact selected sentence(s) to the API
- Backend will handle figures/tables in future updates
- Frontend passes text string as-is

### 7. Error Handling

- If API fails or times out, show error message in modal
- Display "Retry" button to attempt the review again
- Display "Close" button to exit/dismiss
- Keep the selected text state (so user can retry without reselecting)

## Implementation Structure

### Files to Create

1. `/no-ragrets-ui/src/services/api/review.ts`

   - API service for rubric review calls
   - Function: `reviewText(text: string, rubricName: string)`
   - Calls: `POST /api/review/rubric/{rubricName}`

2. `/no-ragrets-ui/src/types/review.ts`

   - TypeScript types for review responses
   - RubricName type (union of 6 rubric options)
   - ReviewResponse interface

3. `/no-ragrets-ui/src/components/review/RubricReviewModal.tsx`
   - Modal component for displaying reviews
   - Props: isOpen, selectedText, review, loading, error, onClose, onRetry
   - Responsive, themed, scrollable

### Files to Modify

1. `/no-ragrets-ui/src/pages/PaperView.tsx`

   - Add review state management
   - Add "Review" button to SelectionHeader
   - Add rubric dropdown menu
   - Integrate RubricReviewModal component

2. Possibly `/no-ragrets-ui/src/components/annotated-view/AnnotatedView.tsx`
   - If we need to pass review callbacks

## Component Hierarchy

```
PaperView
””€”€ AnnotatedView (handles sentence selection)
”””€”€ Sidebar
   OK””€”€ SelectionHeader (with "Review" button + X button)
   OK”””€”€ Relations List
”””€”€ RubricReviewModal (overlay when active)
```

## State Flow

1. User selects sentencesOK†’ selectedContent exists
2. "Review" button appears in sidebar SelectionHeader
3. User clicks "Review"OK†’ dropdown menu shows 6 rubric options
4. User picks rubric (e.g., "Methodology")
5. Modal opens with loading state and spinner
6. API call executes: `POST /api/review/rubric/methodology { text: "..." }`
7. Response arrives (~30 seconds)OK†’ modal shows review text
8. User closes modal OR selects new textOK†’ review state clears
9. If error occursOK†’ show error message with retry button in modal

## API Integration

### Endpoint

```
POST http://localhost:8002/api/review/rubric/{rubric_name}
```

### Rubric Names (Path Parameter)

- methodology
- reproducibility
- rigor
- data
- presentation
- references

### Request Body

```json
{
  "text": "Selected sentence or paragraph text..."
}
```

### Response

```json
{
  "rubric_name": "rubric1_methodology",
  "response": "Tier 2-3: Adequate methodology with some gaps...\n\nStrengths:\n- Clear experimental design\n- Appropriate controls\n\nWeaknesses:\n- Missing statistical power analysis\n- Limited validation details\n\nRecommendations:\n- Add quantitative validation metrics\n- Include power calculations",
  "metadata": {
    "provider": "ollama",
    "model": "llama3.1:8b"
  }
}
```

### Performance

- Ollama (llama3.1:8b): ~30 seconds per rubric
- OpenAI (gpt-4o-mini): ~5-10 seconds per rubric

## Implementation Steps

### Step 1: Create API Service

Create `reviewText()` function in `/services/api/review.ts`:

- Takes `text` and `rubricName` parameters
- Calls `POST /api/review/rubric/{rubricName}`
- Returns the review response
- Handles errors appropriately

### Step 2: Create TypeScript Types

Create types in `/types/review.ts`:

- RubricName union type
- ReviewResponse interface
- ReviewMetadata interface

### Step 3: Create Modal Component

Create `RubricReviewModal.tsx`:

- Centered overlay with backdrop
- Themed (dark/light mode support)
- Loading state with spinner
- Error state with retry button
- Scrollable content for long reviews
- Responsive design

### Step 4: Integrate into Sidebar

Modify `PaperView.tsx`:

- Add review state (selectedRubric, rubricReview, isReviewLoading, showReviewModal, reviewError)
- Add "Review" button to SelectionHeader (inside blue box, next to X)
- Add rubric dropdown menu component
- Handle rubric selection and API call
- Show/hide modal based on state
- Clear review when new text selected

### Step 5: Testing

- Test with different rubrics
- Test error handling (disconnect backend, timeout)
- Test theme switching (dark/light mode)
- Test responsive design (narrow/wide screens)
- Test long review text (scrolling)
- Test selecting new text (destructive behavior)

## Future Enhancements (Not in This Implementation)

- Support for reviewing figures and tables (requires backend changes)
- Persistence/history of reviews
- Comparison of multiple rubric reviews
- Export review results
- Intelligent rubric suggestions based on content
- Progress indication for long-running reviews
- Context window adjustment (send surrounding text)
