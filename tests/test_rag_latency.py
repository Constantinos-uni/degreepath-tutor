import asyncio
import time
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.rag import rag_system

async def test_rag():
    print("Starting RAG Test...")
    
    # Measure Ingestion Time
    start_time = time.time()
    await rag_system.ingest_skills()
    await rag_system.ingest_materials()
    # Note: ingest_units might take longer if DB is large, but we'll test it.
    await rag_system.ingest_units()
    ingest_time = time.time() - start_time
    print(f"Ingestion Time: {ingest_time:.4f}s")
    
    # Measure Retrieval Time (First Run - Uncached)
    query = "What are the prerequisites for COMP1000?"
    start_time = time.time()
    results = await rag_system.query(query)
    retrieval_time = time.time() - start_time
    print(f"Retrieval Time (Uncached): {retrieval_time:.4f}s")
    
    if retrieval_time > 0.2:
        print("WARNING: Retrieval time > 200ms")
    
    print(f"Top Result: {results[0]['content'][:100]}...")
    
    # Measure Retrieval Time (Second Run - Cached)
    start_time = time.time()
    results_cached = await rag_system.query(query)
    cached_time = time.time() - start_time
    print(f"Retrieval Time (Cached): {cached_time:.4f}s")
    
    if cached_time < retrieval_time:
        print("SUCCESS: Caching is working (faster response).")
    else:
        print("NOTE: Caching might not be effective or overhead is high.")

if __name__ == "__main__":
    asyncio.run(test_rag())
