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
import faiss  # Facebook AI Similarity Search - vector database
from sentence_transformers import SentenceTransformer  # Text embeddings

# Check if torch is available (used by sentence_transformers)
try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


# ============================================================================
# CONFIGURATION
# ============================================================================

# Get the directory where this script is located for relative file paths
# This ensures the index files are stored next to the script
SCRIPT_DIR = os.path.dirname(__file__)

# File paths for the vector index and metadata
# - INDEX_FILE: The FAISS vector index (binary file)
# - METADATA_FILE: JSON file with text content for each vector
INDEX_FILE = os.path.join(SCRIPT_DIR, "reef_knowledge.index")
METADATA_FILE = os.path.join(SCRIPT_DIR, "reef_knowledge_meta.json")

# Embedding dimension for All-MiniLM-L6-v2 model
# This is the size of the vector that represents each text chunk
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
    Vector database for reef knowledge using FAISS.
    
    FAISS (Facebook AI Similarity Search) is a library for efficient
    similarity search of dense vectors. It allows us to:
    
    1. Store embeddings (numerical representations of text)
    2. Search by semantic similarity (not just keywords)
    3. Scale to millions of vectors
    
    How it works:
    1. Each text chunk is converted to a 384-dimensional vector
    2. Vectors are stored in a FAISS index
    3. To search, we convert the query to a vector
    4. FAISS finds the closest vectors (most similar text)
    """
    
    def __init__(self, index_path: str = INDEX_FILE, meta_path: str = METADATA_FILE):
        """
        Initialize the vector knowledge base.
        
        Args:
            index_path: Path to the FAISS index file
            meta_path: Path to the metadata JSON file
        """
        self.index_path = index_path
        self.meta_path = meta_path
        self.index: Optional[faiss.IndexFlatIP] = None
        self.metadata: List[Dict] = []
        self.model: Optional[SentenceTransformer] = None
        self._load()  # Try to load existing index
    
    def _load_model(self):
        """Load the sentence transformer model for embeddings."""
        if self.model is None:
            print("Loading embedding model...")
            # All-MiniLM-L6-v2 creates 384-dimensional embeddings
            # It's fast and produces good results for semantic search
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            print("Model loaded")
    
    def _load(self):
        """
        Load existing index and metadata from disk.
        
        Called automatically on initialization to resume previous work.
        """
        # Try to load FAISS index
        if os.path.exists(self.index_path):
            try:
                self.index = faiss.read_index(self.index_path)
                print(f"Loaded index with {self.index.ntotal} vectors")
            except Exception as e:
                print(f"Could not load index: {e}")
                self.index = None
        
        # Try to load metadata
        if os.path.exists(self.meta_path):
            try:
                with open(self.meta_path, 'r') as f:
                    self.metadata = json.load(f)
                print(f"Loaded {len(self.metadata)} metadata entries")
            except Exception as e:
                print(f"Could not load metadata: {e}")
                self.metadata = []
    
    def _normalize(self, vectors: np.ndarray) -> np.ndarray:
        """
        Normalize vectors for cosine similarity.
        
        Cosine similarity measures how similar two vectors are
        by the angle between them (not magnitude).
        This is important for semantic search.
        """
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)  # Avoid division by zero
        return vectors / norms
    
    def add_chunks(self, chunks: List[ReefKnowledgeChunk]):
        """
        Add knowledge chunks to the vector database.
        
        This:
        1. Converts each text chunk to a vector (embedding)
        2. Normalizes the vectors
        3. Adds them to the FAISS index
        4. Stores metadata for retrieval
        
        Args:
            chunks: List of knowledge chunks to add
        """
        if not chunks:
            return
        
        self._load_model()
        
        # Extract text content from chunks
        texts = [chunk.content for chunk in chunks]
        print(f"Embedding {len(texts)} chunks...")
        
        # Convert text to vectors using the transformer model
        vectors = self.model.encode(texts, show_progress_bar=True)
        vectors = vectors.astype('float32')
        vectors = self._normalize(vectors)
        
        # Get the dimension of the vectors
        dim = vectors.shape[1]
        
        # Create index if needed (IndexFlatIP = inner product for cosine similarity)
        if self.index is None:
            self.index = faiss.IndexFlatIP(dim)
        
        # Add vectors to the index
        self.index.add(vectors)
        
        # Store metadata for retrieval
        for chunk in chunks:
            self.metadata.append(chunk.to_dict())
        
        print(f"Total vectors: {self.index.ntotal}")
    
    def save(self):
        """
        Save index and metadata to disk for later use.
        
        This allows us to load the database without re-scraping.
        """
        if self.index:
            faiss.write_index(self.index, self.index_path)
            print(f"Saved index to {self.index_path}")
        
        with open(self.meta_path, 'w') as f:
            json.dump(self.metadata, f, indent=2)
            print(f"Saved {len(self.metadata)} metadata entries")
    
    def search(self, query: str, k: int = 5) -> List[Dict]:
        """
        Search for relevant knowledge chunks.
        
        This is the core function that enables RAG (Retrieval-Augmented Generation).
        
        Args:
            query: The user's question
            k: Number of results to return
            
        Returns:
            List of relevant knowledge chunks with scores
        """
        if self.index is None or self.index.ntotal == 0:
            return []
        
        self._load_model()
        
        # Convert query to embedding
        query_vec = self.model.encode([query]).astype('float32')
        query_vec = self._normalize(query_vec)
        
        # Search for k most similar vectors
        # Returns both scores (similarity) and indices
        scores, indices = self.index.search(query_vec, min(k, self.index.ntotal))
        
        # Build results from metadata
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and idx < len(self.metadata):
                result = self.metadata[idx].copy()
                result['score'] = float(score)
                results.append(result)
        
        return results


# ============================================================================
# PUBLIC FUNCTIONS
# ============================================================================

def create_vector_db():
    """
    Initialize the vector database with reef knowledge.
    """
    kb = VectorKnowledgeBase()
    
    # We skip direct scraping because forums block it with 403 Forbidden.
    # Instead, we rely entirely on DuckDuckGo web search.
    print("Initiating Web Search Scraper...")
    web_scraper = WebSearchScraper()
    chunks = web_scraper.run()
    
    if chunks:
        kb.add_chunks(chunks)
        kb.save()
        return kb
    
    # If internet is down or search fails, add seed data from scraper.py
    try:
        from scraper import MANUAL_KNOWLEDGE
        seed_chunks = []
        for issue, info in MANUAL_KNOWLEDGE.items():
            content_parts = []
            if info.get("treatments"):
                content_parts.append("Treatments: " + ", ".join(info["treatments"]))
            if info.get("references"):
                content_parts.append("References: " + ", ".join(info["references"]))
            
            if content_parts:
                chunk = ReefKnowledgeChunk(
                    content=". ".join(content_parts),
                    source="seed_knowledge",
                    url="",
                    title=issue.replace("_", " ").title(),
                    topic=issue,
                    timestamp=datetime.now().isoformat(),
                    chunk_id=hashlib.md5(issue.encode()).hexdigest()[:16],
                )
                seed_chunks.append(chunk)
        
        kb.add_chunks(seed_chunks)
        kb.save()
    except ImportError:
        print("Failed to load seed data from scraper.py")
        
    return kb


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
        
    Usage:
        context = get_vector_context("How do I raise pH?", k=3)
        # Returns:
        # ## Relevant Reef Knowledge
        # 
        # ### 1. reef aquarium ph troubleshooting
        # Source: web_search
        # If you have suppressed pH in your reef tank (7.7 to 7.9)...
    """
    kb = VectorKnowledgeBase()
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
        print("Initializing vector database...")
        print("(This will take a few minutes on first run)")
        kb = create_vector_db()
        print(f"\nVector database ready with {kb.index.ntotal} vectors")
        print(f"Run: get_vector_context('your question') to search")
    else:
        print("Testing vector search...")
        print("Usage: python vector_db.py init")
        
        # Quick test
        kb = VectorKnowledgeBase()
        if kb.index and kb.index.ntotal > 0:
            results = kb.search("calcium reactor setup", k=3)
            print(f"\nFound {len(results)} results:")
            for r in results:
                print(f"  - {r.get('title')}: {r.get('content')[:80]}...")
        else:
            print("No vectors found. Run: python vector_db.py init")