import { apiClient } from './client';
import type {
  Paper,
  PaperListResponse,
  PaperEntitiesResponse,
  PaperEntitiesParams,
} from '../../types';

// Get all papers in the knowledge graph
export const getAllPapers = async (): Promise<PaperListResponse> => {
  const response = await apiClient.get<PaperListResponse>('/api/papers');
  return response.data;
};

// Get paper by ID
export const getPaperById = async (paperId: string): Promise<Paper> => {
  const response = await apiClient.get<Paper>(`/api/papers/${encodeURIComponent(paperId)}`);
  return response.data;
};

// Get all entities from a specific paper
export const getPaperEntities = async (
  paperId: string,
  params?: PaperEntitiesParams
): Promise<PaperEntitiesResponse> => {
  const response = await apiClient.get<PaperEntitiesResponse>(
    `/api/papers/${encodeURIComponent(paperId)}/entities`,
    { params }
  );
  return response.data;
};

// Get paper relations by searching with source_paper filter
export const getPaperRelations = async (paperFilename: string): Promise<any[]> => {
  const response = await apiClient.get('/api/relations/search', {
    params: {
      source_paper: paperFilename,
      limit: 1000,  // Get all relations for this paper
    },
  });
  return response.data;
};
