"""
Reef Knowledge Vector Database
=========================
This module scrapes reef aquarium content from the web and stores embeddings 
in a FAISS vector database for semantic search (RAG context).

Usage:
    from vector_db import create_vector_db, get_vector_context
    
    # Initialize the database (run once)
    kb = create_vector_db()
    
    # Get relevant context for a question
    context = get_vector_context("How do I set up a calcium reactor?", k=3)

The vector database enables ReefGPT to find relevant reef-keeping knowledge
to inject into the LLM prompt when answering user questions.
"""

# Standard library imports
import os
import json
import time
import hashlib
import requests
import threading
import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

# Third-party imports for ML/vectors
import numpy as np
from sentence_transformers import SentenceTransformer  # Text embeddings

# Check if torch is available (used by sentence_transformers)
try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))


# ============================================================================
# CONFIGURATION
# ============================================================================

# Embedding dimension for All-MiniLM-L6-v2 model
EMBED_DIM = 384


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class ReefKnowledgeChunk:
    """
    Represents a single piece of reef knowledge to store in the vector DB.
    
    Each chunk contains:
    - content: The actual text (e.g., "Calcium reactors maintain 400ppm calcium...")
    - source: Where it came from (e.g., "web_search", "Bulk Reef Supply")
    - url: The URL where it was found
    - title: Title of the article/page
    - topic: Category (e.g., "calcium", "pH", "corals")
    - timestamp: When it was scraped
    - chunk_id: Unique identifier (hash of content)
    """
    content: str
    source: str
    url: str
    title: str
    topic: str
    timestamp: str
    chunk_id: str
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON storage."""
        return asdict(self)


# ============================================================================
# WEB SCRAPER
# ============================================================================

class ReefScraper:
    """
    Scrapes reef content from websites.
    
    Note: Most reef forums (Reef2Reef, Humble.fish) block scraping (403).
    We use DuckDuckGo web search instead to find content.
    """
    
    # No direct scraping - most sites block us
    SOURCES = {}  # Web search only


class WebSearchScraper:
    """
    Uses DuckDuckGo web search to find reef aquarium content.
    
    This is more reliable than direct website scraping because:
    1. Forums block automated scraping (403 Forbidden)
    2. Many reef sites are just e-commerce (no articles)
    3. Web search finds relevant articles from multiple sources
    
    Search results come from DuckDuckGo's HTML interface.
    """
    
    def __init__(self):
        """Initialize session with browser-like headers."""
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        })
        self.chunks: List[ReefKnowledgeChunk] = []
    
    def search_and_scrape(self, query: str, max_results: int = 10) -> List[ReefKnowledgeChunk]:
        """
        Search for content and scrape result snippets.
        
        Args:
            query: The search term (e.g., "calcium reactor setup")
            max_results: Maximum number of results to retrieve
            
        Returns:
            List of knowledge chunks from search results
        """
        chunks = []
        
        # Use DuckDuckGo HTML search
        search_url = f"https://html.duckduckgo.com/html/?q={query}&b={max_results}"
        
        try:
            response = self.session.get(search_url, timeout=15)
            if response.status_code != 200:
                return chunks
            
            # Parse HTML to extract search results
            import bs4
            soup = bs4.BeautifulSoup(response.text, 'html.parser')
            
            # Extract result snippets from search results
            for result in soup.find_all('a', class_='result__snippet'):
                url = result.get('href', '')
                if url and 'http' in url:
                    text = result.get_text()
                    if len(text) > 100:
                        # Create a knowledge chunk from the result
                        chunk = ReefKnowledgeChunk(
                            content=text,
                            source="web_search",
                            url=url,
                            title=query,  # Use query as title
                            topic="search",
                            timestamp=datetime.now().isoformat(),
                            chunk_id=hashlib.md5((text + url).encode()).hexdigest()[:16],
                        )
                        chunks.append(chunk)
        
        except Exception as e:
            print(f"Search error for {query}: {e}")
        
        return chunks
    
    def run(self) -> List[ReefKnowledgeChunk]:
        """
        Run web search for all reef-related queries.
        
        This searches for 105 different reef aquarium topics
        to build a comprehensive knowledge base.
        
        Returns:
            All knowledge chunks found from searches
        """
        all_chunks = []
        
        # 105 search queries covering all reef aquarium topics
        search_queries = [
            # Water Parameters (core chemistry) - 15 queries
            ("reef tank calcium alkalinity magnesium balance", 40),
            ("magnesium reef tank ideal level", 30),
            ("reef tank pH low high problem", 35),
            ("reef tank salinity specific gravity", 25),
            ("reef tank nitrate phosphate control", 35),
            ("reef tank dKH alkalinity ideal range", 30),
            ("calcium reef tank 400 ppm", 25),
            ("magnesium reef 1300 1400 ppm", 20),
            ("reef tank salinity 1.025 specific gravity", 20),
            ("nitrate phosphate reef tank too high", 30),
            ("reef tank ammonia nitrite control", 25),
            ("red sea vs salifert test kit", 20),
            ("reef tank ORP level", 20),
            ("reef tank redox potential", 15),
            ("reef tank dissolved oxygen", 20),
            
            # Equipment - 20 queries
            ("calcium reactor setup guide reef", 40),
            ("dosing pump reef aquarium setup", 35),
            ("protein skimmer tuning guide", 30),
            ("reef tank heater controller", 25),
            ("reef lighting PAR requirements", 30),
            ("reef tank return pump size", 20),
            ("reef tank powerhead flow rate", 25),
            ("reef tank wavemaker placement", 20),
            ("auto top off reef aquarium", 30),
            ("reef tank UV sterilizer use", 25),
            ("reef tank ozone generator", 20),
            ("reef tank chiller size", 25),
            ("reef tank RO/DI filter", 25),
            ("reef tank sump design", 25),
            ("reef tank refugium setup", 25),
            ("reef tank dosing manifold", 20),
            ("balling method reef dosing", 30),
            ("kalkwasser reactor reef", 25),
            ("reef tank calcium dosage", 25),
            ("reef tank doser pump", 25),
            
            # Maintenance - 15 queries
            ("reef tank water change frequency", 35),
            ("reef tank maintenance schedule", 30),
            ("how to test reef water parameters", 30),
            ("reef tank weekly maintenance", 25),
            ("reef tank monthly maintenance", 25),
            ("reef tank water change percentage", 30),
            ("reef tank filter cleaning", 20),
            ("reef tank glass cleaning", 20),
            ("reef tank sand bed cleaning", 20),
            ("reef tank skimmer cup cleaning", 20),
            ("reef tank pump cleaning", 20),
            ("reef tank hose cleaning", 15),
            ("reef tank water top off", 25),
            ("reef tank evaporation", 20),
            ("reef tank salinity drift", 20),
            
            # Corals - 15 queries
            ("SPS coral care reef tank", 30),
            ("LPS coral placement guide", 25),
            ("reef coral fragging techniques", 30),
            ("zoanthid coral care", 25),
            ("soft coral reef tank", 25),
            ("reef coral feeding", 25),
            ("coral dip guide reef", 30),
            ("acclimate new coral reef", 25),
            ("reef coral growth rate", 20),
            ("coral color reef lighting", 25),
            ("reef coral frag trade", 20),
            ("coral placement reef tank", 25),
            ("SPS vs LPS reef coral", 25),
            ("reef coral compatibility", 20),
            ("coral predation reef", 20),
            
            # Troubleshooting - 20 queries
            ("reef tank algae control", 30),
            ("coral bleaching prevention", 30),
            ("reef tank pest identification", 30),
            ("reef tank brown algae", 25),
            ("reef tank green algae", 25),
            ("hair algae reef tank", 25),
            ("red slime algae reef", 25),
            ("reef tank ich treatment", 30),
            ("velvet disease reef fish", 25),
            ("brooklynella reef parasite", 25),
            ("reef tank coral died", 25),
            ("coral receding reef", 20),
            ("reef tank coral closed", 20),
            ("reef tank fish hiding", 20),
            ("reef tank fish aggressive", 20),
            ("reef tank not eating", 20),
            ("reef tank swimming erratically", 15),
            ("reef tank flashing fish", 15),
            ("reef tank slimy fish", 20),
            ("reef tank fungal infection", 25),
            
            # General/Flow - 20 queries
            ("new reef tank setup guide", 35),
            ("reef tank cycling process", 30),
            ("reef tank nitrogen cycle", 30),
            ("reef tank fish only vs reef", 25),
            ("mini reef tank setup", 30),
            ("reef tank substrate sand", 25),
            ("live rock reef tank", 30),
            ("reef tank biological filter", 25),
            ("reef tank sump filter", 25),
            ("reef tank protein skimmers", 30),
            ("reef tank equipment list", 25),
            ("budget reef tank setup", 25),
            ("reef tank cost estimate", 20),
            ("reef tank beginner mistake", 25),
            ("reef tank order to add fish", 25),
            ("reef tank stocking level", 25),
            ("reef tank fish compatibility list", 25),
            ("reef tank coral placement guide", 25),
            ("reef tank flow map", 20),
            ("reef tank light schedule", 25),
            ("reef tank photoperiod", 25),
        ]
        
        for query, max_results in search_queries:
            print(f"Searching: {query}")
            try:
                chunks = self.search_and_scrape(query, max_results)
                all_chunks.extend(chunks)
            except Exception as e:
                print(f"  Error: {e}")
            time.sleep(1)  # Rate limiting to avoid being blocked
        
        return all_chunks


# ============================================================================
# VECTOR DATABASE
# ============================================================================

class VectorKnowledgeBase:
    """
    Vector database for reef knowledge using Supabase pgvector.
    """
    
    def __init__(self):
        self.supabase: Client = create_client(
            os.environ.get("SUPABASE_URL", ""),
            os.environ.get("SUPABASE_KEY", "")
        )
        self.gemini_key = os.environ.get("GEMINI_API_KEY", "")
    
    def _get_gemini_embedding(self, text: str) -> List[float]:
        if not self.gemini_key:
            print("Error: GEMINI_API_KEY not found.")
            return []
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-2:embedContent?key={self.gemini_key}"
        headers = {"Content-Type": "application/json"}
        data = {
            "model": "models/gemini-embedding-2",
            "content": {
                "parts": [{"text": text}]
            }
        }
        try:
            import requests
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            return result.get("embedding", {}).get("values", [])
        except Exception as e:
            print(f"Gemini Embedding Error: {e}")
            return []
    
    def _normalize(self, vectors: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        return vectors / norms
    
    def add_chunks(self, chunks: List[ReefKnowledgeChunk]):
        if not chunks:
            return
            
        print(f"Embedding {len(chunks)} chunks with Gemini...")
        
        data_to_insert = []
        for i, chunk in enumerate(chunks):
            embedding = self._get_gemini_embedding(chunk.content)
            if not embedding:
                continue
                
            data_to_insert.append({
                "content": chunk.content,
                "source": chunk.source,
                "topic": chunk.title,
                "embedding": embedding
            })
            time.sleep(4.1) # 15 RPM limit for free tier
            
        print("Uploading to Supabase pgvector...")
        # Batch insert to avoid payload size limits
        batch_size = 50
        for i in range(0, len(data_to_insert), batch_size):
            batch = data_to_insert[i:i + batch_size]
            try:
                self.supabase.table("reef_knowledge").insert(batch).execute()
            except Exception as e:
                print(f"Error inserting batch: {e}")
                
        print("Upload complete!")
    
    def save(self):
        # Deprecated: Supabase saves instantly
        pass
    
    def search(self, query: str, k: int = 5) -> List[Dict]:
        query_vec = self._get_gemini_embedding(query)
        if not query_vec:
            return []
        
        try:
            response = self.supabase.rpc("match_knowledge", {
                "query_embedding": query_vec,
                "match_threshold": 0.1,
                "match_count": k
            }).execute()
            
            results = []
            if response.data:
                for item in response.data:
                    results.append({
                        "content": item.get("content", ""),
                        "source": item.get("source", ""),
                        "title": item.get("topic", "Unknown"),
                        "score": item.get("similarity", 0.0)
                    })
            return results
        except Exception as e:
            print(f"Supabase RPC Error: {e}")
            return []


# ============================================================================
# PUBLIC FUNCTIONS
# ============================================================================

def create_vector_db():
    """
    Initialize the vector database with reef knowledge.
    """
    kb = VectorKnowledgeBase()
    
    # Try to load existing local chunks first to avoid rate-limiting
    meta_path = os.path.join(os.path.dirname(__file__), "reef_knowledge_meta.json")
    if os.path.exists(meta_path):
        print(f"Found existing local knowledge chunks in {meta_path}. Loading...")
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            chunks = []
            for item in data:
                chunk = ReefKnowledgeChunk(
                    content=item.get("content", ""),
                    source=item.get("source", "local_json"),
                    url=item.get("url", ""),
                    title=item.get("title", "Unknown"),
                    topic=item.get("topic", "general"),
                    timestamp=item.get("timestamp", datetime.now().isoformat()),
                    chunk_id=item.get("chunk_id", hashlib.md5(item.get("content", "").encode()).hexdigest()[:16])
                )
                chunks.append(chunk)
            
            if chunks:
                print(f"Loaded {len(chunks)} chunks from local file. Uploading to Supabase...")
                kb.add_chunks(chunks)
                kb.save()
                return kb
        except Exception as e:
            print(f"Error loading local chunks: {e}")

    # Fallback to scraping
    print("Initiating Web Search Scraper...")
    web_scraper = WebSearchScraper()
    chunks = web_scraper.run()
    
    if chunks:
        kb.add_chunks(chunks)
        kb.save()
        return kb
    
    return kb


# Global instance to prevent reloading the PyTorch model on every request
GLOBAL_KB = None

def get_global_kb():
    global GLOBAL_KB
    if GLOBAL_KB is None:
        print("Initializing Global Vector Database (Gemini API)...")
        GLOBAL_KB = VectorKnowledgeBase()
    return GLOBAL_KB

def get_vector_context(query: str, k: int = 5) -> str:
    """
    Get contextual information from vector database for RAG.
    
    This is the main function called by the /chat endpoint
    to inject relevant knowledge into the LLM prompt.
    
    Args:
        query: The user's question
        k: Number of context chunks to retrieve
        
    Returns:
        Formatted context string for the LLM prompt
    """
    kb = get_global_kb()
    results = kb.search(query, k=k)
    
    if not results:
        return ""
    
    # Format as markdown for the prompt
    context_parts = ["## Relevant Reef Knowledge"]
    
    for i, result in enumerate(results[:k]):
        context_parts.append(f"\n### {i+1}. {result.get('title', 'Unknown')}")
        context_parts.append(f"Source: {result.get('source', 'Unknown')}")
        context_parts.append(result.get('content', '')[:500])
    
    return "\n".join(context_parts)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "init":
        print("Initializing Supabase pgvector database...")
        print("(This will take a few minutes on first run)")
        kb = create_vector_db()
        print(f"\nVector database seeded into Supabase!")
        print(f"Run: get_vector_context('your question') to search")
    else:
        print("Testing vector search...")
        print("Usage: python vector_db.py init")
        
        # Quick test
        kb = VectorKnowledgeBase()
        results = kb.search("calcium reactor setup", k=3)
        if results:
            print(f"\nFound {len(results)} results:")
            for r in results:
                print(f"  - {r.get('title')}: {r.get('content')[:80]}...")
        else:
            print("No vectors found. Run: python vector_db.py init")