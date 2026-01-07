import { apiClient } from './client';

export interface GraphStats {
  total_nodes: number;
  total_relations: number;
  total_papers: number;
  unique_predicates: number;
  most_connected_entities: any[];
}

// Get graph statistics
export const getGraphStats = async (): Promise<GraphStats> => {
  const response = await apiClient.get<GraphStats>('/api/graph/stats');
  return response.data;
};
