// Paper information
export interface Paper {
  id: string;
  title: string;
  filename: string;
  processed_at?: string;
  total_entities?: number;
  total_relations?: number;
  sections?: string[];
  authors?: string[];
  year?: number;
}

// Paper list response
export type PaperListResponse = Paper[];

// Paper entities response
export interface PaperEntity {
  id: string;
  name: string;
  type: string;
  section?: string;
}

export interface PaperEntitiesResponse {
  paper_id: string;
  entities: PaperEntity[];
  total: number;
}
