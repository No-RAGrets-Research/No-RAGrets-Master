// API Response types

// Health check response
export interface HealthResponse {
  status: 'healthy' | 'unhealthy';
  timestamp: string;
  database: string;
  api_version: string;
}

// Graph statistics
export interface GraphStats {
  total_nodes: number;
  total_relations: number;
  total_papers: number;
  unique_predicates: number;
  most_connected_entities?: any[];
}

// API Root response
export interface ApiRootResponse {
  message: string;
  version: string;
  docs: string;
  endpoints: {
    search: string;
    traversal: string;
    provenance: string;
    analytics: string;
  };
}

// Generic API error
export interface ApiError {
  detail: string;
  status?: number;
}

// Search parameters
export interface EntitySearchParams {
  q: string;
  type?: string;
  namespace?: string;
  limit?: number;
}

export interface RelationSearchParams {
  predicate?: string;
  subject?: string;
  object?: string;
  section?: string;
  limit?: number;
}

export interface EntityConnectionsParams {
  direction?: 'incoming' | 'outgoing' | 'both';
  max_relations?: number;
}

export interface PathParams {
  max_depth?: number;
}

export interface PaperEntitiesParams {
  section?: string;
  limit?: number;
}

export interface MostConnectedParams {
  limit?: number;
}
