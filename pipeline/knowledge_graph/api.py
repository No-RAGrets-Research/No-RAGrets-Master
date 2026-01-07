#!/usr/bin/env python3
"""
Knowledge Graph REST API
========================
Comprehensive FastAPI application providing search, traversal, provenance, and analytics
endpoints for the knowledge graph database.
"""

from fastapi import FastAPI, HTTPException, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict
import uvicorn
from datetime import datetime
import json
import socket
import socket
import os

from dgraph_manager import DgraphManager
from query_builder import GraphQLQueryBuilder

# LLM Review System imports
from llm_review.utils.text_loader import load_paper_text
from llm_review.utils.llm_runner import run_llm
from llm_review.utils.result_merger import merge_rubric_outputs, synthesize_review

# Initialize FastAPI app
app = FastAPI(
    title="Knowledge Graph API",
    description="REST API for querying and analyzing extracted knowledge graphs",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for web applications
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
dgraph = DgraphManager()
query_builder = GraphQLQueryBuilder()

# Utility functions for port management
def is_port_in_use(port: int) -> bool:
    """Check if a port is currently in use."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', port))
            return False
    except OSError:
        return True

def find_available_port(start_port=8001, max_attempts=10):
    """Find an available port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        if not is_port_in_use(port):
            return port
    raise RuntimeError(f"No available ports found in range {start_port}-{start_port + max_attempts}")

def get_optimal_configuration():
    """Get optimal port configuration avoiding conflicts."""
    # Check if something is running on common ports
    if is_port_in_use(8000):
        print("🔍 Port 8000 in use (likely Dgraph Ratel or other service)")
    if is_port_in_use(8080):
        print("🔍 Port 8080 in use (likely Dgraph HTTP)")
    
    # Find available port for API, preferring 8001 if 8000 is taken
    start_port = 8001 if is_port_in_use(8000) else 8000
    api_port = find_available_port(start_port)
    return api_port

# Pydantic models for API responses
class NodeResponse(BaseModel):
    id: str
    name: str
    type: Optional[str] = None
    namespace: Optional[str] = None
    created_at: Optional[str] = None

class RelationResponse(BaseModel):
    id: str
    predicate: str
    subject: NodeResponse
    object: NodeResponse
    section: Optional[str] = None
    pages: Optional[List[int]] = None
    source_paper: Optional[str] = None
    confidence: Optional[float] = None
    figure_id: Optional[str] = None  # e.g., "page6_fig1"
    table_id: Optional[str] = None  # e.g., "page5_table2"

class PaperResponse(BaseModel):
    id: str
    title: str
    filename: str
    processed_at: Optional[str] = None
    total_entities: Optional[int] = None
    total_relations: Optional[int] = None
    sections: Optional[List[str]] = None

class ProvenanceResponse(BaseModel):
    relation_id: str
    section: Optional[str] = None
    pages: Optional[List[int]] = None
    #bbox_data: Optional[Dict] = None
    bbox_data: Optional[Union[Dict[str, Any], List[Any]]] = None
    source_paper: Optional[str] = None
    extraction_method: Optional[str] = None

class EntityPosition(BaseModel):
    start: int
    end: int
    sentence_id: int
    matched_text: str

class DocumentOffsets(BaseModel):
    start: int
    end: int

class SourceSpanLocation(BaseModel):
    chunk_id: int
    sentence_range: List[int]  # [start_sentence, end_sentence]
    document_offsets: DocumentOffsets

class SourceSpanResponse(BaseModel):
    span_type: str  # "single_sentence", "multi_sentence", "cross_chunk", "chunk_fallback"
    text_evidence: str
    confidence: float
    location: SourceSpanLocation
    subject_positions: Optional[List[EntityPosition]] = None
    object_positions: Optional[List[EntityPosition]] = None
    docling_ref: Optional[str] = None  # Reference to Docling JSON element (e.g., "#/texts/66")

class RelationSourceSpanResponse(BaseModel):
    relation_id: str
    subject: str
    predicate: str
    object: str
    source_span: Optional[SourceSpanResponse] = None

class BatchSourceSpanMetadata(BaseModel):
    requested: int
    found: int
    not_found: List[str]
    processing_time_ms: float

class BatchSourceSpanResponse(BaseModel):
    results: List[RelationSourceSpanResponse]
    metadata: BatchSourceSpanMetadata

class GraphStatsResponse(BaseModel):
    total_nodes: int
    total_relations: int
    total_papers: int
    unique_predicates: int
    most_connected_entities: List[Dict[str, Any]]

class ReviewRequest(BaseModel):
    """Request model for paper review endpoint."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "pdf_filename": "A. Priyadarsini et al. 2023.pdf"
            }
        }
    )
    
    text: Optional[str] = Field(None, description="Direct paper text input")
    pdf_filename: Optional[str] = Field(None, description="PDF filename in papers/ directory")

# ==========================================
# 1. SEARCH & DISCOVERY ENDPOINTS
# ==========================================

@app.get("/api/entities/search", response_model=List[NodeResponse])
async def search_entities(
    q: str = Query(..., description="Search query for entity names"),
    type_filter: Optional[str] = Query(None, alias="type", description="Filter by entity type"),
    namespace: Optional[str] = Query(None, description="Filter by namespace"),
    limit: int = Query(20, description="Maximum number of results")
):
    """Search for entities by name, type, or namespace."""
    try:
        query = query_builder.build_entity_search(q, type_filter, namespace, limit)
        response = dgraph.query(query["query"], query["variables"])
        
        if "errors" in response:
            raise HTTPException(status_code=500, detail=response["errors"])
        
        nodes = response.get("data", {}).get("queryNode", [])
        return [NodeResponse(**node) for node in nodes]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/relations/search", response_model=List[RelationResponse])
async def search_relations(
    predicate: Optional[str] = Query(None, description="Search by predicate/relationship type"),
    subject: Optional[str] = Query(None, description="Search by subject entity name"),
    object: Optional[str] = Query(None, description="Search by object entity name"),
    section: Optional[str] = Query(None, description="Filter by document section"),
    limit: int = Query(20, description="Maximum number of results")
):
    """Search for relationships by predicate, entities, or document section."""
    try:
        query = query_builder.build_relation_search(predicate, subject, object, section, limit)
        response = dgraph.query(query["query"], query["variables"])
        
        if "errors" in response:
            raise HTTPException(status_code=500, detail=response["errors"])
        
        relations = response.get("data", {}).get("queryRelation", [])
        return [RelationResponse(**rel) for rel in relations]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/relations/by-text", response_model=List[RelationResponse])
async def search_relations_by_text(
    q: str = Query(..., description="Text to search for in relation source spans"),
    limit: int = Query(50, description="Maximum number of results")
):
    """Search for relations by their source text evidence.
    
    Find relations where the extracted sentence/text contains the query string.
    Useful for finding what relations came from specific sentences or paragraphs.
    """
    try:
        # Query all relations and filter in-memory for source_span text
        # Note: This could be optimized with full-text search indexing in the future
        query = """
        {
            queryRelation(first: 10000) {
                id
                subject { id name type namespace }
                predicate
                object { id name type namespace }
                source_paper
                section
                pages
                confidence
                source_span
            }
        }
        """
        
        response = dgraph.query(query)
        
        if "errors" in response:
            raise HTTPException(status_code=500, detail=response["errors"])
        
        all_relations = response.get("data", {}).get("queryRelation", [])
        
        # Filter by text evidence
        matching_relations = []
        query_lower = q.lower()
        
        for rel in all_relations:
            if rel.get("source_span"):
                try:
                    span_data = json.loads(rel["source_span"])
                    text_evidence = span_data.get("text_evidence", "")
                    if query_lower in text_evidence.lower():
                        matching_relations.append(rel)
                        if len(matching_relations) >= limit:
                            break
                except (json.JSONDecodeError, TypeError):
                    continue
        
        return [RelationResponse(**rel) for rel in matching_relations]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/relations/by-location", response_model=List[RelationResponse])
async def search_relations_by_location(
    paper_id: str = Query(..., description="Paper filename or ID"),
    section: Optional[str] = Query(None, description="Document section name"),
    page: Optional[int] = Query(None, description="Page number"),
    limit: int = Query(100, description="Maximum number of results")
):
    """Get all relations from a specific location in a paper.
    
    Filter by paper, section, and/or page to find what relations were extracted
    from a specific part of a document.
    """
    try:
        # Build filter conditions
        filters = [f'source_paper: {{ eq: "{paper_id}" }}']
        
        if section:
            filters.append(f'section: {{ anyofterms: "{section}" }}')
        
        filter_str = ", ".join(filters)
        
        query = f"""
        {{
            queryRelation(filter: {{ {filter_str} }}, first: 1000) {{
                id
                subject {{ id name type namespace }}
                predicate
                object {{ id name type namespace }}
                source_paper
                section
                pages
                confidence
            }}
        }}
        """
        
        response = dgraph.query(query)
        
        if "errors" in response:
            raise HTTPException(status_code=500, detail=response["errors"])
        
        relations = response.get("data", {}).get("queryRelation", [])
        
        # Filter by page if specified (post-processing since pages is an array)
        if page is not None:
            relations = [rel for rel in relations if rel.get("pages") and page in rel["pages"]]
        
        # Apply limit
        relations = relations[:limit]
        
        return [RelationResponse(**rel) for rel in relations]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/relations/by-chunk", response_model=List[RelationResponse])
async def search_relations_by_chunk(
    paper_id: str = Query(..., description="Paper filename or ID"),
    chunk_id: int = Query(..., description="Chunk ID from document processing"),
    limit: int = Query(100, description="Maximum number of results")
):
    """Get all relations extracted from a specific text chunk.
    
    Use the chunk_id from the source_span data to find all relations from
    a specific chunk of the document.
    """
    try:
        # Query relations from this paper
        query = f"""
        {{
            queryRelation(filter: {{ source_paper: {{ eq: "{paper_id}" }} }}, first: 10000) {{
                id
                subject {{ id name type namespace }}
                predicate
                object {{ id name type namespace }}
                source_paper
                section
                pages
                confidence
                source_span
            }}
        }}
        """
        
        response = dgraph.query(query)
        
        if "errors" in response:
            raise HTTPException(status_code=500, detail=response["errors"])
        
        all_relations = response.get("data", {}).get("queryRelation", [])
        
        # Filter by chunk_id in source_span
        matching_relations = []
        
        for rel in all_relations:
            if rel.get("source_span"):
                try:
                    span_data = json.loads(rel["source_span"])
                    if span_data.get("chunk_id") == chunk_id:
                        matching_relations.append(rel)
                        if len(matching_relations) >= limit:
                            break
                except (json.JSONDecodeError, TypeError):
                    continue
        
        return [RelationResponse(**rel) for rel in matching_relations]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/relations/by-figure", response_model=List[RelationResponse])
async def search_relations_by_figure(
    paper_id: str = Query(..., description="Paper filename or ID"),
    figure_id: str = Query(..., description="Figure ID (e.g., 'page6_fig1')"),
    limit: int = Query(100, description="Maximum number of results")
):
    """Get all relations extracted from a specific figure.
    
    Find relations that were extracted from a specific figure or chart
    by matching the figure_id field.
    
    Examples:
    - figure_id="page6_fig1"
    - figure_id="page3_fig2"
    """
    try:
        # Query relations from this paper with matching figure_id
        query = f"""
        {{
            queryRelation(filter: {{ 
                source_paper: {{ eq: "{paper_id}" }},
                figure_id: {{ anyofterms: "{figure_id}" }}
            }}, first: {limit}) {{
                id
                subject {{ id name type namespace }}
                predicate
                object {{ id name type namespace }}
                source_paper
                section
                pages
                confidence
                figure_id
                table_id
                source_span
            }}
        }}
        """
        
        response = dgraph.query(query)
        
        if "errors" in response:
            raise HTTPException(status_code=500, detail=response["errors"])
        
        relations = response.get("data", {}).get("queryRelation", [])
        
        return [RelationResponse(**rel) for rel in relations]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/relations/by-table", response_model=List[RelationResponse])
async def search_relations_by_table(
    paper_id: str = Query(..., description="Paper filename or ID"),
    table_id: str = Query(..., description="Table ID (e.g., 'page5_table2')"),
    limit: int = Query(100, description="Maximum number of results")
):
    """Get all relations extracted from a specific table.
    
    Find relations that were extracted from a specific table
    by matching the table_id field.
    
    Examples:
    - table_id="page5_table2"
    - table_id="page7_table1"
    """
    try:
        # Query relations from this paper with matching table_id
        query = f"""
        {{
            queryRelation(filter: {{ 
                source_paper: {{ eq: "{paper_id}" }},
                table_id: {{ anyofterms: "{table_id}" }}
            }}, first: {limit}) {{
                id
                subject {{ id name type namespace }}
                predicate
                object {{ id name type namespace }}
                source_paper
                section
                pages
                confidence
                figure_id
                table_id
                source_span
            }}
        }}
        """
        
        response = dgraph.query(query)
        
        if "errors" in response:
            raise HTTPException(status_code=500, detail=response["errors"])
        
        relations = response.get("data", {}).get("queryRelation", [])
        
        return [RelationResponse(**rel) for rel in relations]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# 2. GRAPH TRAVERSAL ENDPOINTS
# ==========================================

@app.get("/api/entities/{entity_name}/connections", response_model=Dict[str, List[RelationResponse]])
async def get_entity_connections(
    entity_name: str = Path(..., description="Entity name to explore"),
    direction: str = Query("both", pattern="^(incoming|outgoing|both)$", description="Direction of relationships"),
    max_relations: int = Query(50, description="Maximum relations to return")
):
    """Get all relationships for a specific entity."""
    try:
        query = query_builder.build_entity_connections(entity_name, direction, max_relations)
        response = dgraph.query(query["query"], query["variables"])
        
        # Check for GraphQL errors but don't fail - we may have partial data
        has_errors = "errors" in response
        
        nodes = response.get("data", {}).get("queryNode", [])
        if not nodes:
            raise HTTPException(status_code=404, detail=f"Entity '{entity_name}' not found")
        
        node = nodes[0]
        result = {}
        
        # Filter out null/malformed relations
        if direction in ["outgoing", "both"]:
            outgoing = node.get("outgoing", [])
            # Filter out None values and relations missing required fields
            valid_outgoing = [
                rel for rel in outgoing 
                if rel is not None and rel.get("predicate") and rel.get("subject") and rel.get("object")
            ]
            result["outgoing"] = [RelationResponse(**rel) for rel in valid_outgoing]
        
        if direction in ["incoming", "both"]:
            incoming = node.get("incoming", [])
            # Filter out None values and relations missing required fields
            valid_incoming = [
                rel for rel in incoming 
                if rel is not None and rel.get("predicate") and rel.get("subject") and rel.get("object")
            ]
            result["incoming"] = [RelationResponse(**rel) for rel in valid_incoming]
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/entities/{entity_name}/path-to/{target_entity}")
async def find_path_between_entities(
    entity_name: str = Path(..., description="Source entity"),
    target_entity: str = Path(..., description="Target entity"),
    max_depth: int = Query(3, description="Maximum path length to search")
):
    """Find connection paths between two entities."""
    try:
        query = query_builder.build_path_query(entity_name, target_entity, max_depth)
        response = dgraph.query(query["query"], query["variables"])
        
        if "errors" in response:
            raise HTTPException(status_code=500, detail=response["errors"])
        
        # Process path results (this would need custom path-finding logic)
        return {"message": "Path finding endpoint - implementation depends on specific path algorithm"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# 3. DOCUMENT/PROVENANCE ENDPOINTS
# ==========================================

@app.get("/api/papers", response_model=List[PaperResponse])
async def list_papers():
    """Get list of all papers in the knowledge graph."""
    try:
        query = query_builder.build_papers_list()
        response = dgraph.query(query["query"], query["variables"])
        
        if "errors" in response:
            raise HTTPException(status_code=500, detail=response["errors"])
        
        papers = response.get("data", {}).get("queryPaper", [])
        return [PaperResponse(**paper) for paper in papers]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/papers/search")
async def search_papers(
    q: str = Query(..., description="Search query for paper titles or filenames"),
    limit: int = Query(10, description="Maximum number of results")
):
    """Search papers by title or filename."""
    try:
        # Use GraphQL fulltext search on title field
        query = f"""
        query {{
          queryPaper(filter: {{ title: {{ anyoftext: "{q}" }} }}, first: {limit}) {{
            id
            title
            filename
            processed_at
            total_entities
            total_relations
            sections
          }}
        }}
        """
        
        response = dgraph.query(query)
        if "errors" in response:
            raise HTTPException(status_code=500, detail=response["errors"])
        
        papers = response.get("data", {}).get("queryPaper", [])
        return [PaperResponse(**paper) for paper in papers]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/papers/{paper_id}/relations", response_model=List[RelationResponse])
async def get_paper_relations(
    paper_id: str = Path(..., description="Paper ID (source_paper field)"),
    section: Optional[str] = Query(None, description="Filter by document section"),
    limit: int = Query(1000, description="Maximum number of relations")
):
    """Get all relations extracted from a specific paper."""
    try:
        # Build filter for section if provided
        section_filter = f', section: {{ anyofterms: "{section}" }}' if section else ""
        
        query = f"""
        query {{
          queryRelation(filter: {{ source_paper: {{ eq: "{paper_id}" }}{section_filter} }}, first: {limit}) {{
            id
            predicate
            section
            pages
            source_paper
            confidence
            subject {{ id name type namespace }}
            object {{ id name type namespace }}
          }}
        }}
        """
        
        response = dgraph.query(query)
        if "errors" in response:
            raise HTTPException(status_code=500, detail=response["errors"])
        
        relations = response.get("data", {}).get("queryRelation", [])
        return [RelationResponse(**rel) for rel in relations]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/papers/{paper_id}/entities", response_model=List[NodeResponse])
async def get_paper_entities(
    paper_id: str = Path(..., description="Paper ID"),
    section: Optional[str] = Query(None, description="Filter by document section"),
    limit: int = Query(100, description="Maximum number of entities")
):
    """Get entities extracted from a specific paper, optionally filtered by section."""
    try:
        query = query_builder.build_paper_entities(paper_id, section, limit)
        response = dgraph.query(query["query"], query["variables"])
        
        if "errors" in response:
            raise HTTPException(status_code=500, detail=response["errors"])
        
        # Extract entities from relations (since entities are connected via relations)
        relations = response.get("data", {}).get("queryRelation", [])
        entities = {}
        
        for rel in relations:
            if rel.get("subject"):
                entities[rel["subject"]["id"]] = rel["subject"]
            if rel.get("object"):
                entities[rel["object"]["id"]] = rel["object"]
        
        return [NodeResponse(**entity) for entity in entities.values()]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class DeletePaperResponse(BaseModel):
    message: str
    paper_id: str
    filename: str
    relations_deleted: int


@app.delete("/api/papers/{paper_id}", response_model=DeletePaperResponse)
async def delete_paper(
    paper_id: str = Path(..., description="Paper UID (e.g., '0xa82e')")
):
    """
    Delete a paper and all its associated relations from the knowledge graph.
    
    This is a destructive operation that:
    1. Finds all relations where this paper is the source
    2. Deletes all those relations
    3. Deletes the paper itself
    
    Use with caution - this cannot be undone.
    """
    try:
        import requests
        
        # Step 1: Get paper info first
        info_query = f'''
        {{
          paper(func: uid({paper_id})) {{
            uid
            filename
            title
          }}
        }}
        '''
        
        info_response = requests.post(
            "http://localhost:8080/query",
            data=info_query,
            headers={"Content-Type": "application/dql"}
        )
        info_result = info_response.json()
        papers = info_result.get('paper', [])
        
        if not papers:
            raise HTTPException(
                status_code=404,
                detail=f"Paper with UID '{paper_id}' not found"
            )
        
        paper_info = papers[0]
        filename = paper_info.get('filename', 'unknown')
        
        # Step 2: Get all relations for this paper
        relations_query = f'''
        {{
          relations(func: uid({paper_id})) {{
            ~source_paper {{
              uid
            }}
          }}
        }}
        '''
        
        relations_response = requests.post(
            "http://localhost:8080/query",
            data=relations_query,
            headers={"Content-Type": "application/dql"}
        )
        relations_result = relations_response.json()
        
        relations_count = 0
        relations_data = relations_result.get('relations', [])
        
        if relations_data and relations_data[0].get('~source_paper'):
            relation_uids = [r['uid'] for r in relations_data[0]['~source_paper']]
            relations_count = len(relation_uids)
            
            # Delete all relations
            for rel_uid in relation_uids:
                mutation = [{"uid": rel_uid}]
                requests.post(
                    "http://localhost:8080/mutate?commitNow=true",
                    json={"delete": mutation},
                    headers={"Content-Type": "application/json"}
                )
        
        # Step 3: Delete the paper itself
        paper_mutation = [{"uid": paper_id}]
        requests.post(
            "http://localhost:8080/mutate?commitNow=true",
            json={"delete": paper_mutation},
            headers={"Content-Type": "application/json"}
        )
        
        return DeletePaperResponse(
            message=f"Successfully deleted paper and {relations_count} associated relations",
            paper_id=paper_id,
            filename=filename,
            relations_deleted=relations_count
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# @app.get("/api/relations/{relation_id}/provenance", response_model=ProvenanceResponse)
# async def get_relation_provenance(
#     relation_id: str = Path(..., description="Relation ID")
# ):
#     """Get detailed provenance information for a specific relationship."""
#     try:
#         query = query_builder.build_relation_provenance(relation_id)
#         response = dgraph.query(query["query"], query["variables"])
        
#         if "errors" in response:
#             raise HTTPException(status_code=500, detail=response["errors"])
        
#         relations = response.get("data", {}).get("queryRelation", [])
#         if not relations:
#             raise HTTPException(status_code=404, detail=f"Relation '{relation_id}' not found")
        
#         rel = relations[0]
#         bbox_data = None
#         if rel.get("bbox_data"):
#             try:
#                 bbox_data = json.loads(rel["bbox_data"])
#             except json.JSONDecodeError:
#                 bbox_data = {"raw": rel["bbox_data"]}
        
#         return ProvenanceResponse(
#             relation_id=rel["id"],
#             section=rel.get("section"),
#             pages=rel.get("pages"),
#             bbox_data=bbox_data,
#             source_paper=rel.get("source_paper"),
#             extraction_method=rel.get("extraction_method")
#         )
    
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/relations/{relation_id}/provenance", response_model=ProvenanceResponse)
async def get_relation_provenance(
    relation_id: str = Path(..., description="Relation ID")
):
    """Get detailed provenance for a relation by UID."""
    try:
        # Fetch all relations
        query = query_builder.build_relation_provenance()
        response = dgraph.query(query["query"])

        if "errors" in response:
            raise HTTPException(status_code=500, detail=response["errors"])

        relations = response.get("data", {}).get("queryRelation", [])

        # Filter in Python by UID (id == "0x5")
        rel = next((r for r in relations if r.get("id") == relation_id), None)

        if not rel:
            raise HTTPException(status_code=404, detail=f"Relation '{relation_id}' not found")

        bbox_data_raw = rel.get("bbox_data")

        bbox_data = None
        if bbox_data_raw:
            try:
                parsed = json.loads(bbox_data_raw)
                # Allow list OR dict
                if isinstance(parsed, (dict, list)):
                    bbox_data = parsed
                else:
                    bbox_data = {"raw": parsed}
            except Exception:
                bbox_data = {"raw": bbox_data_raw}


        return ProvenanceResponse(
            relation_id=rel["id"],
            section=rel.get("section"),
            pages=rel.get("pages"),
            bbox_data=bbox_data,
            source_paper=rel.get("source_paper"),
            extraction_method=rel.get("extraction_method")
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/relations/{relation_id}/source-span", response_model=RelationSourceSpanResponse)
async def get_relation_source_span(
    relation_id: str = Path(..., description="Relation ID")
):
    """Get the exact text span where this relation was extracted from."""
    try:
        # First try to get the relation directly (this approach may need improvement)
        # For now, let's get all relations and filter by ID in memory
        query = """
        {
            queryRelation {
                id
                subject { name }
                predicate
                object { name }
                source_span
                confidence
            }
        }
        """
        
        response = dgraph.query(query)
        
        if "errors" in response:
            raise HTTPException(status_code=500, detail=response["errors"])
        
        relations = response.get("data", {}).get("queryRelation", [])
        
        # Filter by ID in memory since ID filtering in GraphQL doesn't seem to work
        matching_relations = [r for r in relations if r.get("id") == relation_id]
        if not matching_relations:
            raise HTTPException(status_code=404, detail=f"Relation '{relation_id}' not found")
        
        relation = matching_relations[0]
        subject_name = relation.get("subject", {}).get("name", "")
        object_name = relation.get("object", {}).get("name", "")
        predicate = relation.get("predicate", "")
        
        # Parse source span data if available
        source_span_data = None
        if relation.get("source_span"):
            try:
                span_json = json.loads(relation["source_span"])
                
                # Parse entity positions if available
                subject_positions = []
                if span_json.get("subject_positions"):
                    subject_positions = [
                        EntityPosition(**pos) for pos in span_json["subject_positions"]
                    ]
                
                object_positions = []
                if span_json.get("object_positions"):
                    object_positions = [
                        EntityPosition(**pos) for pos in span_json["object_positions"]
                    ]
                
                # Create document offsets
                doc_offsets = span_json.get("document_offsets", {})
                document_offsets = DocumentOffsets(
                    start=doc_offsets.get("start", 0),
                    end=doc_offsets.get("end", 0)
                )
                
                # Create location info
                location = SourceSpanLocation(
                    chunk_id=span_json.get("chunk_id", 0),
                    sentence_range=[
                        span_json.get("sentence_start", 0),
                        span_json.get("sentence_end", 0)
                    ],
                    document_offsets=document_offsets
                )
                
                # Extract docling_ref if available
                docling_ref = span_json.get("docling_ref")
                
                source_span_data = SourceSpanResponse(
                    span_type=span_json.get("span_type", "unknown"),
                    text_evidence=span_json.get("text_evidence", ""),
                    confidence=span_json.get("confidence", 0.0),
                    location=location,
                    subject_positions=subject_positions if subject_positions else None,
                    object_positions=object_positions if object_positions else None,
                    docling_ref=docling_ref
                )
                
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                # If span data is malformed, still return the relation without span info
                print(f"Warning: Could not parse source span for relation {relation_id}: {e}")
        
        return RelationSourceSpanResponse(
            relation_id=relation_id,
            subject=subject_name,
            predicate=predicate,
            object=object_name,
            source_span=source_span_data
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/relations/source-spans", response_model=BatchSourceSpanResponse)
async def get_batch_source_spans(
    ids: str = Query(..., description="Comma-separated list of relation IDs")
):
    """Get source spans for multiple relations in a single request.
    
    Example: /api/relations/source-spans?ids=0x5,0x6,0x7
    
    Maximum 500 IDs per request.
    """
    import time
    start_time = time.time()
    
    try:
        # Parse and validate input
        relation_ids = [rid.strip() for rid in ids.split(',') if rid.strip()]
        
        if not relation_ids:
            raise HTTPException(status_code=400, detail="ids parameter is required and must not be empty")
        
        if len(relation_ids) > 500:
            raise HTTPException(status_code=400, detail=f"Maximum 500 IDs per request, received {len(relation_ids)}")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_ids = []
        for rid in relation_ids:
            if rid not in seen:
                seen.add(rid)
                unique_ids.append(rid)
        
        # Build GraphQL query with ID filter
        ids_filter = ", ".join([f'"{rid}"' for rid in unique_ids])
        query = f"""
        {{
            queryRelation(filter: {{ id: [{ids_filter}] }}) {{
                id
                subject {{ name }}
                predicate
                object {{ name }}
                source_span
                confidence
            }}
        }}
        """
        
        response = dgraph.query(query)
        
        if "errors" in response:
            raise HTTPException(status_code=500, detail=response["errors"])
        
        relations = response.get("data", {}).get("queryRelation", [])
        
        # Build results list
        results = []
        found_ids = set()
        
        for relation in relations:
            relation_id = relation.get("id")
            if not relation_id:
                continue
            
            found_ids.add(relation_id)
            subject_name = relation.get("subject", {}).get("name", "")
            object_name = relation.get("object", {}).get("name", "")
            predicate = relation.get("predicate", "")
            
            # Parse source span data if available
            source_span_data = None
            if relation.get("source_span"):
                try:
                    span_json = json.loads(relation["source_span"])
                    
                    # Parse entity positions
                    subject_positions = []
                    if span_json.get("subject_positions"):
                        subject_positions = [
                            EntityPosition(**pos) for pos in span_json["subject_positions"]
                        ]
                    
                    object_positions = []
                    if span_json.get("object_positions"):
                        object_positions = [
                            EntityPosition(**pos) for pos in span_json["object_positions"]
                        ]
                    
                    # Create document offsets
                    doc_offsets = span_json.get("document_offsets", {})
                    document_offsets = DocumentOffsets(
                        start=doc_offsets.get("start", 0),
                        end=doc_offsets.get("end", 0)
                    )
                    
                    # Create location info
                    location = SourceSpanLocation(
                        chunk_id=span_json.get("chunk_id", 0),
                        sentence_range=[
                            span_json.get("sentence_start", 0),
                            span_json.get("sentence_end", 0)
                        ],
                        document_offsets=document_offsets
                    )
                    
                    # Extract docling_ref if available
                    docling_ref = span_json.get("docling_ref")
                    
                    source_span_data = SourceSpanResponse(
                        span_type=span_json.get("span_type", "unknown"),
                        text_evidence=span_json.get("text_evidence", ""),
                        confidence=span_json.get("confidence", 0.0),
                        location=location,
                        subject_positions=subject_positions if subject_positions else None,
                        object_positions=object_positions if object_positions else None,
                        docling_ref=docling_ref
                    )
                    
                except (json.JSONDecodeError, KeyError, TypeError) as e:
                    print(f"Warning: Could not parse source span for relation {relation_id}: {e}")
            
            results.append(RelationSourceSpanResponse(
                relation_id=relation_id,
                subject=subject_name,
                predicate=predicate,
                object=object_name,
                source_span=source_span_data
            ))
        
        # Calculate not found IDs
        not_found = [rid for rid in unique_ids if rid not in found_ids]
        
        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Build metadata
        metadata = BatchSourceSpanMetadata(
            requested=len(unique_ids),
            found=len(found_ids),
            not_found=not_found,
            processing_time_ms=round(processing_time_ms, 2)
        )
        
        return BatchSourceSpanResponse(
            results=results,
            metadata=metadata
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# 4. ANALYTICS ENDPOINTS
# ==========================================

@app.get("/api/graph/stats", response_model=GraphStatsResponse)
async def get_graph_statistics():
    """Get comprehensive statistics about the knowledge graph."""
    try:
        query = query_builder.build_graph_stats()
        response = dgraph.query(query["query"], query["variables"])
        
        if "errors" in response:
            raise HTTPException(status_code=500, detail=response["errors"])
        
        data = response.get("data", {})
        
        # Extract statistics from aggregation queries
        stats = GraphStatsResponse(
            total_nodes=len(data.get("allNodes", [])),
            total_relations=len(data.get("allRelations", [])),
            total_papers=len(data.get("allPapers", [])),
            unique_predicates=len(set(rel.get("predicate", "") for rel in data.get("allRelations", []))),
            most_connected_entities=[]  # Would need additional query for top connected entities
        )
        
        return stats
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/entities/most-connected")
async def get_most_connected_entities(
    limit: int = Query(10, description="Number of top entities to return")
):
    """Get entities with the most relationships."""
    try:
        query = query_builder.build_most_connected_entities(limit)
        response = dgraph.query(query["query"], query["variables"])
        
        if "errors" in response:
            raise HTTPException(status_code=500, detail=response["errors"])
        
        nodes = response.get("data", {}).get("queryNode", [])
        
        # Calculate connection counts and sort
        entity_counts = []
        for node in nodes:
            total_connections = len(node.get("outgoing", [])) + len(node.get("incoming", []))
            entity_counts.append({
                "entity": NodeResponse(**node),
                "total_connections": total_connections,
                "outgoing_count": len(node.get("outgoing", [])),
                "incoming_count": len(node.get("incoming", []))
            })
        
        entity_counts.sort(key=lambda x: x["total_connections"], reverse=True)
        return entity_counts[:limit]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/predicates/frequency")
async def get_predicate_frequency():
    """Get frequency distribution of relationship predicates."""
    try:
        query = query_builder.build_predicate_frequency()
        response = dgraph.query(query["query"], query["variables"])
        
        if "errors" in response:
            raise HTTPException(status_code=500, detail=response["errors"])
        
        relations = response.get("data", {}).get("queryRelation", [])
        
        # Count predicate frequencies
        predicate_counts = {}
        for rel in relations:
            predicate = rel.get("predicate", "unknown")
            predicate_counts[predicate] = predicate_counts.get(predicate, 0) + 1
        
        # Sort by frequency
        sorted_predicates = sorted(predicate_counts.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "total_unique_predicates": len(predicate_counts),
            "predicate_frequencies": [
                {"predicate": pred, "count": count} 
                for pred, count in sorted_predicates
            ]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# ==========================================
# SECTION TEXT
# ==========================================

import pathlib
import os

import fitz  # PyMuPDF
from fastapi.responses import StreamingResponse
from io import BytesIO
from PIL import Image, ImageDraw
import difflib

# ---------------------------------------------------------------------
# Locate repo root and papers directory
# ---------------------------------------------------------------------

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
# knowledge_graph/api.py → parent = "knowledge_graph" → parent = project root
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent

def find_best_matching_pdf(
    requested_name: str,
    papers_dir: pathlib.Path
) -> pathlib.Path | None:
    """Return the closest-matching PDF file to the requested name."""
    requested_clean = requested_name.lower().replace(".pdf", "")

    pdf_files = list(papers_dir.glob("*.pdf"))
    if not pdf_files:
        return None

    pdf_names = [p.stem.lower() for p in pdf_files]
    matches = difflib.get_close_matches(requested_clean, pdf_names, n=1, cutoff=0.4)

    if not matches:
        return None

    best_stem = matches[0]
    return papers_dir / f"{best_stem}.pdf"


# ----------------------------------------
# PROJECT-RELATIVE & ENV-OVERRIDABLE PATHS
# ----------------------------------------


# Default location for papers inside the repo
DEFAULT_PAPERS_DIR = BASE_DIR / "papers"

# Allow override using environment variable
PAPERS_DIR = pathlib.Path(os.getenv("PAPERS_DIR", DEFAULT_PAPERS_DIR))
# Chunks directory (relative to repo root)
DEFAULT_CHUNKS_DIR = BASE_DIR / "kg_gen_pipeline" / "output" / "text_chunks"
CHUNKS_DIR = pathlib.Path(os.getenv("CHUNKS_DIR", DEFAULT_CHUNKS_DIR))

# ==========================================
# SECTION TEXT ENDPOINT (FIXED BBOX HANDLING)
# ==========================================
from fastapi.responses import JSONResponse, StreamingResponse
import io
import fitz  # PyMuPDF
import json
import base64

@app.get("/api/relations/{relation_id}/section-text")
async def get_relation_section_text(
    relation_id: str = Path(..., description="Relation UID")
):
    """
    Return PDF text (and optional bbox snippet) for a KG relation.
    """

    # ---- 1. Fetch provenance for ALL relations ----
    prov_query = query_builder.build_relation_provenance()
    prov_resp = dgraph.query(prov_query["query"])

    if "errors" in prov_resp:
        raise HTTPException(status_code=500, detail=prov_resp["errors"])

    relations = prov_resp.get("data", {}).get("queryRelation", [])
    rel = next((r for r in relations if r.get("id") == relation_id), None)
    print("DEBUG REL:", rel)

    if not rel:
        raise HTTPException(status_code=404, detail=f"Relation '{relation_id}' not found")

    source_name = rel.get("source_paper")
    pages = rel.get("pages")          # list of page numbers (1-indexed)
    section_label = rel.get("section")
    bbox_raw = rel.get("bbox_data")

    # ============================================================
    #  FIXED BBOX PARSER — handles actual DGraph structure
    # ============================================================
    bbox = None
    bbox_page = None

    if bbox_raw:
        try:
            parsed = json.loads(bbox_raw)

            # Expecting a list: [{ "page": N, "bbox": {...}}]
            if isinstance(parsed, list) and len(parsed) > 0:
                entry = parsed[0]
                if "page" in entry and "bbox" in entry:
                    bbox_page = entry["page"]  # 1-indexed
                    bb = entry["bbox"]
                    # Store raw dict for later coordinate conversion
                    bbox = bb

        except Exception:
            bbox = None

    # ---- 2. Find matching PDF ----
    if not source_name:
        raise HTTPException(status_code=400, detail="Relation has no source_paper field")

    pdf_path = find_best_matching_pdf(source_name, PAPERS_DIR)

    if not pdf_path or not pdf_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Could not locate PDF file similar to '{source_name}' in {PAPERS_DIR}"
        )

    # ---- 3. Open PDF ----
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unable to open PDF: {e}")

    extracted_text = ""
    rendered_image_base64 = None

    # ============================================================
    #  CASE A — BBOX AVAILABLE (highest priority)
    # ============================================================
    if bbox and bbox_page:
        page_index = bbox_page - 1
        if 0 <= page_index < len(doc):
            page = doc[page_index]

            # Convert BOTTOMLEFT coords → TOPLEFT (PyMuPDF)
            page_height = page.rect.height

            x0 = bbox["l"]
            x1 = bbox["r"]

            # Convert y from bottom-left to top-left origin
            y_top = page_height - bbox["t"]
            y_bottom = page_height - bbox["b"]

            rect = fitz.Rect(x0, y_top, x1, y_bottom)

            # TEXT
            extracted_text = page.get_text("text", clip=rect) or ""

            # IMAGE
            pix = page.get_pixmap(clip=rect, dpi=180)
            rendered_image_base64 = base64.b64encode(pix.tobytes("png")).decode()

    # ============================================================
    #  CASE B — Extract by pages
    # ============================================================
    elif pages:
        for p in pages:
            # IMPORTANT: provenance pages are 1-indexed, PyMuPDF is 0-indexed
            idx = p - 1
            if 0 <= idx < len(doc):
                extracted_text += doc[idx].get_text()

    # ============================================================
    #  CASE C — Fallback: match section label anywhere
    # ============================================================
    elif section_label:
        section_clean = section_label.lower()
        for page in doc:
            pt = page.get_text()
            if section_clean in pt.lower():
                extracted_text += pt + "\n"

    # ---- Final fallback ----
    if not extracted_text.strip():
        extracted_text = "[No text extracted from PDF for given provenance]"

    return JSONResponse({
        "relation_id": relation_id,
        "pdf_file": str(pdf_path.name),
        "section": section_label,
        "pages": pages,
        "bbox_used": bool(bbox),
        "text": extracted_text,
        "image_base64_png": rendered_image_base64
    })

@app.get("/api/relations/{relation_id}/section-image")
async def get_relation_section_image(
    relation_id: str = Path(..., description="Relation UID")
):

    from fastapi.responses import StreamingResponse
    from io import BytesIO
    import fitz
    import json

    # ---- 1. fetch provenance ----
    prov_query = query_builder.build_relation_provenance()
    prov_resp = dgraph.query(prov_query["query"])

    if "errors" in prov_resp:
        raise HTTPException(status_code=500, detail=prov_resp["errors"])

    relations = prov_resp.get("data", {}).get("queryRelation", [])
    rel = next((r for r in relations if r["id"] == relation_id), None)

    if not rel:
        raise HTTPException(status_code=404, detail="Relation not found")

    source_name = rel.get("source_paper")
    pages = rel.get("pages")
    bbox_raw = rel.get("bbox_data")

    if not bbox_raw:
        raise HTTPException(status_code=400, detail="No bbox_data in relation")

    # ---- 2. parse actual bbox structure ----
    try:
        parsed = json.loads(bbox_raw)
        entry = parsed[0]                     # [{ page: 1, bbox: {...}}]
        bb = entry["bbox"]
        page_number = entry.get("page", pages[0])
    except Exception:
        raise HTTPException(status_code=400, detail="Malformed bbox_data")

    # ---- 3. locate PDF ----
    pdf_path = find_best_matching_pdf(source_name, PAPERS_DIR)
    if not pdf_path or not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF not found")

    doc = fitz.open(pdf_path)

    # provenance is 1-indexed, PyMuPDF is 0-indexed
    page_index = page_number - 1

    if page_index < 0 or page_index >= len(doc):
        raise HTTPException(status_code=400, detail="Invalid page index")

    page = doc[page_index]

    # ---- 4. convert coordinates BOTTOMLEFT → TOPLEFT ----
    page_height = page.rect.height

    x0 = bb["l"]
    y0 = page_height - bb["t"]
    x1 = bb["r"]
    y1 = page_height - bb["b"]

    rect = fitz.Rect(x0, y0, x1, y1)

    # ---- 5. crop & render ----
    try:
        pix = page.get_pixmap(clip=rect, dpi=180)
        png_bytes = pix.tobytes("png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unable to crop PDF region: {e}")

    # ---- 6. return actual PNG file ----
    return StreamingResponse(
        BytesIO(png_bytes),
        media_type="image/png",
        headers={"Content-Disposition": f"inline; filename={relation_id}.png"}
    )

# ==========================================
# HEALTH & INFO ENDPOINTS
# ==========================================

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    try:
        healthy = dgraph.health_check()
        return {
            "status": "healthy" if healthy else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "database": "dgraph",
            "api_version": "1.0.0"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/")
async def root():
    """API root endpoint with basic information."""
    return {
        "message": "Knowledge Graph API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "search": "/api/entities/search, /api/relations/search",
            "traversal": "/api/entities/{name}/connections",
            "provenance": "/api/papers, /api/relations/{id}/provenance",
            "analytics": "/api/graph/stats, /api/entities/most-connected"
        }
    }

# ==========================================
# 6. PAPER REVIEW ENDPOINTS
# ==========================================

@app.post("/api/review")
async def review_paper(request: ReviewRequest):
    """
    Evaluate a scientific paper using 6 specialized rubrics.
    
    Rubrics assess:
    1. Methodology & Research Design
    2. Reproducibility & Transparency
    3. Scientific Rigor
    4. Data Quality & Management
    5. Presentation & Clarity
    6. References & Literature Review
    
    Args:
        request: ReviewRequest with either text or pdf_filename
    
    Returns:
        dict: Rubric responses, merged text, and final synthesis
    
    Example:
        POST /api/review
        {"pdf_filename": "paper.pdf"}
        
        POST /api/review
        {"text": "# Abstract\\n\\nThis paper presents..."}
    """
    try:
        # Validate input
        if not request.text and not request.pdf_filename:
            raise HTTPException(
                status_code=400,
                detail="Either 'text' or 'pdf_filename' must be provided"
            )
        
        if request.text and request.pdf_filename:
            raise HTTPException(
                status_code=400,
                detail="Provide either 'text' or 'pdf_filename', not both"
            )
        
        # Load paper text
        if request.text:
            paper_text = request.text
        else:
            paper_text = load_paper_text(request.pdf_filename)
        
        # Define rubrics
        rubric_files = [
            "llm_review/prompts/rubric1_methodology.txt",
            "llm_review/prompts/rubric2_reproducibility.txt",
            "llm_review/prompts/rubric3_rigor.txt",
            "llm_review/prompts/rubric4_data.txt",
            "llm_review/prompts/rubric5_presentation.txt",
            "llm_review/prompts/rubric6_references.txt"
        ]
        
        # Run each rubric
        rubric_responses = []
        for rubric_file in rubric_files:
            with open(rubric_file, 'r') as f:
                rubric_prompt = f.read()
            
            full_prompt = f"{rubric_prompt}\n\n---PAPER---\n{paper_text}"
            response = run_llm(full_prompt)
            
            rubric_name = rubric_file.split('/')[-1].replace('.txt', '')
            rubric_responses.append({
                "rubric_name": rubric_name,
                "response": response
            })
        
        # Merge rubric outputs
        merged_text = merge_rubric_outputs(rubric_responses)
        
        # Generate final synthesis
        final_summary = synthesize_review(merged_text)
        
        return {
            "rubric_responses": rubric_responses,
            "merged_text": merged_text,
            "final_summary": final_summary,
            "metadata": {
                "rubric_count": len(rubric_responses),
                "provider": os.getenv("LLM_PROVIDER", "openai"),
                "model": os.getenv("OLLAMA_MODEL" if os.getenv("LLM_PROVIDER") == "ollama" else "OPENAI_MODEL", "unknown")
            }
        }
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"File not found: {str(e)}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Configuration error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Review failed: {str(e)}")

@app.post("/api/review/rubric/{rubric_name}")
async def review_paper_single_rubric(rubric_name: str, request: ReviewRequest):
    """
    Evaluate a scientific paper using a single rubric.
    
    Available rubrics:
    - methodology (or rubric1)
    - reproducibility (or rubric2)
    - rigor (or rubric3)
    - data (or rubric4)
    - presentation (or rubric5)
    - references (or rubric6)
    
    Args:
        rubric_name: Name of the rubric to run
        request: ReviewRequest with either text or pdf_filename
    
    Returns:
        dict: Single rubric evaluation
    
    Example:
        POST /api/review/rubric/methodology
        {"text": "# Abstract\\n\\nThis paper presents..."}
    """
    try:
        # Validate input
        if not request.text and not request.pdf_filename:
            raise HTTPException(
                status_code=400,
                detail="Either 'text' or 'pdf_filename' must be provided"
            )
        
        # Map rubric names
        rubric_mapping = {
            "methodology": "rubric1_methodology",
            "rubric1": "rubric1_methodology",
            "reproducibility": "rubric2_reproducibility",
            "rubric2": "rubric2_reproducibility",
            "rigor": "rubric3_rigor",
            "rubric3": "rubric3_rigor",
            "data": "rubric4_data",
            "rubric4": "rubric4_data",
            "presentation": "rubric5_presentation",
            "rubric5": "rubric5_presentation",
            "references": "rubric6_references",
            "rubric6": "rubric6_references"
        }
        
        if rubric_name.lower() not in rubric_mapping:
            available = list(set(rubric_mapping.keys()))
            raise HTTPException(
                status_code=400,
                detail=f"Invalid rubric name. Available: {', '.join(available)}"
            )
        
        # Load paper text
        if request.text:
            paper_text = request.text
        else:
            paper_text = load_paper_text(request.pdf_filename)
        
        # Get rubric file
        rubric_file = f"llm_review/prompts/{rubric_mapping[rubric_name.lower()]}.txt"
        
        # Run rubric
        with open(rubric_file, 'r') as f:
            rubric_prompt = f.read()
        
        full_prompt = f"{rubric_prompt}\n\n---PAPER---\n{paper_text}"
        response = run_llm(full_prompt)
        
        return {
            "rubric_name": rubric_mapping[rubric_name.lower()],
            "response": response,
            "metadata": {
                "provider": os.getenv("LLM_PROVIDER", "openai"),
                "model": os.getenv("OLLAMA_MODEL" if os.getenv("LLM_PROVIDER") == "ollama" else "OPENAI_MODEL", "unknown")
            }
        }
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"File not found: {str(e)}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Configuration error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rubric evaluation failed: {str(e)}")


@app.post("/api/review/figures")
async def review_paper_figures(request: ReviewRequest):
    """
    Evaluate all figures in a scientific paper using all 6 rubrics with vision models.
    
    Runs complete evaluation (methodology, reproducibility, rigor, data, 
    presentation, references) on each figure using vision models to analyze
    the visual content.
    
    Args:
        request: ReviewRequest with pdf_filename (required for figures)
    
    Returns:
        dict: Complete rubric assessments for all figures in the paper
    
    Example:
        POST /api/review/figures
        {"pdf_filename": "A. Priyadarsini et al. 2023.pdf"}
    """
    from llm_review.utils.figure_extractor import load_paper_figures
    from llm_review.utils.vision_runner import analyze_figure
    from pathlib import Path
    
    try:
        # Validate input
        if not request.pdf_filename:
            raise HTTPException(
                status_code=400,
                detail="pdf_filename is required for figure review"
            )
        
        # Extract figures from paper
        figures = load_paper_figures(request.pdf_filename)
        
        if not figures:
            return {
                "figure_count": 0,
                "message": "No figures found in this paper",
                "metadata": {
                    "provider": os.getenv("VISION_PROVIDER", "openai"),
                    "model": os.getenv("VISION_MODEL", "gpt-4o")
                }
            }
        
        # All 6 rubrics
        rubrics = [
            "rubric1_methodology",
            "rubric2_reproducibility", 
            "rubric3_rigor",
            "rubric4_data",
            "rubric5_presentation",
            "rubric6_references"
        ]
        
        # Analyze each figure with all rubrics
        figure_reviews = []
        for figure in figures:
            try:
                # Save image temporarily for vision model
                temp_image_path = f"/tmp/{figure['figure_id']}.png"
                figure['image'].save(temp_image_path)
                
                # Run all 6 rubrics on this figure
                rubric_responses = []
                for rubric_name in rubrics:
                    rubric_path = f"llm_review/prompts/{rubric_name}.txt"
                    with open(rubric_path, 'r') as f:
                        rubric_prompt = f.read()
                    
                    # Analyze with vision model
                    assessment = analyze_figure(
                        figure_image_path=temp_image_path,
                        figure_caption=figure['caption_text'],
                        rubric_prompt=rubric_prompt,
                        paper_context=f"Page {figure['page']}, Figure {figure['figure_id']}"
                    )
                    
                    rubric_responses.append({
                        "rubric_name": rubric_name,
                        "response": assessment
                    })
                
                figure_reviews.append({
                    "figure_id": figure['figure_id'],
                    "page": figure['page'],
                    "caption": figure['caption_text'],
                    "rubric_responses": rubric_responses
                })
                
                # Clean up temp file
                Path(temp_image_path).unlink(missing_ok=True)
                
            except Exception as e:
                figure_reviews.append({
                    "figure_id": figure['figure_id'],
                    "page": figure['page'],
                    "caption": figure['caption_text'],
                    "error": str(e)
                })
        
        return {
            "figure_count": len(figures),
            "figure_reviews": figure_reviews,
            "metadata": {
                "provider": os.getenv("VISION_PROVIDER", "openai"),
                "model": os.getenv("VISION_MODEL", "gpt-4o")
            }
        }
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"File not found: {str(e)}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Configuration error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Figure review failed: {str(e)}")


@app.post("/api/review/figure/{figure_id}/rubric/{rubric_name}")
async def review_single_figure_rubric(figure_id: str, rubric_name: str, request: ReviewRequest):
    """
    Evaluate a single figure using a specific rubric with vision models.
    
    Available rubrics (same as text review):
    - methodology (or rubric1)
    - reproducibility (or rubric2)
    - rigor (or rubric3)
    - data (or rubric4)
    - presentation (or rubric5)
    - references (or rubric6)
    
    Args:
        figure_id: Figure identifier (e.g., "page5_fig0", "page6_fig0")
        rubric_name: Name of the rubric to apply
        request: ReviewRequest with pdf_filename (required for figures)
    
    Returns:
        dict: Single rubric assessment for the specified figure
    
    Example:
        POST /api/review/figure/page5_fig0/rubric/presentation
        {"pdf_filename": "A. Priyadarsini et al. 2023.pdf"}
    """
    from llm_review.utils.figure_extractor import load_paper_figures
    from llm_review.utils.vision_runner import analyze_figure
    from pathlib import Path
    
    try:
        # Validate input
        if not request.pdf_filename:
            raise HTTPException(
                status_code=400,
                detail="pdf_filename is required for figure review"
            )
        
        # Map rubric names (same as text rubrics)
        rubric_mapping = {
            "methodology": "rubric1_methodology",
            "rubric1": "rubric1_methodology",
            "reproducibility": "rubric2_reproducibility",
            "rubric2": "rubric2_reproducibility",
            "rigor": "rubric3_rigor",
            "rubric3": "rubric3_rigor",
            "data": "rubric4_data",
            "rubric4": "rubric4_data",
            "presentation": "rubric5_presentation",
            "rubric5": "rubric5_presentation",
            "references": "rubric6_references",
            "rubric6": "rubric6_references"
        }
        
        if rubric_name.lower() not in rubric_mapping:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown rubric: {rubric_name}. Available: methodology, reproducibility, rigor, data, presentation, references"
            )
        
        # Load rubric
        rubric_file = f"llm_review/prompts/{rubric_mapping[rubric_name.lower()]}.txt"
        with open(rubric_file, 'r') as f:
            rubric_prompt = f.read()
        
        # Extract figures from paper
        figures = load_paper_figures(request.pdf_filename)
        
        # Find the requested figure
        target_figure = None
        for figure in figures:
            if figure['figure_id'] == figure_id:
                target_figure = figure
                break
        
        if not target_figure:
            raise HTTPException(
                status_code=404,
                detail=f"Figure {figure_id} not found. Available figures: {[f['figure_id'] for f in figures]}"
            )
        
        # Save image temporarily for vision model
        temp_image_path = f"/tmp/{figure_id}.png"
        target_figure['image'].save(temp_image_path)
        
        try:
            # Analyze with vision model
            assessment = analyze_figure(
                figure_image_path=temp_image_path,
                figure_caption=target_figure['caption_text'],
                rubric_prompt=rubric_prompt,
                paper_context=f"Page {target_figure['page']}, Figure {figure_id}"
            )
            
            return {
                "figure_id": figure_id,
                "page": target_figure['page'],
                "caption": target_figure['caption_text'],
                "rubric_name": rubric_mapping[rubric_name.lower()],
                "response": assessment,
                "metadata": {
                    "provider": os.getenv("VISION_PROVIDER", "openai"),
                    "model": os.getenv("VISION_MODEL", "gpt-4o")
                }
            }
            
        finally:
            # Clean up temp file
            Path(temp_image_path).unlink(missing_ok=True)
        
    except HTTPException:
        raise
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"File not found: {str(e)}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Configuration error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Figure review failed: {str(e)}")


# ==========================================
# NEW SIMPLIFIED ENDPOINTS (Frontend-Based)
# ==========================================

class FigureReviewRequest(BaseModel):
    image_data: str = Field(..., description="Base64 encoded image data (with or without data:image/png;base64, prefix)")
    rubric: str = Field(..., description="Rubric name: methodology, reproducibility, rigor, data, presentation, or references")

class TableReviewRequest(BaseModel):
    table_data: Dict[str, Any] = Field(..., description="Docling table object with data, grid, and metadata")
    rubric: str = Field(..., description="Rubric name: methodology, reproducibility, rigor, data, presentation, or references")


@app.post("/api/review/figure")
async def review_figure_base64(request: FigureReviewRequest):
    """
    Review a figure using base64 image data from the frontend.
    
    This endpoint accepts image data directly from the frontend (which already extracts
    figures as data URLs), eliminating the need for backend PDF processing.
    
    Args:
        request: FigureReviewRequest with image_data (base64) and rubric name
    
    Returns:
        dict: Figure review with assessment text
    
    Example:
        POST /api/review/figure
        {
            "image_data": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
            "rubric": "presentation"
        }
    """
    from llm_review.utils.vision_runner import run_vision_model
    import base64
    from pathlib import Path
    
    try:
        # Map rubric names
        rubric_mapping = {
            "methodology": "rubric1_methodology",
            "reproducibility": "rubric2_reproducibility",
            "rigor": "rubric3_rigor",
            "data": "rubric4_data",
            "presentation": "rubric5_presentation",
            "references": "rubric6_references"
        }
        
        rubric_key = request.rubric.lower()
        if rubric_key not in rubric_mapping:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown rubric: {request.rubric}. Available: methodology, reproducibility, rigor, data, presentation, references"
            )
        
        # Load rubric prompt
        rubric_file = f"llm_review/prompts/{rubric_mapping[rubric_key]}.txt"
        with open(rubric_file, 'r') as f:
            rubric_prompt = f.read()
        
        # Strip data URL prefix if present
        image_data = request.image_data
        if image_data.startswith('data:image'):
            # Extract base64 after the comma
            image_data = image_data.split(',', 1)[1]
        
        # Decode base64 to verify it's valid
        try:
            image_bytes = base64.b64decode(image_data)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid base64 image data: {str(e)}"
            )
        
        # Save to temp file for vision model
        temp_image_path = "/tmp/frontend_figure_review.png"
        with open(temp_image_path, 'wb') as f:
            f.write(image_bytes)
        
        try:
            # Call vision model
            assessment = run_vision_model(
                image_path=temp_image_path,
                prompt=rubric_prompt
            )
            
            return {
                "review": assessment,
                "rubric": rubric_mapping[rubric_key],
                "metadata": {
                    "provider": os.getenv("VISION_PROVIDER", "openai"),
                    "model": os.getenv("VISION_MODEL", "gpt-4o")
                }
            }
            
        finally:
            # Clean up temp file
            Path(temp_image_path).unlink(missing_ok=True)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Figure review failed: {str(e)}")


@app.post("/api/review/table")
async def review_table_data(request: TableReviewRequest):
    """
    Review a table using Docling table object from the frontend.
    
    This endpoint accepts table data directly from the frontend (which already parses
    Docling JSON), eliminating the need for backend table extraction.
    
    Args:
        request: TableReviewRequest with table_data (Docling object) and rubric name
    
    Returns:
        dict: Table review with assessment text
    
    Example:
        POST /api/review/table
        {
            "table_data": {
                "data": {...},
                "grid": [...],
                "text": "...",
                "caption": {"text": "Table 1. Results..."}
            },
            "rubric": "data"
        }
    """
    try:
        # Map rubric names
        rubric_mapping = {
            "methodology": "rubric1_methodology",
            "reproducibility": "rubric2_reproducibility",
            "rigor": "rubric3_rigor",
            "data": "rubric4_data",
            "presentation": "rubric5_presentation",
            "references": "rubric6_references"
        }
        
        rubric_key = request.rubric.lower()
        if rubric_key not in rubric_mapping:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown rubric: {request.rubric}. Available: methodology, reproducibility, rigor, data, presentation, references"
            )
        
        # Load rubric prompt
        rubric_file = f"llm_review/prompts/{rubric_mapping[rubric_key]}.txt"
        with open(rubric_file, 'r') as f:
            rubric_prompt = f.read()
        
        # Format table data as markdown/text for the LLM
        table_text = format_table_for_review(request.table_data)
        
        # Build prompt combining rubric and table
        full_prompt = f"{rubric_prompt}\n\n---\n\nTable to Review:\n\n{table_text}\n\n---\n\nPlease evaluate this table according to the rubric above."
        
        # Call text LLM (not vision model)
        assessment = run_llm(
            prompt=full_prompt,
            temperature=0.7
        )
        
        return {
            "review": assessment,
            "rubric": rubric_mapping[rubric_key],
            "metadata": {
                "provider": os.getenv("LLM_PROVIDER", "ollama"),
                "model": os.getenv("OLLAMA_MODEL" if os.getenv("LLM_PROVIDER") == "ollama" else "OPENAI_MODEL", "llama3.1:8b")
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Table review failed: {str(e)}")


def format_table_for_review(table_data: Dict[str, Any]) -> str:
    """
    Format Docling table object as markdown/text for LLM review.
    
    Args:
        table_data: Docling table object with data, grid, text, caption
    
    Returns:
        str: Formatted table text for review
    """
    parts = []
    
    # Add caption if available
    if 'caption' in table_data and table_data['caption']:
        caption_text = table_data['caption'].get('text', '')
        if caption_text:
            parts.append(f"Caption: {caption_text}\n")
    
    # Add table text (pre-rendered by Docling)
    if 'text' in table_data and table_data['text']:
        parts.append("Table Content:")
        parts.append(table_data['text'])
    
    # If no text, try to format from grid
    elif 'grid' in table_data and table_data['grid']:
        parts.append("Table Content:")
        grid = table_data['grid']
        
        # Simple markdown table formatting
        for row in grid:
            if isinstance(row, list):
                parts.append("| " + " | ".join(str(cell) for cell in row) + " |")
    
    # Add data dict if available
    elif 'data' in table_data and table_data['data']:
        parts.append("Table Data:")
        parts.append(json.dumps(table_data['data'], indent=2))
    
    return "\n".join(parts)


# ==========================================
# STARTUP CONFIGURATION
# ==========================================

if __name__ == "__main__":
    try:
        # Get optimal port configuration
        api_port = get_optimal_configuration()
        
        print(f"Starting Knowledge Graph API on http://localhost:{api_port}")
        print(f"API Documentation: http://localhost:{api_port}/docs")
        print(f"Source Span Endpoint: http://localhost:{api_port}/api/relations/{{id}}/source-span")
        
        uvicorn.run(
            "api:app",
            host="0.0.0.0",
            port=api_port,
            reload=True,
            log_level="info"
        )
        
    except Exception as e:
        print(f"Startup error: {e}")
        print("Trying fallback port 8001...")
        uvicorn.run(
            "api:app",
            host="0.0.0.0",
            port=8001,
            reload=True,
            log_level="info"
        )