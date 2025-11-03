"""
Qdrant Storage Module for Disaster Tweets
==========================================
Standalone module to add vector search capabilities to your disaster tweet pipeline.

Why use this?
- Semantic search: Find tweets by meaning, not just keywords
- Similarity detection: Find duplicate reports or related incidents
- Real-time queries: Search stored tweets instantly by location, severity, type
- Trend analysis: Find patterns across similar disaster events

Usage:
    from qdrant_storage import QdrantManager
    
    # Initialize
    qdrant = QdrantManager()
    
    # Store tweets from your pipeline
    qdrant.store_from_file('pipeline_output/04_final_results.jsonl')
    
    # Search
    results = qdrant.search("earthquake in California")
    results = qdrant.search_by_location("Tokyo", disaster_type="earthquake")
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance, VectorParams, PointStruct, 
        Filter, FieldCondition, MatchValue, Range
    )
    from sentence_transformers import SentenceTransformer
    QDRANT_AVAILABLE = True
except ImportError:
    print("⚠️  Qdrant dependencies not installed")
    print("Run: pip install qdrant-client sentence-transformers")
    QDRANT_AVAILABLE = False

load_dotenv()


class QdrantManager:
    """
    Manage disaster tweets in Qdrant vector database.
    
    Features:
    - Store tweets with semantic embeddings
    - Search by meaning (not just keywords)
    - Filter by disaster type, location, severity
    - Find similar incidents
    """
    
    def __init__(self, 
                 url: str = None,
                 api_key: str = None,
                 collection_name: str = "disaster_tweets",
                 embedding_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize Qdrant manager.
        
        Args:
            url: Qdrant server URL (default: from QDRANT_URL env or localhost)
            api_key: Qdrant API key (default: from QDRANT_API_KEY env)
            collection_name: Name of the collection
            embedding_model: Sentence transformer model for embeddings
        """
        if not QDRANT_AVAILABLE:
            raise ImportError(
                "Qdrant dependencies not installed. "
                "Run: pip install qdrant-client sentence-transformers"
            )
        
        self.url = url or os.getenv('QDRANT_URL', 'http://localhost:6333')
        self.api_key = api_key or os.getenv('QDRANT_API_KEY')
        self.collection_name = collection_name
        
        # Connect to Qdrant
        print(f"Connecting to Qdrant at {self.url}...")
        self.client = QdrantClient(url=self.url, api_key=self.api_key)
        
        # Load embedding model
        print(f"Loading embedding model: {embedding_model}...")
        self.encoder = SentenceTransformer(embedding_model)
        
        print("✓ Connected to Qdrant\n")
    
    def create_collection(self, recreate: bool = False):
        """
        Create the collection (or recreate if it exists).
        
        Args:
            recreate: If True, delete existing collection and create new one
        """
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)
        
        if exists:
            if recreate:
                print(f"Deleting existing collection '{self.collection_name}'...")
                self.client.delete_collection(self.collection_name)
            else:
                print(f"Collection '{self.collection_name}' already exists (use recreate=True to reset)")
                return
        
        # Get vector size from model
        vector_size = self.encoder.get_sentence_embedding_dimension()
        
        # Create collection
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE  # Cosine similarity
            )
        )
        
        print(f"✓ Created collection '{self.collection_name}' (vector size: {vector_size})\n")
    
    def store_tweets(self, tweets: List[Dict]) -> int:
        """
        Store tweets in Qdrant with semantic embeddings.
        
        Args:
            tweets: List of tweet dictionaries from your pipeline
            
        Returns:
            Number of tweets stored
        """
        print(f"Storing {len(tweets)} tweets in Qdrant...")
        
        points = []
        for tweet in tweets:
            # Create embedding from tweet text
            text = tweet.get('text', '')
            if not text:
                continue
            
            vector = self.encoder.encode(text).tolist()
            
            # Prepare payload with all metadata
            ml_cls = tweet.get('ml_classification', {})
            llm_ext = tweet.get('llm_extraction', {})
            
            payload = {
                # Basic info
                'id': tweet.get('id'),
                'text': text,
                'author': tweet.get('author', {}).get('handle'),
                'created_at': tweet.get('createdAt'),
                
                # ML classification
                'is_disaster': ml_cls.get('is_disaster', False),
                'disaster_type': ml_cls.get('disaster_type'),
                'confidence': ml_cls.get('confidence', 0.0),
                
                # LLM extraction (if available)
                'location': llm_ext.get('location') if llm_ext else None,
                'severity': llm_ext.get('severity') if llm_ext else None,
                'casualties_mentioned': llm_ext.get('casualties_mentioned', False) if llm_ext else False,
                'damage_mentioned': llm_ext.get('damage_mentioned', False) if llm_ext else False,
                'needs_help': llm_ext.get('needs_help', False) if llm_ext else False,
                'key_details': llm_ext.get('key_details') if llm_ext else None,
                
                # Engagement metrics
                'like_count': tweet.get('like_count', 0),
                'reply_count': tweet.get('reply_count', 0),
                'repost_count': tweet.get('repost_count', 0),
            }
            
            # Create point with unique ID
            point = PointStruct(
                id=abs(hash(tweet.get('id', ''))) % (10 ** 10),  # Convert to positive int
                vector=vector,
                payload=payload
            )
            points.append(point)
        
        # Upload in batches
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            self.client.upsert(
                collection_name=self.collection_name,
                points=batch
            )
            if len(points) > batch_size:
                print(f"  Uploaded {min(i + batch_size, len(points))}/{len(points)} tweets")
        
        print(f"✓ Stored {len(points)} tweets in Qdrant\n")
        return len(points)
    
    def store_from_file(self, filepath: str) -> int:
        """
        Load tweets from JSONL file and store in Qdrant.
        
        Args:
            filepath: Path to JSONL file (e.g., '04_final_results.jsonl')
            
        Returns:
            Number of tweets stored
        """
        print(f"Loading tweets from {filepath}...")
        
        tweets = []
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    tweets.append(json.loads(line))
        
        print(f"Loaded {len(tweets)} tweets\n")
        
        # Ensure collection exists
        collections = self.client.get_collections().collections
        if not any(c.name == self.collection_name for c in collections):
            self.create_collection()
        
        return self.store_tweets(tweets)
    
    def search(self, query: str, limit: int = 10, 
               min_confidence: float = 0.0) -> List[Dict]:
        """
        Search for tweets by semantic similarity.
        
        Args:
            query: Search query (e.g., "earthquake in California")
            limit: Maximum number of results
            min_confidence: Minimum ML confidence score (0-1)
            
        Returns:
            List of matching tweets with similarity scores
        """
        # Create query embedding
        query_vector = self.encoder.encode(query).tolist()
        
        # Build filter
        filter_conditions = None
        if min_confidence > 0:
            filter_conditions = Filter(
                must=[
                    FieldCondition(
                        key="confidence",
                        range=Range(gte=min_confidence)
                    )
                ]
            )
        
        # Search
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit,
            query_filter=filter_conditions
        )
        
        return [self._format_result(hit) for hit in results]
    
    def search_by_type(self, disaster_type: str, limit: int = 10) -> List[Dict]:
        """
        Find all tweets of a specific disaster type.
        
        Args:
            disaster_type: Type (e.g., "earthquake", "flood")
            limit: Maximum results
        """
        results = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="disaster_type",
                        match=MatchValue(value=disaster_type)
                    )
                ]
            ),
            limit=limit
        )
        
        return [self._format_result(hit) for hit in results[0]]
    
    def search_by_location(self, location: str, 
                          disaster_type: Optional[str] = None,
                          limit: int = 10) -> List[Dict]:
        """
        Search for disasters in a specific location.
        
        Args:
            location: Location name (e.g., "California", "Tokyo")
            disaster_type: Optional filter by disaster type
            limit: Maximum results
        """
        # Create query from location
        query = f"disaster in {location}"
        query_vector = self.encoder.encode(query).tolist()
        
        # Build filter
        conditions = []
        if disaster_type:
            conditions.append(
                FieldCondition(
                    key="disaster_type",
                    match=MatchValue(value=disaster_type)
                )
            )
        
        filter_conditions = Filter(must=conditions) if conditions else None
        
        # Search
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit,
            query_filter=filter_conditions
        )
        
        # Further filter by location in text or extracted location
        filtered = []
        location_lower = location.lower()
        for hit in results:
            text = hit.payload.get('text', '').lower()
            extracted_loc = (hit.payload.get('location') or '').lower()
            
            if location_lower in text or location_lower in extracted_loc:
                filtered.append(self._format_result(hit))
        
        return filtered
    
    def find_similar(self, tweet_text: str, limit: int = 5) -> List[Dict]:
        """
        Find tweets similar to a given tweet.
        
        Useful for:
        - Finding duplicate reports
        - Detecting related incidents
        - Grouping similar events
        
        Args:
            tweet_text: Text of the tweet to find similar ones
            limit: Maximum results
        """
        return self.search(tweet_text, limit=limit)
    
    def get_stats(self) -> Dict:
        """Get statistics about stored tweets."""
        collection_info = self.client.get_collection(self.collection_name)
        
        # Get disaster type distribution
        disaster_types = {}
        for dtype in ['earthquake', 'flood', 'hurricane', 'wildfire', 'tornado']:
            results = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="disaster_type",
                            match=MatchValue(value=dtype)
                        )
                    ]
                ),
                limit=1,
                with_payload=False
            )
            # Count is approximate
            disaster_types[dtype] = len(results[0])
        
        return {
            'total_tweets': collection_info.points_count,
            'vector_size': collection_info.config.params.vectors.size,
            'distance_metric': collection_info.config.params.vectors.distance.name,
            'disaster_type_counts': disaster_types
        }
    
    def _format_result(self, hit) -> Dict:
        """Format search result for display."""
        return {
            'similarity_score': hit.score if hasattr(hit, 'score') else 1.0,
            'text': hit.payload.get('text'),
            'disaster_type': hit.payload.get('disaster_type'),
            'location': hit.payload.get('location'),
            'severity': hit.payload.get('severity'),
            'confidence': hit.payload.get('confidence'),
            'needs_help': hit.payload.get('needs_help'),
            'casualties_mentioned': hit.payload.get('casualties_mentioned'),
            'damage_mentioned': hit.payload.get('damage_mentioned'),
            'author': hit.payload.get('author'),
            'created_at': hit.payload.get('created_at'),
            'like_count': hit.payload.get('like_count', 0),
            'reply_count': hit.payload.get('reply_count', 0)
        }


