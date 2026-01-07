// Entity types based on the API
export interface Entity {
  id: string;
  name: string;
  type: string;
  namespace?: string;
  created_at?: string;
}

export interface EntitySearchResult extends Entity {
  // Search results may include additional metadata
}

export interface EntityConnection {
  id: string;
  predicate: string;
  subject?: Entity;
  object?: Entity;
}

export interface EntityConnections {
  outgoing: EntityConnection[];
  incoming: EntityConnection[];
}

export interface MostConnectedEntity {
  entity: Entity;
  total_connections: number;
  outgoing_count: number;
  incoming_count: number;
}

// Entity types for color coding
export type EntityType = 
  | 'chemical'
  | 'organism'
  | 'process'
  | 'organelle'
  | 'enzyme'
  | 'protein'
  | 'gene'
  | 'metabolite'
  | 'pathway'
  | string;
