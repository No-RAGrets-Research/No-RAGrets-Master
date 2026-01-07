# No-RAGrets UI - Feature Summary

## Overview

No-RAGrets is a knowledge graph explorer for scientific papers with advanced annotation and navigation capabilities. It enables seamless exploration of entities, relations, and research documents through an integrated interface.

---

## Core Features

### 1. **Knowledge Graph Visualization**

- **Interactive Graph View**: Visualize entities and their relationships using ReactFlow
- **Entity Search**: Search for scientific entities (chemicals, processes, organisms, etc.) with auto-complete
- **Dynamic Graph Loading**:
  - Start with an empty canvas
  - Search and add entities on demand
  - Click nodes to expand their connections (up to 50 relations per entity)
- **Relation Details**: Click edges to see:
  - Subject and object entities with type badges
  - Predicate (relationship type)
  - Source papers, sections, and page numbers
  - Confidence scores
- **Multi-Source Support**: Relations can appear in multiple papers - view all sources
- **Clean UI**: Empty state with search guidance when no entities loaded

### 2. **Document Viewer (Dual Mode)**

#### **Reference PDF View**

- Native PDF rendering with zoom and page navigation
- Click text to see entity and relation information
- Quick access to paper metadata

#### **Annotated Docling View** (Enhanced)

- Structured document rendering from Docling JSON:
  - Text blocks with semantic structure
  - Figures with lazy-loaded extraction from PDF
  - Tables with proper formatting
- **Interactive Elements**:
  - Click sentences to find relations
  - Click figures to find visual relations
  - Click tables to find data relations
- **Smart Relation Search**:
  - Text-based relation discovery
  - Location-based relation discovery
  - Figure and table relation discovery
- **Visual Feedback**:
  - Blue highlighting for exact relation matches
  - Yellow highlighting for approximate matches
  - Loading indicators during relation search

### 3. **Bidirectional Navigation**

#### **Graph → Paper Navigation**

- Click edge in knowledge graph
- Select "View in Paper" from relation sources
- Automatically:
  - Opens the paper in annotated view
  - Scrolls to the exact location using `docling_ref`
  - Highlights the relevant text/figure/table
  - Shows relation details in sidebar

#### **Paper → Graph Navigation** (NEW!)

- Click text/figure/table in paper to find relations
- Select a specific relation from sidebar
- Click "View in Graph" button
- Automatically:
  - Opens knowledge graph view
  - Loads subject and object entities
  - Shows only the specific relation clicked
  - Clean 2-node view for focused exploration

### 4. **Relation Discovery System**

#### **Exact Matching**

- Uses backend `docling_ref` field for direct DOM element lookup
- Supports all element types:
  - Text blocks: `#/texts/N`
  - Figures: `#/pictures/N`
  - Tables: `#/tables/N`
- Fast, reliable scrolling with retry logic (3 attempts)

#### **Approximate Matching (Fallback)**

When exact relation not found, intelligent fallback:

- **Strategy 1**: Find text blocks mentioning subject OR object entity
- **Strategy 2**: Scroll to first text on target page
- Visual differentiation with yellow highlighting
- Informative messages explaining approximate vs exact matches

### 5. **AI-Powered Content Review**

- **Rubric-Based Analysis**: Review content against specific rubrics:
  - Clarity and Coherence
  - Data Reporting Quality
  - Hypothesis Validity
  - Experimental Design
  - Methodology Soundness
- **Multi-Content Support**:
  - Text selections
  - Figures (via image analysis)
  - Tables (structured data)
  - Full papers
- **Detailed Feedback**: Get AI-generated assessment with scoring and recommendations

### 6. **Entity & Relation Management**

- **Entity Types**: Scientific entities categorized by type
  - Chemical compounds
  - Biological processes
  - Organisms
  - Physical properties
  - And more...
- **Entity Filtering**: View entities grouped by type with counts
- **Relation Display**:
  - Clear subject-predicate-object structure
  - Metadata (section, pages, confidence)
  - Type badges for entity classification

---

## User Interface Components

### **Main Layout**

- **Sidebar Navigation**:
  - Dashboard (overview)
  - Knowledge Graph (entity exploration)
  - Papers list (quick access to all documents)
- **Dark Mode Support**: Full dark/light theme support throughout
- **Responsive Design**: Adapts to different screen sizes

### **Knowledge Graph Panel**

- Search bar with live results
- ReactFlow canvas with controls:
  - Zoom in/out
  - Fit view
  - Minimap for navigation
- Relation detail sidebar (expandable)
- Graph statistics display

### **Paper View Panel**

- View mode toggle (Reference PDF ↔ Annotated)
- Entity panel with:
  - Type-based entity grouping
  - Relation discovery from selections
  - Selected content preview
  - Review button for AI analysis
- Relation detail modal with "View in Graph" button

---

## Technical Highlights

### **Performance Optimizations**

- Lazy loading of PDF figures (only load visible figures)
- Intersection observer for viewport detection
- Debounced search (200ms) for responsive typing
- Smart relation caching

### **Data Integration**

- **Backend API**: RESTful endpoints for entities, relations, and papers
- **Dgraph Database**: GraphQL for knowledge graph queries
- **Docling JSON**: Structured document representation
- **PDF.js**: Native PDF rendering and figure extraction

### **Navigation Flow**

- React Router for SPA navigation
- Navigation state for cross-view communication
- History management for proper back/forward behavior
- URL-based paper identification

### **Visual Feedback**

- Loading spinners and progress indicators
- Highlight animations (smooth scroll, fade effects)
- Color-coded feedback:
  - Blue: Exact matches
  - Yellow: Approximate matches
  - Purple: Predicates/relations
  - Gray: Metadata

---

## Current Limitations & Future Enhancements

### **Known Limitations**

- Some relations may not have exact `docling_ref` (fallback to approximate)
- Figure extraction can be slow for large PDFs
- Entity extraction quality varies by paper
- Graph can become cluttered with highly connected entities

### **Potential Improvements**

- Reverse direction: Paper → Graph entity expansion
- Graph layout algorithms (force-directed, hierarchical)
- Relation filtering by confidence threshold
- Export graph as image/data
- Collaborative annotations
- Custom entity type creation
- Batch paper processing

---

## Getting Started

1. **Explore the Knowledge Graph**:

   - Navigate to "Knowledge Graph"
   - Search for an entity (e.g., "methane", "carbon")
   - Click nodes to expand connections
   - Click edges to see relation details

2. **Read a Paper**:

   - Select a paper from the sidebar
   - Toggle to "Annotated" view
   - Click text/figures/tables to find relations
   - Use "View in Graph" to explore entities

3. **Navigate Between Views**:
   - From graph: Click edge → "View in Paper"
   - From paper: Click relation → "View in Graph"
   - Seamlessly explore the knowledge space

---

## Technology Stack

- **Frontend**: React + TypeScript
- **Routing**: React Router v6
- **Graph Viz**: ReactFlow
- **Styling**: Tailwind CSS
- **PDF**: PDF.js
- **Build**: Vite
- **Backend**: Python FastAPI (assumed)
- **Database**: Dgraph (GraphQL)