# ============================================================================
# EXAMPLE USAGE & CLI
# ============================================================================

def example_usage():
    """Example usage of QdrantManager"""
    
    # Initialize
    qdrant = QdrantManager()
    
    # Create collection
    qdrant.create_collection(recreate=True)
    
    # Store tweets from pipeline output
    qdrant.store_from_file('pipeline_output/04_final_results.jsonl')
    
    # Example searches
    print("\n" + "="*70)
    print("EXAMPLE SEARCHES")
    print("="*70 + "\n")
    
    # 1. Semantic search
    print("1. Search: 'buildings collapsed from earthquake'")
    print("-" * 70)
    results = qdrant.search("buildings collapsed from earthquake", limit=3)
    for i, r in enumerate(results, 1):
        print(f"{i}. [{r['disaster_type']}] Similarity: {r['similarity_score']:.3f}")
        print(f"   {r['text'][:100]}...")
        if r['location']:
            print(f"   📍 {r['location']}")
        print()
    
    # 2. Search by location
    print("\n2. Disasters in California")
    print("-" * 70)
    results = qdrant.search_by_location("California", limit=3)
    for i, r in enumerate(results, 1):
        print(f"{i}. [{r['disaster_type']}] {r['text'][:80]}...")
    
    # 3. Search by type
    print("\n3. All earthquakes")
    print("-" * 70)
    results = qdrant.search_by_type("earthquake", limit=3)
    for i, r in enumerate(results, 1):
        print(f"{i}. {r['text'][:80]}...")
    
    # Stats
    print("\n" + "="*70)
    print("DATABASE STATS")
    print("="*70)
    stats = qdrant.get_stats()
    print(f"Total tweets: {stats['total_tweets']}")
    print(f"Disaster types: {stats['disaster_type_counts']}")


