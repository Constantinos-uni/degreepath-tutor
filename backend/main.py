"""
Part 1 API: Unit Database, RAG System, and Eligibility Checking
Provides unit information with live web search and database fallback.
"""

import os
import re
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .models import EligibilityRequest, EligibilityResponse, UnitResponse, Unit
from .logic import check_prereqs, check_incompatibles
from .database import get_unit, save_unit
from .rag import rag_system
from .unit_search import search_unit, unit_searcher

load_dotenv()

# Configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

app = FastAPI(
    title="DegreePath Tutor - Part 1",
    description="Unit database, RAG system, and eligibility checking API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models

class RAGQueryRequest(BaseModel):
    query: str
    k: int = Field(default=5, ge=1, le=20)
    filter_source: Optional[str] = None
    filter_type: Optional[str] = None
    filter_unit_code: Optional[str] = None
    include_live: bool = True


class SmartSearchRequest(BaseModel):
    query: str
    include_prerequisites: bool = True
    include_rag: bool = True
    max_results: int = Field(default=5, ge=1, le=10)


# Helper Functions

def get_unit_with_live_first(unit_code: str, use_cache: bool = False) -> Optional[Dict[str, Any]]:
    """
    Get unit data with live web search as primary source.
    
    Priority:
        1. Live web search (accurate prerequisites)
        2. Database (cache/fallback)
    """
    unit_code = unit_code.upper()
    
    if use_cache:
        unit_data = get_unit(unit_code)
        if unit_data and unit_data.get("title") and unit_data["title"] != "Placeholder Unit":
            return unit_data
    
    live_data = search_unit(unit_code)
    
    if live_data and live_data.get("unit_code"):
        save_unit({
            "unit_code": live_data["unit_code"],
            "title": live_data["title"],
            "description": live_data["description"],
            "credit_points": live_data["credit_points"],
            "year_level": live_data["year_level"],
            "raw_prerequisites": live_data["raw_prerequisites"],
            "raw_corequisites": live_data["raw_corequisites"],
            "learning_outcomes": live_data["learning_outcomes"]
        })
        
        return {
            "unit_code": live_data["unit_code"],
            "title": live_data["title"],
            "description": live_data["description"],
            "credit_points": live_data["credit_points"],
            "year_level": live_data["year_level"],
            "prerequisites": live_data["prerequisites"],
            "raw_prerequisites": live_data["raw_prerequisites"],
            "raw_corequisites": live_data["raw_corequisites"],
            "corequisites": live_data["corequisites"],
            "incompatible_units": [],
            "learning_outcomes": live_data["learning_outcomes"],
            "source": "live_web"
        }
    
    unit_data = get_unit(unit_code)
    
    if unit_data and unit_data.get("title") and unit_data["title"] != "Placeholder Unit":
        unit_data["source"] = "database_fallback"
        return unit_data
    
    return None


# Endpoints

@app.get("/")
def read_root():
    """Service information."""
    return {
        "service": "DegreePath Tutor - Part 1",
        "version": "1.0.0",
        "features": ["database", "rag", "live_web_search"]
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "features": ["database", "rag", "live_web_search"]}


@app.get("/unit/{unit_code}", response_model=UnitResponse)
def get_unit_endpoint(unit_code: str, force_live: bool = False, use_cache: bool = False):
    """
    Get unit details with live web search as primary source.
    
    Args:
        unit_code: The unit code (e.g., COMP1010)
        force_live: Always fetch from web
        use_cache: Try database first for speed
    """
    unit_code = unit_code.upper()
    
    if force_live:
        live_data = search_unit(unit_code)
        if not live_data:
            raise HTTPException(status_code=404, detail=f"Unit {unit_code} not found")
        
        return {
            "unit_code": unit_code,
            "details": {
                "title": live_data["title"],
                "prerequisites": live_data["prerequisites"],
                "corequisites": live_data["corequisites"],
                "incompatible_units": [],
                "credit_points": live_data["credit_points"],
                "year_level": live_data["year_level"],
                "learning_outcomes": live_data["learning_outcomes"]
            },
            "source": "live_web"
        }
    
    unit_data = get_unit_with_live_first(unit_code, use_cache=use_cache)
    
    if not unit_data:
        raise HTTPException(status_code=404, detail=f"Unit {unit_code} not found")
    
    return {
        "unit_code": unit_code,
        "details": {
            "title": unit_data["title"],
            "prerequisites": unit_data.get("prerequisites", []),
            "corequisites": [unit_data["raw_corequisites"]] if unit_data.get("raw_corequisites") else [],
            "incompatible_units": unit_data.get("incompatible_units", []),
            "credit_points": unit_data.get("credit_points", 10),
            "year_level": unit_data.get("year_level", 1),
            "learning_outcomes": unit_data.get("learning_outcomes", [])
        }
    }


@app.get("/unit/{unit_code}/live")
def get_unit_live(unit_code: str):
    """Get unit details directly from live web scraping."""
    unit_code = unit_code.upper()
    
    live_data = search_unit(unit_code)
    
    if not live_data:
        raise HTTPException(status_code=404, detail=f"Unit {unit_code} not found")
    
    return {
        "unit_code": unit_code,
        "title": live_data["title"],
        "description": live_data["description"],
        "credit_points": live_data["credit_points"],
        "year_level": live_data["year_level"],
        "prerequisites": live_data["prerequisites"],
        "raw_prerequisites": live_data["raw_prerequisites"],
        "corequisites": live_data["corequisites"],
        "raw_corequisites": live_data["raw_corequisites"],
        "learning_outcomes": live_data["learning_outcomes"],
        "source_url": live_data["source_url"],
        "source": "live_web"
    }


@app.post("/eligibility", response_model=EligibilityResponse)
def check_eligibility(request: EligibilityRequest):
    """Check if a student is eligible to take specified units."""
    if not request.query_units:
        return {
            "eligible": False,
            "missing_prerequisites": [],
            "incompatible_units": [],
            "errors": ["No query units provided"]
        }
    
    target_unit = request.query_units[0].upper()
    unit_data = get_unit_with_live_first(target_unit)
    
    if not unit_data:
        return {
            "eligible": False,
            "missing_prerequisites": [],
            "incompatible_units": [],
            "errors": [f"Unit {target_unit} not found"]
        }
    
    prerequisites = unit_data.get("prerequisites", [])
    completed_upper = [u.upper() for u in request.completed_units]
    
    missing = [p for p in prerequisites if p.upper() not in completed_upper]
    incompatibles = check_incompatibles(request.completed_units, target_unit)
    
    is_eligible = len(missing) == 0 and len(incompatibles) == 0
    
    return {
        "eligible": is_eligible,
        "missing_prerequisites": missing,
        "incompatible_units": incompatibles,
        "errors": []
    }


@app.post("/rag/ingest")
async def trigger_ingest(background_tasks: BackgroundTasks):
    """Trigger RAG ingestion in background."""
    background_tasks.add_task(rag_system.ingest_units)
    background_tasks.add_task(rag_system.ingest_skills)
    background_tasks.add_task(rag_system.ingest_materials)
    return {"message": "Ingestion started in background"}


@app.post("/rag/ingest-live")
async def ingest_live_units(background_tasks: BackgroundTasks, unit_codes: Optional[List[str]] = None):
    """Fetch units from web and ingest into RAG system."""
    
    async def fetch_and_ingest():
        if unit_codes:
            for code in unit_codes:
                live_data = search_unit(code)
                if live_data:
                    save_unit({
                        "unit_code": live_data["unit_code"],
                        "title": live_data["title"],
                        "description": live_data["description"],
                        "credit_points": live_data["credit_points"],
                        "year_level": live_data["year_level"],
                        "raw_prerequisites": live_data["raw_prerequisites"],
                        "raw_corequisites": live_data["raw_corequisites"],
                        "learning_outcomes": live_data["learning_outcomes"]
                    })
        else:
            all_codes = unit_searcher.get_all_computing_units()
            for code in all_codes[:50]:
                live_data = search_unit(code)
                if live_data:
                    save_unit({
                        "unit_code": live_data["unit_code"],
                        "title": live_data["title"],
                        "description": live_data["description"],
                        "credit_points": live_data["credit_points"],
                        "year_level": live_data["year_level"],
                        "raw_prerequisites": live_data["raw_prerequisites"],
                        "raw_corequisites": live_data["raw_corequisites"],
                        "learning_outcomes": live_data["learning_outcomes"]
                    })
        
        await rag_system.ingest_units()
    
    background_tasks.add_task(fetch_and_ingest)
    return {"message": "Live ingestion started", "unit_codes": unit_codes or "all computing units"}


@app.post("/rag/query")
async def query_rag(request: RAGQueryRequest):
    """Query RAG system with optional metadata filters."""
    results = await rag_system.query(
        query_text=request.query,
        k=request.k,
        filter_source=request.filter_source,
        filter_type=request.filter_type,
        filter_unit_code=request.filter_unit_code
    )
    
    live_results = []
    if request.include_live:
        unit_codes = re.findall(r'[A-Z]{4}\d{4}', request.query.upper())
        for code in unit_codes[:3]:
            live_data = search_unit(code)
            if live_data:
                live_results.append({
                    "content": f"Unit: {live_data['unit_code']} - {live_data['title']}\nDescription: {live_data['description']}\nPrerequisites: {', '.join(live_data['prerequisites']) or 'None'}",
                    "metadata": {"source": "live_web", "type": "unit_info", "unit_code": code},
                    "distance": 0,
                    "similarity_percent": 100
                })
    
    return {
        "query": request.query,
        "filters": {
            "source": request.filter_source,
            "type": request.filter_type,
            "unit_code": request.filter_unit_code
        },
        "results": live_results + results,
        "count": len(live_results) + len(results),
        "live_count": len(live_results)
    }


@app.post("/search/smart")
async def smart_search(request: SmartSearchRequest):
    """Smart search combining RAG, database, and live web data."""
    results = {
        "query": request.query,
        "units": [],
        "rag_results": [],
        "prerequisite_chains": []
    }
    
    unit_codes = re.findall(r'[A-Z]{4}\d{4}', request.query.upper())
    
    for code in unit_codes[:5]:
        unit_data = get_unit_with_live_first(code, use_cache=True)
        if unit_data:
            results["units"].append({
                "unit_code": code,
                "title": unit_data.get("title"),
                "description": unit_data.get("description", "")[:300],
                "prerequisites": unit_data.get("prerequisites", []),
                "year_level": unit_data.get("year_level"),
                "credit_points": unit_data.get("credit_points")
            })
            
            if request.include_prerequisites and unit_data.get("prerequisites"):
                chain = [code]
                prereqs = unit_data.get("prerequisites", [])
                
                for _ in range(3):
                    next_prereqs = []
                    for prereq in prereqs:
                        if prereq not in chain:
                            chain.append(prereq)
                            prereq_data = get_unit_with_live_first(prereq, use_cache=True)
                            if prereq_data:
                                next_prereqs.extend(prereq_data.get("prerequisites", []))
                    prereqs = next_prereqs
                    if not prereqs:
                        break
                
                results["prerequisite_chains"].append({
                    "unit": code,
                    "chain": chain,
                    "description": f"To take {code}, you need: {' -> '.join(reversed(chain))}"
                })
    
    if request.include_rag:
        rag_results = await rag_system.query(request.query, k=request.max_results)
        results["rag_results"] = rag_results
    
    return results


@app.get("/units/computing")
def list_computing_units():
    """Get list of all computing unit codes from live web."""
    codes = unit_searcher.get_all_computing_units()
    return {"count": len(codes), "unit_codes": codes}


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("PART1_HOST", "127.0.0.1")
    port = int(os.getenv("PART1_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
