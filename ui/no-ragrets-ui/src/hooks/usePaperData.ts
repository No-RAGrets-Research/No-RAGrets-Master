import { useQuery, type UseQueryResult } from '@tanstack/react-query';
import { getAllPapers, getPaperById, getPaperEntities, getPaperRelations } from '../services/api';
import type {
  Paper,
  PaperListResponse,
  PaperEntitiesResponse,
  PaperEntitiesParams,
  Relation,
} from '../types';

// Hook for getting all papers
export const usePapers = (): UseQueryResult<PaperListResponse, Error> => {
  return useQuery({
    queryKey: ['papers'],
    queryFn: () => getAllPapers(),
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
};

// Hook for getting a specific paper
export const usePaper = (
  paperId: string,
  enabled: boolean = true
): UseQueryResult<Paper, Error> => {
  return useQuery({
    queryKey: ['papers', paperId],
    queryFn: () => getPaperById(paperId),
    enabled: enabled && !!paperId,
    staleTime: 10 * 60 * 1000,
  });
};

// Hook for getting paper entities
export const usePaperEntities = (
  paperId: string,
  params?: PaperEntitiesParams,
  enabled: boolean = true
): UseQueryResult<PaperEntitiesResponse, Error> => {
  return useQuery({
    queryKey: ['papers', paperId, 'entities', params],
    queryFn: () => getPaperEntities(paperId, params),
    enabled: enabled && !!paperId,
    staleTime: 5 * 60 * 1000,
  });
};

// Hook for getting paper relations
export const usePaperRelations = (
  paperFilename: string,
  enabled: boolean = true
): UseQueryResult<Relation[], Error> => {
  return useQuery({
    queryKey: ['papers', 'relations', paperFilename],
    queryFn: () => getPaperRelations(paperFilename),
    enabled: enabled && !!paperFilename,
    staleTime: 5 * 60 * 1000,
  });
};
