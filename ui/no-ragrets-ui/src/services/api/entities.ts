import { apiClient } from './client';
import type {
  Entity,
  EntitySearchResult,
  EntityConnections,
  MostConnectedEntity,
  EntitySearchParams,
  EntityConnectionsParams,
  MostConnectedParams,
} from '../../types';

// Search entities by name, type, or namespace
export const searchEntities = async (
  params: EntitySearchParams
): Promise<EntitySearchResult[]> => {
  const response = await apiClient.get<EntitySearchResult[]>('/api/entities/search', {
    params,
  });
  return response.data;
};

// Get all connections (incoming/outgoing) for an entity
export const getEntityConnections = async (
  entityName: string,
  params?: EntityConnectionsParams
): Promise<EntityConnections> => {
  const response = await apiClient.get<EntityConnections>(
    `/api/entities/${encodeURIComponent(entityName)}/connections`,
    { params }
  );
  return response.data;
};

// Find path between two entities
export const findPathBetweenEntities = async (
  sourceEntity: string,
  targetEntity: string,
  maxDepth: number = 3
): Promise<any> => {
  const response = await apiClient.get(
    `/api/entities/${encodeURIComponent(sourceEntity)}/path-to/${encodeURIComponent(targetEntity)}`,
    { params: { max_depth: maxDepth } }
  );
  return response.data;
};

// Get most connected entities (hub nodes)
export const getMostConnectedEntities = async (
  params?: MostConnectedParams
): Promise<MostConnectedEntity[]> => {
  const response = await apiClient.get<MostConnectedEntity[]>(
    '/api/entities/most-connected',
    { params }
  );
  return response.data;
};

// Get entity by ID
export const getEntityById = async (entityId: string): Promise<Entity> => {
  const response = await apiClient.get<Entity>(`/api/entities/${entityId}`);
  return response.data;
};
