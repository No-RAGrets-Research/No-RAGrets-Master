import { apiClient } from './client';
import type { GraphStats, HealthResponse, ApiRootResponse } from '../../types';

// Get graph statistics
export const getGraphStats = async (): Promise<GraphStats> => {
  const response = await apiClient.get<GraphStats>('/api/graph/stats');
  return response.data;
};

// Health check
export const checkHealth = async (): Promise<HealthResponse> => {
  const response = await apiClient.get<HealthResponse>('/api/health');
  return response.data;
};

// Get API root information
export const getApiInfo = async (): Promise<ApiRootResponse> => {
  const response = await apiClient.get<ApiRootResponse>('/');
  return response.data;
};
