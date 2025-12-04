"""
RAG (Retrieval-Augmented Generation) System
Uses ChromaDB for vector storage and HuggingFace embeddings for semantic search.
"""

import os
import json
import asyncio
import hashlib
from typing import List, Dict, Any, Optional

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

from .database import get_all_units

CHROMA_DB_DIR = os.path.join(os.path.dirname(__file__), "data", "chroma_db")
SKILLS_FILE = os.path.join(os.path.dirname(__file__), "data", "skills_roles.json")
MATERIALS_FILE = os.path.join(os.path.dirname(__file__), "data", "learning_materials.json")

QUERY_EXPANSIONS = {
    "oop": "object-oriented programming",
    "db": "database",
    "ai": "artificial intelligence",
    "ml": "machine learning",
    "ds": "data science",
    "fe": "frontend",
    "be": "backend",
}

class RAGSystem:
    """Vector-based retrieval system for semantic search over unit information."""
    
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.vector_store = Chroma(
            persist_directory=CHROMA_DB_DIR,
            embedding_function=self.embeddings,
            collection_name="degreepath_knowledge"
        )
        self.indexed_ids = set()
    
    def _generate_doc_id(self, content: str, metadata: Dict[str, Any]) -> str:
        """Generate unique ID for document based on content and metadata."""
        key = f"{metadata.get('unit_code', '')}:{metadata.get('type', '')}:{content[:100]}"
        return hashlib.md5(key.encode()).hexdigest()
    
    def _expand_query(self, query: str) -> str:
        """Expand abbreviations in query."""
        query_lower = query.lower()
        for abbrev, full in QUERY_EXPANSIONS.items():
            if abbrev in query_lower:
                query = query.replace(abbrev, full)
                query = query.replace(abbrev.upper(), full)
        return query
    
    def _normalize_score(self, distance: float) -> float:
        """Convert ChromaDB distance to similarity percentage (0-100)."""
        clamped = min(distance, 2.0)
        similarity = max(0, 100 * (1 - clamped / 2.0))
        return round(similarity, 2)

    async def ingest_units(self):
        """Ingest units from database into vector store."""
        units = get_all_units()
        documents = []

        for unit_code, unit in units.items():
            prereq_list = unit.get('prerequisites', [])
            prereq_text = ', '.join(prereq_list) if prereq_list else unit.get('raw_prerequisites', 'None')
            desc_text = f"Unit Code: {unit_code}\nTitle: {unit['title']}\nDescription: {unit['description']}\nPrerequisites: {prereq_text}\nCredit Points: {unit.get('credit_points', 'N/A')}"
            
            metadata = {"source": "unit_guide", "type": "description", "unit_code": unit_code}
            doc_id = self._generate_doc_id(desc_text, metadata)
            
            if doc_id not in self.indexed_ids:
                documents.append(Document(
                    page_content=desc_text,
                    metadata=metadata,
                    id=doc_id
                ))
                self.indexed_ids.add(doc_id)

            for i, outcome in enumerate(unit.get('learning_outcomes', [])):
                lo_text = f"Unit Code: {unit_code}\nLearning Outcome {i+1}: {outcome}"
                lo_metadata = {"source": "unit_guide", "type": "learning_outcome", "unit_code": unit_code, "outcome_index": i}
                lo_id = self._generate_doc_id(lo_text, lo_metadata)
                
                if lo_id not in self.indexed_ids:
                    documents.append(Document(
                        page_content=lo_text,
                        metadata=lo_metadata,
                        id=lo_id
                    ))
                    self.indexed_ids.add(lo_id)

        if documents:
            await self._add_documents_async(documents)

    async def ingest_skills(self):
        """Ingest skills and roles from JSON file."""
        if not os.path.exists(SKILLS_FILE):
            return

        with open(SKILLS_FILE, 'r') as f:
            skills_data = json.load(f)

        documents = []
        for item in skills_data:
            text = f"Skill: {item['skill']}\nRoles: {', '.join(item['roles'])}\nDescription: {item['description']}\nCertifications: {', '.join(item.get('certifications', []))}"
            metadata = {"source": "skills_mapping", "type": "skill", "skill_name": item['skill']}
            doc_id = self._generate_doc_id(text, metadata)
            
            if doc_id not in self.indexed_ids:
                documents.append(Document(
                    page_content=text,
                    metadata=metadata,
                    id=doc_id
                ))
                self.indexed_ids.add(doc_id)

        if documents:
            await self._add_documents_async(documents)

    async def ingest_materials(self):
        """Ingest learning materials from JSON file."""
        if not os.path.exists(MATERIALS_FILE):
            return

        with open(MATERIALS_FILE, 'r') as f:
            materials_data = json.load(f)

        documents = []
        for item in materials_data:
            text = f"Title: {item['title']}\nType: {item['type']}\nDescription: {item['description']}\nURL: {item['url']}\nTags: {', '.join(item.get('tags', []))}"
            metadata = {"source": "public_resource", "type": "material", "title": item['title']}
            doc_id = self._generate_doc_id(text, metadata)
            
            if doc_id not in self.indexed_ids:
                documents.append(Document(
                    page_content=text,
                    metadata=metadata,
                    id=doc_id
                ))
                self.indexed_ids.add(doc_id)

        if documents:
            await self._add_documents_async(documents)

    async def _add_documents_async(self, documents: List[Document]):
        """Add documents to vector store asynchronously."""
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.vector_store.add_documents, documents)

    async def query(
        self, 
        query_text: str, 
        k: int = 5,
        filter_source: Optional[str] = None,
        filter_type: Optional[str] = None,
        filter_unit_code: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query_text: Search query
            k: Number of results to return
            filter_source: Filter by source (unit_guide, skills_mapping, etc.)
            filter_type: Filter by type (description, learning_outcome, skill)
            filter_unit_code: Filter by specific unit code
        """
        expanded_query = self._expand_query(query_text)
        
        where_filter = {}
        if filter_source:
            where_filter["source"] = filter_source
        if filter_type:
            where_filter["type"] = filter_type
        if filter_unit_code:
            where_filter["unit_code"] = filter_unit_code
        
        loop = asyncio.get_running_loop()
        
        if where_filter:
            results = await loop.run_in_executor(
                None,
                lambda: self.vector_store.similarity_search_with_score(
                    expanded_query, k=k * 2, filter=where_filter
                )
            )
        else:
            results = await loop.run_in_executor(
                None, 
                lambda: self.vector_store.similarity_search_with_score(expanded_query, k=k * 2)
            )
        
        seen_content = set()
        formatted_results = []
        
        for doc, distance in results:
            content_hash = hashlib.md5(doc.page_content.encode()).hexdigest()
            
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                formatted_results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "distance": round(distance, 4),
                    "similarity_percent": self._normalize_score(distance)
                })
            
            if len(formatted_results) >= k:
                break
        
        return formatted_results


rag_system = RAGSystem()
