import { useQuery, type UseQueryResult } from '@tanstack/react-query';
import { searchEntities, getEntityConnections, getMostConnectedEntities } from '../services/api';
import type {
  EntitySearchResult,
  EntityConnections,
  MostConnectedEntity,
  EntitySearchParams,
  EntityConnectionsParams,
  MostConnectedParams,
} from '../types';

// Hook for searching entities
export const useEntitySearch = (
  params: EntitySearchParams,
  enabled: boolean = true
): UseQueryResult<EntitySearchResult[], Error> => {
  return useQuery({
    queryKey: ['entities', 'search', params],
    queryFn: () => searchEntities(params),
    enabled: enabled && !!params.q,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

// Hook for getting entity connections
export const useEntityConnections = (
  entityName: string,
  params?: EntityConnectionsParams,
  enabled: boolean = true
): UseQueryResult<EntityConnections, Error> => {
  return useQuery({
    queryKey: ['entities', entityName, 'connections', params],
    queryFn: () => getEntityConnections(entityName, params),
    enabled: enabled && !!entityName,
    staleTime: 5 * 60 * 1000,
  });
};

// Hook for getting most connected entities
export const useMostConnectedEntities = (
  params?: MostConnectedParams
): UseQueryResult<MostConnectedEntity[], Error> => {
  return useQuery({
    queryKey: ['entities', 'most-connected', params],
    queryFn: () => getMostConnectedEntities(params),
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
};
