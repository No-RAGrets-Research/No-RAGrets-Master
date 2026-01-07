import { apiClient } from './client';
import type {
  Relation,
  RelationSearchResult,
  RelationProvenance,
  RelationSourceSpan,
  PredicateFrequencyResponse,
  RelationSearchParams,
} from '../../types';

// Search relations by predicate, subject, object, or section
export const searchRelations = async (
  params: RelationSearchParams
): Promise<RelationSearchResult[]> => {
  const response = await apiClient.get<RelationSearchResult[]>('/api/relations/search', {
    params,
  });
  return response.data;
};

// Get detailed provenance for a relation
export const getRelationProvenance = async (
  relationId: string
): Promise<RelationProvenance> => {
  const response = await apiClient.get<RelationProvenance>(
    `/api/relations/${relationId}/provenance`
  );
  return response.data;
};

// Get source span with exact text and character positions
export const getRelationSourceSpan = async (
  relationId: string
): Promise<RelationSourceSpan> => {
  const response = await apiClient.get<RelationSourceSpan>(
    `/api/relations/${relationId}/source-span`
  );
  return response.data;
};

// Get section image with highlighted relation (returns image blob)
export const getRelationSectionImage = async (
  relationId: string
): Promise<Blob> => {
  const response = await apiClient.get(`/api/relations/${relationId}/section-image`, {
    responseType: 'blob',
  });
  return response.data;
};

// Get predicate frequency distribution
export const getPredicateFrequency = async (): Promise<PredicateFrequencyResponse> => {
  const response = await apiClient.get<PredicateFrequencyResponse>(
    '/api/predicates/frequency'
  );
  return response.data;
};

// Get relation by ID
export const getRelationById = async (relationId: string): Promise<Relation> => {
  const response = await apiClient.get<Relation>(`/api/relations/${relationId}`);
  return response.data;
};

// NEW: Lazy-loading endpoints for click-to-lookup

// Get relations by chunk ID (primary method for text blocks)
export const getRelationsByChunk = async (
  paperId: string,
  chunkId: number
): Promise<Relation[]> => {
  const response = await apiClient.get<Relation[]>('/api/relations/by-chunk', {
    params: { paper_id: paperId, chunk_id: chunkId },
  });
  return response.data;
};

// Get relations by text search (fallback for text blocks)
export const getRelationsByText = async (query: string): Promise<Relation[]> => {
  const response = await apiClient.get<Relation[]>('/api/relations/by-text', {
    params: { q: query },
  });
  return response.data;
};

// Get relations by location (page-based, can filter by bbox)
export const getRelationsByLocation = async (
  paperId: string,
  page?: number
): Promise<Relation[]> => {
  const response = await apiClient.get<Relation[]>('/api/relations/by-location', {
    params: {
      paper_id: paperId,
      ...(page && { page }),
    },
  });
  return response.data;
};

// Get relations by figure ID
export const getRelationsByFigure = async (
  paperId: string,
  figureId: string
): Promise<Relation[]> => {
  const response = await apiClient.get<Relation[]>('/api/relations/by-figure', {
    params: { paper_id: paperId, figure_id: figureId },
  });
  return response.data;
};

// Get relations by table ID
export const getRelationsByTable = async (
  paperId: string,
  tableId: string
): Promise<Relation[]> => {
  const response = await apiClient.get<Relation[]>('/api/relations/by-table', {
    params: { paper_id: paperId, table_id: tableId },
  });
  return response.data;
};
