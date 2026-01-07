import { useQuery, type UseQueryResult } from '@tanstack/react-query';
import {
  searchRelations,
  getRelationProvenance,
  getRelationSourceSpan,
  getPredicateFrequency,
} from '../services/api';
import type {
  RelationSearchResult,
  RelationProvenance,
  RelationSourceSpan,
  PredicateFrequencyResponse,
  RelationSearchParams,
} from '../types';

// Hook for searching relations
export const useRelationSearch = (
  params: RelationSearchParams,
  enabled: boolean = true
): UseQueryResult<RelationSearchResult[], Error> => {
  return useQuery({
    queryKey: ['relations', 'search', params],
    queryFn: () => searchRelations(params),
    enabled,
    staleTime: 5 * 60 * 1000,
  });
};

// Hook for getting relation provenance
export const useRelationProvenance = (
  relationId: string,
  enabled: boolean = true
): UseQueryResult<RelationProvenance, Error> => {
  return useQuery({
    queryKey: ['relations', relationId, 'provenance'],
    queryFn: () => getRelationProvenance(relationId),
    enabled: enabled && !!relationId,
    staleTime: 10 * 60 * 1000,
  });
};

// Hook for getting relation source span
export const useRelationSourceSpan = (
  relationId: string,
  enabled: boolean = true
): UseQueryResult<RelationSourceSpan, Error> => {
  return useQuery({
    queryKey: ['relations', relationId, 'source-span'],
    queryFn: () => getRelationSourceSpan(relationId),
    enabled: enabled && !!relationId,
    staleTime: 10 * 60 * 1000,
  });
};

// Hook for getting predicate frequency
export const usePredicateFrequency = (): UseQueryResult<PredicateFrequencyResponse, Error> => {
  return useQuery({
    queryKey: ['predicates', 'frequency'],
    queryFn: () => getPredicateFrequency(),
    staleTime: 15 * 60 * 1000, // 15 minutes
  });
};
