import type { Entity } from './entities';

// Bounding box data from PDF
export interface BoundingBox {
  l: number;  // left
  t: number;  // top
  r: number;  // right
  b: number;  // bottom
  coord_origin: 'TOPLEFT' | 'BOTTOMLEFT';
}

// Text span location information
export interface TextSpanLocation {
  chunk_id: number;
  sentence_range: [number, number];
  document_offsets: {
    start: number;
    end: number;
  };
}

// Subject/Object position in text
export interface TextPosition {
  start: number;
  end: number;
  sentence_id: number;
  matched_text: string;
}

// Source span with text evidence
export interface SourceSpan {
  span_type: 'single_sentence' | 'multi_sentence' | 'cross_paragraph';
  text_evidence: string;
  confidence: number;
  docling_ref?: string; // Direct reference to Docling JSON element (e.g., "#/texts/19")
  location: TextSpanLocation;
}

// Relation with full provenance
export interface Relation {
  id: string;
  predicate: string;
  subject: Entity;
  object: Entity;
  section?: string;
  pages?: number[];
  source_paper?: string;
  confidence?: number;
  bbox_data?: BoundingBox;
}

// Relation search result
export interface RelationSearchResult extends Relation {
  // May include additional search metadata
}

// Detailed provenance information
export interface RelationProvenance {
  relation_id: string;
  section: string;
  pages: number[];
  bbox_data?: Array<{
    page: number;
    bbox: BoundingBox;
  }>;
  source_paper: string;
  extraction_method: string;
}

// Source span with positions
export interface RelationSourceSpan {
  relation_id: string;
  subject: string;
  predicate: string;
  object: string;
  source_span: SourceSpan;
  subject_positions: TextPosition[];
  object_positions: TextPosition[];
}

// Predicate frequency
export interface PredicateFrequency {
  predicate: string;
  count: number;
}

export interface PredicateFrequencyResponse {
  total_unique_predicates: number;
  predicate_frequencies: PredicateFrequency[];
}