def main():
    """CLI for Qdrant storage"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Store and search disaster tweets in Qdrant'
    )
    parser.add_argument(
        'action',
        choices=['store', 'search', 'stats', 'example'],
        help='Action to perform'
    )
    parser.add_argument(
        '--file', '-f',
        type=str,
        default='pipeline_output/04_final_results.jsonl',
        help='Path to tweets JSONL file (for store action)'
    )
    parser.add_argument(
        '--query', '-q',
        type=str,
        help='Search query (for search action)'
    )
    parser.add_argument(
        '--type', '-t',
        type=str,
        help='Disaster type filter'
    )
    parser.add_argument(
        '--location', '-l',
        type=str,
        help='Location filter'
    )
    parser.add_argument(
        '--limit', '-n',
        type=int,
        default=10,
        help='Maximum results (default: 10)'
    )
    parser.add_argument(
        '--recreate',
        action='store_true',
        help='Recreate collection (for store action)'
    )
    
    args = parser.parse_args()
    
    # Initialize
    qdrant = QdrantManager()
    
    if args.action == 'store':
        qdrant.create_collection(recreate=args.recreate)
        qdrant.store_from_file(args.file)
    
    elif args.action == 'search':
        if not args.query:
            print("Error: --query required for search")
            return
        
        if args.location:
            results = qdrant.search_by_location(
                args.location,
                disaster_type=args.type,
                limit=args.limit
            )
        elif args.type:
            results = qdrant.search_by_type(args.type, limit=args.limit)
        else:
            results = qdrant.search(args.query, limit=args.limit)
        
        print(f"\nFound {len(results)} results:\n")
        for i, r in enumerate(results, 1):
            print(f"{i}. [{r['disaster_type']}] Score: {r['similarity_score']:.3f}")
            print(f"   {r['text']}")
            if r['location']:
                print(f"   📍 {r['location']}")
            if r['severity']:
                print(f"   ⚠️  Severity: {r['severity']}")
            print()
    
    elif args.action == 'stats':
        stats = qdrant.get_stats()
        print("\n" + "="*50)
        print("QDRANT DATABASE STATS")
        print("="*50)
        print(f"\nTotal tweets: {stats['total_tweets']}")
        print(f"Vector size: {stats['vector_size']}")
        print(f"Distance metric: {stats['distance_metric']}")
        print(f"\nDisaster types:")
        for dtype, count in stats['disaster_type_counts'].items():
            print(f"  {dtype:12s}: {count}")
        print()
    
    elif args.action == 'example':
        example_usage()


if __name__ == "__main__":
    main()