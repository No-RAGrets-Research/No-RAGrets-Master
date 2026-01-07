import { useState, useEffect, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Search, BarChart3, Info } from 'lucide-react';
import ReactFlow, {
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  BackgroundVariant,
  MiniMap,
  type Node,
} from 'reactflow';
import 'reactflow/dist/style.css';
import '@/styles/reactflow-custom.css';
import { getGraphStats, type GraphStats } from '@/services/api/graph';
import { getEntityConnections, searchEntities } from '@/services/api/entities';
import type { EntitySearchResult } from '@/types';

export const GraphView = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [showInfoPanel, setShowInfoPanel] = useState(true);
  const [stats, setStats] = useState<GraphStats | null>(null);
  const [statsLoading, setStatsLoading] = useState(true);
  const [statsError, setStatsError] = useState<string | null>(null);
  
  const [entitiesLoading, setEntitiesLoading] = useState(true);
  const [entitiesError, setEntitiesError] = useState<string | null>(null);

  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<EntitySearchResult[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [showSearchResults, setShowSearchResults] = useState(false);

  // Selected entity state for info panel
  const [selectedEntity, setSelectedEntity] = useState<{
    name: string;
    id: string;
    type: string;
    connections: any;
  } | null>(null);
  const [showPapersList, setShowPapersList] = useState(true);

  // Selected relation state for relation details panel
  const [selectedRelation, setSelectedRelation] = useState<{
    subject: string;
    predicate: string;
    object: string;
    sources: Array<{
      paper: string;
      section: string;
      pages: number[];
      confidence?: number;
    }>;
  } | null>(null);

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  // Debounced search effect
  useEffect(() => {
    if (searchQuery.trim().length < 1) {
      setSearchResults([]);
      setShowSearchResults(false);
      return;
    }

    const debounceTimer = setTimeout(async () => {
      try {
        setSearchLoading(true);
        const results = await searchEntities({ q: searchQuery, limit: 15 });
        setSearchResults(results);
        setShowSearchResults(true);
      } catch (error) {
        console.error('Search failed:', error);
        setSearchResults([]);
      } finally {
        setSearchLoading(false);
      }
    }, 200); // Faster response - 200ms debounce

    return () => clearTimeout(debounceTimer);
  }, [searchQuery]);

  // Transform entities into ReactFlow nodes
  const createNodesFromEntities = useCallback((entityData: Array<{ name: string; id: string; connections: number }>): Node[] => {
    const maxConnections = Math.max(...entityData.map(e => e.connections), 1);
    
    return entityData.map((item, index) => {
      // Calculate node size based on connections (min 40, max 100)
      const connectionRatio = item.connections / maxConnections;
      const nodeSize = 40 + (connectionRatio * 60);
      
      // Create a grid-like layout with some randomness for natural spread
      // This is more readable than circular and ReactFlow's layout will adjust it
      const cols = Math.ceil(Math.sqrt(entityData.length));
      const row = Math.floor(index / cols);
      const col = index % cols;
      const spacing = 250; // Space between nodes
      const x = col * spacing + Math.random() * 50; // Add slight randomness
      const y = row * spacing + Math.random() * 50;
      
      return {
        id: item.id,
        type: 'default',
        position: { x, y },
        data: {
          label: item.name,
          entityName: item.name, // Store for click handler
          entityId: item.id, // Store for click handler
        },
        style: {
          width: nodeSize,
          height: nodeSize,
          borderRadius: '50%',
          backgroundColor: '#3b82f6',
          color: 'white',
          border: '2px solid #1e40af',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '12px',
          fontWeight: 'bold',
          padding: '8px',
          textAlign: 'center',
          cursor: 'pointer',
        },
      };
    });
  }, []);

  // Handle search input - just update state, useEffect handles the actual search
  const handleSearchInput = useCallback((query: string) => {
    setSearchQuery(query);
  }, []);

  // Load a single entity and its connections into the graph
  const loadEntityAndConnections = useCallback(async (entityName: string, entityId: string) => {
    try {
      setEntitiesLoading(true);
      setEntitiesError(null);
      setShowSearchResults(false);
      setSearchQuery('');
      
      console.log('[GraphView] Loading entity:', entityName);
      
      // Fetch connections for this entity
      const connections = await getEntityConnections(entityName, { max_relations: 50 });
      
      // Filter out connections with missing data
      const validOutgoing = connections.outgoing.filter(c => c.object?.name && c.predicate);
      const validIncoming = connections.incoming.filter(c => c.subject?.name && c.predicate);
      
      console.log('[GraphView] Found connections:', validOutgoing.length + validIncoming.length);
      
      // Build entity map with the main entity and its connections
      const entityMap = new Map<string, { name: string; id: string; connections: number }>();
      
      // Add the main entity (we need to use the entity info passed in since API doesn't return it)
      entityMap.set(entityId, {
        name: entityName,
        id: entityId,
        connections: validOutgoing.length + validIncoming.length,
      });
      
      // Build edges and add connected entities
      const edgeMap = new Map<string, any>(); // Track edges with their sources
      
      // Process outgoing relations
      validOutgoing.forEach((relation: any) => {
        if (!entityMap.has(relation.object.id)) {
          entityMap.set(relation.object.id, {
            name: relation.object.name,
            id: relation.object.id,
            connections: 1,
          });
        }
        
        const edgeId = `${entityId}-${relation.predicate}-${relation.object.id}`;
        
        // Check if edge already exists
        if (edgeMap.has(edgeId)) {
          // Add this source to existing edge
          const existingEdge = edgeMap.get(edgeId);
          existingEdge.data.sources.push({
            paper: relation.source_paper,
            section: relation.section,
            pages: relation.pages || [],
            confidence: relation.confidence,
          });
        } else {
          // Create new edge with first source
          edgeMap.set(edgeId, {
            id: edgeId,
            source: entityId,
            target: relation.object.id,
            type: 'smoothstep',
            animated: false,
            style: { stroke: '#3b82f6', strokeWidth: 2 },
            label: relation.predicate,
            labelStyle: { 
              fill: '#1e293b', 
              fontWeight: 600, 
              fontSize: 11,
            },
            labelBgStyle: { 
              fill: '#f1f5f9', 
              fillOpacity: 0.9,
            },
            labelBgPadding: [4, 6] as [number, number],
            labelBgBorderRadius: 3,
            data: {
              subject: entityName,
              predicate: relation.predicate,
              object: relation.object.name,
              sources: [{
                paper: relation.source_paper,
                section: relation.section,
                pages: relation.pages || [],
                confidence: relation.confidence,
              }],
            },
          });
        }
      });
      
      // Process incoming relations
      validIncoming.forEach((relation: any) => {
        if (!entityMap.has(relation.subject.id)) {
          entityMap.set(relation.subject.id, {
            name: relation.subject.name,
            id: relation.subject.id,
            connections: 1,
          });
        }
        
        const edgeId = `${relation.subject.id}-${relation.predicate}-${entityId}`;
        
        // Check if edge already exists
        if (edgeMap.has(edgeId)) {
          // Add this source to existing edge
          const existingEdge = edgeMap.get(edgeId);
          existingEdge.data.sources.push({
            paper: relation.source_paper,
            section: relation.section,
            pages: relation.pages || [],
            confidence: relation.confidence,
          });
        } else {
          // Create new edge with first source
          edgeMap.set(edgeId, {
            id: edgeId,
            source: relation.subject.id,
            target: entityId,
            type: 'smoothstep',
            animated: false,
            style: { stroke: '#3b82f6', strokeWidth: 2 },
            label: relation.predicate,
            labelStyle: { 
              fill: '#1e293b', 
              fontWeight: 600, 
              fontSize: 11,
            },
            labelBgStyle: { 
              fill: '#f1f5f9', 
              fillOpacity: 0.9,
            },
            labelBgPadding: [4, 6] as [number, number],
            labelBgBorderRadius: 3,
            data: {
              subject: relation.subject.name,
              predicate: relation.predicate,
              object: entityName,
              sources: [{
                paper: relation.source_paper,
                section: relation.section,
                pages: relation.pages || [],
                confidence: relation.confidence,
              }],
            },
          });
        }
      });
      
      // Convert edge map to array
      const edgeList = Array.from(edgeMap.values());
      
      const allEntities = Array.from(entityMap.values());
      console.log('[GraphView] Total entities in graph:', allEntities.length);
      console.log('[GraphView] Total edges:', edgeList.length);
      
      const flowNodes = createNodesFromEntities(allEntities);
      setNodes(flowNodes);
      setEdges(edgeList);
      
    } catch (error) {
      console.error('Failed to load entity:', error);
      setEntitiesError('Failed to load entity');
    } finally {
      setEntitiesLoading(false);
    }
  }, [createNodesFromEntities, setNodes, setEdges]);

  // Handle node click - load entity details in info panel AND optionally expand connections
  const handleNodeClick = useCallback(async (_event: React.MouseEvent, node: Node) => {
    const entityName = node.data.entityName;
    const entityId = node.data.entityId;
    const entityType = node.data.entityType || 'entity';
    
    if (entityName && entityId) {
      console.log('[GraphView] Node clicked:', entityName);
      
      // Fetch full connection data for this entity
      try {
        const connections = await getEntityConnections(entityName, { max_relations: 100 });
        
        // Store in selected entity state for info panel
        setSelectedEntity({
          name: entityName,
          id: entityId,
          type: entityType,
          connections: connections,
        });
        
        setShowPapersList(true); // Expand papers list by default
      } catch (error) {
        console.error('Failed to fetch entity details:', error);
      }
    }
  }, []);

  // Handle edge click - show relation details
  const handleEdgeClick = useCallback((_event: React.MouseEvent, edge: any) => {
    console.log('[GraphView] Edge clicked:', edge);
    
    if (edge.data?.subject && edge.data?.predicate && edge.data?.object && edge.data?.sources) {
      setSelectedRelation({
        subject: edge.data.subject,
        predicate: edge.data.predicate,
        object: edge.data.object,
        sources: edge.data.sources,
      });
    }
  }, []);

  // Fetch graph statistics
  useEffect(() => {
    const fetchStats = async () => {
      try {
        setStatsLoading(true);
        setStatsError(null);
        const data = await getGraphStats();
        setStats(data);
      } catch (error) {
        console.error('Failed to fetch graph stats:', error);
        setStatsError('Failed to load statistics');
      } finally {
        setStatsLoading(false);
      }
    };

    fetchStats();
  }, []);

  // Handle navigation from PaperView "View in Graph" button
  useEffect(() => {
    const navState = location.state as { loadRelation?: {
      subjectId: string;
      subjectName: string;
      predicate: string;
      objectId: string;
      objectName: string;
    }} | null;
    
    if (!navState?.loadRelation) return;
    
    const { subjectId, subjectName, predicate, objectId, objectName } = navState.loadRelation;
    
    console.log('[GraphView] Loading relation from navigation:', {
      subject: subjectName,
      predicate,
      object: objectName
    });
    
    // Load both entities and filter to show only the specific predicate
    const loadRelationEntities = async () => {
      try {
        setEntitiesLoading(true);
        setEntitiesError(null);
        
        // Fetch connections for both entities
        const [subjectConnections, objectConnections] = await Promise.all([
          getEntityConnections(subjectName, { max_relations: 50 }),
          getEntityConnections(objectName, { max_relations: 50 })
        ]);
        
        console.log('[GraphView] Subject connections:', subjectConnections.outgoing.length + subjectConnections.incoming.length);
        console.log('[GraphView] Object connections:', objectConnections.outgoing.length + objectConnections.incoming.length);
        
        // Build entity map with just these two entities
        const entityMap = new Map<string, { name: string; id: string; connections: number }>();
        entityMap.set(subjectId, { name: subjectName, id: subjectId, connections: 1 });
        entityMap.set(objectId, { name: objectName, id: objectId, connections: 1 });
        
        // Find the specific edge with the matching predicate
        const edgeMap = new Map<string, any>();
        
        // Look for the relation in subject's outgoing connections
        subjectConnections.outgoing.forEach((relation: any) => {
          if (relation.object.id === objectId && relation.predicate === predicate) {
            const edgeId = `${subjectId}-${predicate}-${objectId}`;
            if (!edgeMap.has(edgeId)) {
              edgeMap.set(edgeId, {
                id: edgeId,
                source: subjectId,
                target: objectId,
                type: 'smoothstep',
                animated: false,
                style: { stroke: '#3b82f6', strokeWidth: 2 },
                label: predicate,
                labelStyle: { 
                  fill: '#1e293b', 
                  fontWeight: 600, 
                  fontSize: 11,
                },
                labelBgStyle: { 
                  fill: '#f1f5f9', 
                  fillOpacity: 0.9,
                },
                labelBgPadding: [4, 6] as [number, number],
                labelBgBorderRadius: 3,
                data: {
                  subject: subjectName,
                  predicate: predicate,
                  object: objectName,
                  sources: [{
                    relationId: relation.id,
                    paper: relation.source_paper,
                    section: relation.section,
                    pages: relation.pages || [],
                    confidence: relation.confidence,
                  }],
                },
              });
            }
          }
        });
        
        // Also check object's incoming connections (reverse direction)
        objectConnections.incoming.forEach((relation: any) => {
          if (relation.subject.id === subjectId && relation.predicate === predicate) {
            const edgeId = `${subjectId}-${predicate}-${objectId}`;
            if (!edgeMap.has(edgeId)) {
              edgeMap.set(edgeId, {
                id: edgeId,
                source: subjectId,
                target: objectId,
                type: 'smoothstep',
                animated: false,
                style: { stroke: '#3b82f6', strokeWidth: 2 },
                label: predicate,
                labelStyle: { 
                  fill: '#1e293b', 
                  fontWeight: 600, 
                  fontSize: 11,
                },
                labelBgStyle: { 
                  fill: '#f1f5f9', 
                  fillOpacity: 0.9,
                },
                labelBgPadding: [4, 6] as [number, number],
                labelBgBorderRadius: 3,
                data: {
                  subject: subjectName,
                  predicate: predicate,
                  object: objectName,
                  sources: [{
                    relationId: relation.id,
                    paper: relation.source_paper,
                    section: relation.section,
                    pages: relation.pages || [],
                    confidence: relation.confidence,
                  }],
                },
              });
            }
          }
        });
        
        const edgeList = Array.from(edgeMap.values());
        
        console.log('[GraphView] Created nodes:', entityMap.size);
        console.log('[GraphView] Created edges:', edgeList.length);
        
        // Create nodes and edges
        const nodes = createNodesFromEntities(Array.from(entityMap.values()));
        setNodes(nodes);
        setEdges(edgeList);
        
      } catch (err) {
        console.error('[GraphView] Failed to load relation:', err);
        setEntitiesError('Failed to load relation');
      } finally {
        setEntitiesLoading(false);
      }
    };
    
    loadRelationEntities();
    
    // Clear navigation state so it doesn't re-trigger
    window.history.replaceState({}, document.title);
  }, [location.state, createNodesFromEntities, setNodes, setEdges]);

  // Fetch most connected entities and their connections - DISABLED FOR EMPTY DEFAULT STATE
  /*
  useEffect(() => {
    const fetchEntitiesAndConnections = async () => {
      try {
        setEntitiesLoading(true);
        setEntitiesError(null);
        
        // Get most connected entities and filter for scientific relevance
        console.log('[GraphView] Fetching most connected entities...');
        const mostConnectedRaw = await getMostConnectedEntities({ limit: 50 });
        
        // Filter out non-scientific entities for demo purposes
        // This excludes: institutional names, citations, common words, and low-quality extractions
        // In production, improve entity extraction quality at the source instead of filtering here
        const excludeWords = [
          'department', 'school', 'university', 'et al.', 'figure', 'table', 'contents', 
          'sciencedirect', 'the study', 'part of', 'india', 'further', 'natural gas',
          'also', 'however', 'therefore', 'thus', 'moreover', 'furthermore'
        ];
        const scientificEntities = mostConnectedRaw.filter(item => {
          const name = item.entity.name.toLowerCase();
          const isShortEnough = item.entity.name.length < 60;
          const isNotExcluded = !excludeWords.some(word => name.includes(word));
          const hasLetters = /[a-z]/i.test(item.entity.name); // Has at least some letters
          return isShortEnough && isNotExcluded && hasLetters && item.total_connections >= 2;
        });
        
        // Take top 10-12 scientific entities for a focused, readable graph
        const topEntities = scientificEntities.slice(0, 12);
        console.log('[GraphView] Selected entities:', topEntities.map(e => `${e.entity.name} (${e.total_connections})`));
        
        if (topEntities.length === 0) {
          console.error('[GraphView] No valid entities found!');
          setEntitiesError('No entities found');
          setEntitiesLoading(false);
          return;
        }
        
        // Fetch connections for each entity (limiting to reduce visual clutter)
        console.log('[GraphView] Fetching connections for entities...');
        console.log('[GraphView] Note: Limiting to 20 connections per entity to keep graph readable.');
        const connectionsPromises = topEntities.map(async (item) => {
          try {
            const connections = await getEntityConnections(item.entity.name, { max_relations: 20 });
            
            // Filter out connections with missing data (backend data quality issue)
            const validOutgoing = connections.outgoing.filter(c => c.object?.name && c.predicate);
            const validIncoming = connections.incoming.filter(c => c.subject?.name && c.predicate);
            
            return {
              entity: item.entity,
              connections: {
                outgoing: validOutgoing,
                incoming: validIncoming,
              },
              total_connections: validOutgoing.length + validIncoming.length,
              outgoing_count: validOutgoing.length,
              incoming_count: validIncoming.length,
            };
          } catch (err) {
            // Silently handle entities with backend data quality issues (e.g., missing names in GraphQL)
            // For demo purposes, we simply exclude these entities rather than showing errors
            return null;
          }
        });
        
        const entitiesWithConnections = await Promise.all(connectionsPromises);
        const curatedData = entitiesWithConnections
          .filter((item): item is NonNullable<typeof item> => item !== null)
          .map((item: any) => ({
            entity: item.entity,
            total_connections: item.total_connections,
            outgoing_count: item.outgoing_count,
            incoming_count: item.incoming_count,
          }));
        
        console.log('[GraphView] Entities with connections:', curatedData.map((e: any) => `${e.entity.name} (${e.total_connections})`));
        
        // Extract just the connections for processing
        const allConnections = entitiesWithConnections
          .filter((item): item is NonNullable<typeof item> => item !== null)
          .map((item: any) => item.connections);
        
        // Build a map of all unique entities (hub entities + connected entities)
        const entityMap = new Map<string, { name: string; id: string; connections: number }>();
        
        // Add hub entities
        curatedData.forEach((item: any) => {
          entityMap.set(item.entity.id, {
            name: item.entity.name,
            id: item.entity.id,
            connections: item.total_connections,
          });
        });
        
        // Strategy: Show each hub entity's top connections to keep graph readable
        const edgeList: Edge[] = [];
        const edgeSet = new Set<string>(); // Track unique edges to prevent duplicates
        const MAX_CONNECTIONS_PER_ENTITY = 3; // Limit connections per hub to reduce clutter
        
        allConnections.forEach((connections: any, idx: number) => {
          const hubEntity = curatedData[idx].entity;
          let connectionCount = 0;
          
          // Process outgoing relations
          connections.outgoing.forEach((relation: any) => {
            if (!relation.object || connectionCount >= MAX_CONNECTIONS_PER_ENTITY) return;
            
            // Add connected entity if not already present
            if (!entityMap.has(relation.object.id)) {
              entityMap.set(relation.object.id, {
                name: relation.object.name,
                id: relation.object.id,
                connections: 1,
              });
            }
            
            const edgeId = `${hubEntity.id}-${relation.object.id}`;
            if (!edgeSet.has(edgeId)) {
              edgeSet.add(edgeId);
              edgeList.push({
                id: edgeId,
                source: hubEntity.id,
                target: relation.object.id,
                type: 'smoothstep', // Use smoothstep for better edge routing
                animated: false,
                style: { stroke: '#3b82f6', strokeWidth: 2 },
                label: relation.predicate,
                labelStyle: { 
                  fill: '#1e293b', 
                  fontWeight: 600, 
                  fontSize: 11,
                },
                labelBgStyle: { 
                  fill: '#f1f5f9', 
                  fillOpacity: 0.9,
                },
                labelBgPadding: [4, 6] as [number, number],
                labelBgBorderRadius: 3,
              });
              connectionCount++;
            }
          });
          
          // Process incoming relations
          connections.incoming.forEach((relation: any) => {
            if (!relation.subject || connectionCount >= MAX_CONNECTIONS_PER_ENTITY) return;
            
            // Add connected entity if not already present
            if (!entityMap.has(relation.subject.id)) {
              entityMap.set(relation.subject.id, {
                name: relation.subject.name,
                id: relation.subject.id,
                connections: 1,
              });
            }
            
            const edgeId = `${relation.subject.id}-${hubEntity.id}`;
            if (!edgeSet.has(edgeId)) {
              edgeSet.add(edgeId);
              edgeList.push({
                id: edgeId,
                source: relation.subject.id,
                target: hubEntity.id,
                type: 'smoothstep', // Use smoothstep for better edge routing
                animated: false,
                style: { stroke: '#3b82f6', strokeWidth: 2 },
                label: relation.predicate,
                labelStyle: { 
                  fill: '#1e293b', 
                  fontWeight: 600, 
                  fontSize: 11,
                },
                labelBgStyle: { 
                  fill: '#f1f5f9', 
                  fillOpacity: 0.9,
                },
                labelBgPadding: [4, 6] as [number, number],
                labelBgBorderRadius: 3,
              });
              connectionCount++;
            }
          });
        });
        
        // Convert entity map to array
        const allEntities = Array.from(entityMap.values());
        console.log('[GraphView] Total entities in graph:', allEntities.length);
        console.log('[GraphView] Total edges:', edgeList.length);
        
        // Create nodes with force-directed initial positions
        const flowNodes = createNodesFromEntities(allEntities);
        setNodes(flowNodes);
        setEdges(edgeList);
        
      } catch (error) {
        console.error('Failed to fetch entities:', error);
        setEntitiesError('Failed to load entities');
      } finally {
        setEntitiesLoading(false);
      }
    };

    fetchEntitiesAndConnections();
  }, [createNodesFromEntities, setNodes, setEdges]);
  */

  // Set initial loading state to false for empty graph
  useEffect(() => {
    setEntitiesLoading(false);
  }, []);

  return (
    <div className="h-full flex flex-col bg-gray-50 dark:bg-gray-900">
      {/* Top Toolbar */}
      <div className="border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-3">
        <div className="flex items-center justify-between gap-4">
          {/* Search Bar */}
          <div className="flex-1 max-w-md relative">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search entities..."
                value={searchQuery}
                onChange={(e) => handleSearchInput(e.target.value)}
                onFocus={() => searchResults.length > 0 && setShowSearchResults(true)}
                onBlur={() => setTimeout(() => setShowSearchResults(false), 200)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              {searchLoading && (
                <div className="absolute right-3 top-1/2 -translate-y-1/2">
                  <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                </div>
              )}
            </div>
            
            {/* Search Results Dropdown */}
            {showSearchResults && searchResults.length > 0 && (
              <div className="absolute top-full mt-1 w-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg max-h-96 overflow-y-auto z-50">
                {searchResults.map((result) => (
                  <button
                    key={result.id}
                    onClick={() => loadEntityAndConnections(result.name, result.id)}
                    className="w-full text-left px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-700 border-b border-gray-100 dark:border-gray-700 last:border-b-0 transition-colors"
                  >
                    <div className="font-medium text-gray-900 dark:text-white">{result.name}</div>
                    <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {result.type}
                      {result.namespace && ` • ${result.namespace}`}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Stats Display */}
          <div className="flex items-center gap-6 px-4 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg">
            <div className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-blue-500" />
              {statsLoading ? (
                <span className="text-sm text-gray-500 dark:text-gray-400">Loading...</span>
              ) : statsError ? (
                <span className="text-sm text-red-500">{statsError}</span>
              ) : stats ? (
                <>
                  <span className="text-sm text-gray-600 dark:text-gray-300">
                    <span className="font-semibold text-gray-900 dark:text-white">
                      {stats.total_nodes.toLocaleString()}
                    </span> entities
                  </span>
                </>
              ) : null}
            </div>
            {stats && !statsLoading && !statsError && (
              <>
                <div className="text-sm text-gray-600 dark:text-gray-300">
                  <span className="font-semibold text-gray-900 dark:text-white">
                    {stats.total_relations.toLocaleString()}
                  </span> relations
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-300">
                  <span className="font-semibold text-gray-900 dark:text-white">
                    {stats.total_papers}
                  </span> papers
                </div>
              </>
            )}
          </div>

          {/* Filter Controls */}
          <div className="flex items-center gap-2">
            <button 
              onClick={() => setShowInfoPanel(!showInfoPanel)}
              className={`p-2 rounded-lg transition-colors ${
                showInfoPanel 
                  ? 'bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-300' 
                  : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600'
              }`}
              title="Toggle info panel"
            >
              <Info className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Graph Canvas */}
        <div className="flex-1 relative">
          {entitiesLoading ? (
            <div className="absolute inset-0 flex items-center justify-center bg-white dark:bg-gray-800">
              <div className="text-center">
                <div className="mb-4 flex justify-center">
                  <div className="relative">
                    {/* Mock nodes with animation */}
                    <div className="absolute top-0 left-0 w-16 h-16 bg-blue-500 rounded-full opacity-50 animate-pulse" />
                    <div className="absolute top-8 right-0 w-12 h-12 bg-green-500 rounded-full opacity-50 animate-pulse delay-100" style={{ animationDelay: '0.1s' }} />
                    <div className="absolute bottom-0 left-8 w-14 h-14 bg-purple-500 rounded-full opacity-50 animate-pulse delay-200" style={{ animationDelay: '0.2s' }} />
                    <div className="w-32 h-32" />
                  </div>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                  Loading Graph...
                </h3>
                <p className="text-gray-600 dark:text-gray-400">
                  Fetching entities and building visualization
                </p>
              </div>
            </div>
          ) : entitiesError ? (
            <div className="absolute inset-0 flex items-center justify-center bg-white dark:bg-gray-800">
              <div className="text-center">
                <h3 className="text-lg font-semibold text-red-600 mb-2">
                  Error Loading Graph
                </h3>
                <p className="text-gray-600 dark:text-gray-400">{entitiesError}</p>
              </div>
            </div>
          ) : nodes.length === 0 ? (
            <div className="absolute inset-0 flex items-center justify-center bg-white dark:bg-gray-800">
              <div className="text-center max-w-md px-4">
                <div className="mb-6">
                  <Search className="w-16 h-16 mx-auto text-gray-300 dark:text-gray-600" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                  Search for an Entity to Begin
                </h3>
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  Use the search bar above to find entities and start exploring the knowledge graph. 
                  Click on nodes to view details and discover connections between entities.
                </p>
                <div className="text-sm text-gray-500 dark:text-gray-500">
                  Try searching for terms like "methane", "carbon", or "bacteria"
                </div>
              </div>
            </div>
          ) : (
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onNodeClick={handleNodeClick}
              onEdgeClick={handleEdgeClick}
              fitView
              elevateEdgesOnSelect={true}
              className="bg-gray-50 dark:bg-gray-900"
            >
              <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
              <Controls />
              <MiniMap 
                nodeColor={() => '#3b82f6'}
                className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700"
              />
            </ReactFlow>
          )}
        </div>

        {/* Info Panel Sidebar */}
        {showInfoPanel && (
          <div className="w-80 border-l border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 overflow-y-auto">
            <div className="p-4">

              {/* Entity Info Section */}
              <div className="mb-6">
                <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">
                  Entity Information
                </h3>
                {!selectedEntity ? (
                  <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600">
                    <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                      Click an entity node to view details
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {/* Entity Details */}
                    <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                      <div className="font-semibold text-gray-900 dark:text-white mb-1 text-lg">{selectedEntity.name}</div>
                      <div className="text-xs text-gray-600 dark:text-gray-400 mb-3">{selectedEntity.type}</div>
                      
                      {/* Connection Stats */}
                      <div className="flex items-center gap-4 text-xs mb-3">
                        <div>
                          <span className="text-gray-600 dark:text-gray-400">Total:</span>
                          <span className="ml-1 font-semibold text-gray-900 dark:text-white">
                            {selectedEntity.connections.outgoing.length + selectedEntity.connections.incoming.length}
                          </span>
                        </div>
                        <div>
                          <span className="text-gray-600 dark:text-gray-400">Out:</span>
                          <span className="ml-1 font-semibold text-green-600 dark:text-green-400">
                            {selectedEntity.connections.outgoing.length}
                          </span>
                        </div>
                        <div>
                          <span className="text-gray-600 dark:text-gray-400">In:</span>
                          <span className="ml-1 font-semibold text-purple-600 dark:text-purple-400">
                            {selectedEntity.connections.incoming.length}
                          </span>
                        </div>
                      </div>

                      <button 
                        onClick={() => loadEntityAndConnections(selectedEntity.name, selectedEntity.id)}
                        className="w-full px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded transition-colors"
                      >
                        Expand Connections
                      </button>
                    </div>

                    {/* Statistics */}
                    <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600">
                      <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">Statistics</h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-600 dark:text-gray-400">Appears in papers:</span>
                          <span className="font-semibold text-gray-900 dark:text-white">
                            {(() => {
                              const allRelations = [...selectedEntity.connections.outgoing, ...selectedEntity.connections.incoming];
                              const uniquePapers = new Set(allRelations.map(r => r.source_paper));
                              return uniquePapers.size;
                            })()}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600 dark:text-gray-400">Top relation:</span>
                          <span className="font-semibold text-gray-900 dark:text-white text-xs">
                            {(() => {
                              const allRelations = [...selectedEntity.connections.outgoing, ...selectedEntity.connections.incoming];
                              const predicateCounts = allRelations.reduce((acc, r) => {
                                acc[r.predicate] = (acc[r.predicate] || 0) + 1;
                                return acc;
                              }, {} as Record<string, number>);
                              const topPredicate = Object.entries(predicateCounts).sort((a, b) => (b[1] as number) - (a[1] as number))[0];
                              return topPredicate ? `"${topPredicate[0]}" (${topPredicate[1]})` : 'N/A';
                            })()}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Source Papers */}
                    <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="text-sm font-semibold text-gray-900 dark:text-white">Source Papers</h4>
                        <button
                          onClick={() => setShowPapersList(!showPapersList)}
                          className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
                        >
                          {showPapersList ? 'Collapse' : 'Expand'}
                        </button>
                      </div>
                      
                      {showPapersList && (
                        <div className="space-y-2">
                          {(() => {
                            const allRelations = [...selectedEntity.connections.outgoing, ...selectedEntity.connections.incoming];
                            const paperCounts = allRelations.reduce((acc, r) => {
                              acc[r.source_paper] = (acc[r.source_paper] || 0) + 1;
                              return acc;
                            }, {} as Record<string, number>);
                            
                            return Object.entries(paperCounts)
                              .sort((a, b) => (b[1] as number) - (a[1] as number))
                              .map(([paper, count]) => (
                                <button
                                  key={paper}
                                  onClick={() => {
                                    // Navigate to paper view with encoded filename
                                    navigate(`/papers/${encodeURIComponent(paper)}`);
                                  }}
                                  className="w-full text-left p-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors"
                                >
                                  <div className="text-xs font-medium text-gray-900 dark:text-white truncate">
                                    {paper}
                                  </div>
                                  <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                    {count as number} {(count as number) === 1 ? 'relation' : 'relations'}
                                  </div>
                                </button>
                              ));
                          })()}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Relation Info Section */}
              <div>
                <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">
                  Relation Details
                </h3>
                <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600">
                  {!selectedRelation ? (
                    <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                      Click a relation edge to view details
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {/* Relation Triple */}
                      <div className="flex items-center gap-2 flex-wrap">
                        <div className="px-3 py-1.5 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 text-sm rounded font-medium">
                          {selectedRelation.subject}
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400 font-medium px-2 py-1 bg-gray-100 dark:bg-gray-600 rounded">
                          {selectedRelation.predicate}
                        </div>
                        <div className="px-3 py-1.5 bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300 text-sm rounded font-medium">
                          {selectedRelation.object}
                        </div>
                      </div>

                      {/* Source Count */}
                      <div className="text-sm text-gray-700 dark:text-gray-300 font-medium">
                        This relation appears in {selectedRelation.sources.length} {selectedRelation.sources.length === 1 ? 'paper' : 'papers'}:
                      </div>

                      {/* Sources List */}
                      <div className="space-y-3">
                        {selectedRelation.sources.map((source, idx) => (
                          <div 
                            key={idx}
                            className="p-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg"
                          >
                            <div className="text-xs font-semibold text-gray-900 dark:text-white mb-2 break-words">
                              {source.paper}
                            </div>
                            <div className="space-y-1 mb-3">
                              <div className="text-xs text-gray-600 dark:text-gray-400">
                                <span className="font-semibold">Section:</span> {source.section || 'Not specified'}
                              </div>
                              <div className="text-xs text-gray-600 dark:text-gray-400">
                                <span className="font-semibold">Pages:</span> {source.pages && source.pages.length > 0 ? source.pages.join(', ') : 'Not specified'}
                              </div>
                              {source.confidence !== undefined && (
                                <div className="text-xs text-gray-600 dark:text-gray-400">
                                  <span className="font-semibold">Confidence:</span> {(source.confidence * 100).toFixed(1)}%
                                </div>
                              )}
                            </div>
                            <button
                              onClick={() => {
                                console.log('[GraphView] Navigating to paper:', source.paper);
                                console.log('[GraphView] Relation data:', {
                                  pages: source.pages,
                                  section: source.section,
                                  subject: selectedRelation.subject,
                                  predicate: selectedRelation.predicate,
                                  object: selectedRelation.object
                                });
                                
                                // Navigate with state to highlight the relation in the paper
                                navigate(`/papers/${encodeURIComponent(source.paper)}`, {
                                  state: {
                                    highlightRelation: {
                                      pages: source.pages,
                                      section: source.section,
                                      subject: selectedRelation.subject,
                                      predicate: selectedRelation.predicate,
                                      object: selectedRelation.object
                                    }
                                  }
                                });
                              }}
                              className="w-full px-3 py-2 bg-green-600 hover:bg-green-700 text-white text-xs rounded transition-colors font-medium"
                            >
                              View in Paper
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
