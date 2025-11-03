"""
Unified Disaster Tweet Pipeline
================================
Complete pipeline that:
1. Fetches tweets from Bluesky
2. Cleans and formats them
3. Classifies them with XGBoost
4. Extracts detailed info with LLM
5. Store in Qdrant DB
"""

import os
import json
import re
import hashlib
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
import numpy as np
from collections import Counter

# Third-party imports
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from typing import TypedDict
import joblib
from sentence_transformers import SentenceTransformer
from qdrant_client.models import PointStruct
from qdrant_client import QdrantClient
from qdrant_client.http import models
import uuid

# Try to import Bluesky client - adjust based on your actual import
try:
    from atproto import Client
    BLUESKY_AVAILABLE = True
except ImportError:
    print("Warning: atproto not installed. Bluesky fetching will be disabled.")
    BLUESKY_AVAILABLE = False

load_dotenv()


# ============================================================================
# CONFIGURATION
# ============================================================================

class PipelineConfig:
    """Configuration for the entire pipeline"""
    
    # Bluesky settings (using Elijah's env variable names)
    BLUESKY_HANDLE = os.getenv('BLUESKY_IDENTIFIER', '')
    BLUESKY_PASSWORD = os.getenv('BLUESKY_PWD', '')
    
    # Search queries for different disaster types
    DISASTER_QUERIES = [
        "earthquake",
        "flood",
        "wildfire", 
        "hurricane"
    ]
    
    # Maximum total posts to fetch
    MAX_POSTS = 500
    
    # ML Model paths
    MODEL_PATH = "xgboost_model_20251018_093203.joblib"
    VECTORIZER_PATH = "xgboost_vectorizer_20251018_093203.joblib"
    CONFIG_PATH = "xgboost_config_20251018_093203.json"
    LABEL_ENCODER_PATH = "label_encoder_20251018_093203.joblib"
    
    # LLM settings
    HF_TOKEN = os.getenv('HF_TOKEN', '')
    LLM_MODEL = "meta-llama/Llama-3.1-8B-Instruct:novita"
    RATE_LIMIT_DELAY = 1.0  # seconds between LLM calls
    
    # Output paths
    OUTPUT_DIR = Path("pipeline_output")
    RAW_TWEETS_FILE = OUTPUT_DIR / "01_raw_tweets.jsonl"
    CLEANED_TWEETS_FILE = OUTPUT_DIR / "02_cleaned_tweets.jsonl"
    CLASSIFIED_TWEETS_FILE = OUTPUT_DIR / "03_classified_tweets.jsonl"
    FINAL_OUTPUT_FILE = OUTPUT_DIR / "04_final_results.jsonl"


# ============================================================================
# STEP 1: FETCH TWEETS FROM BLUESKY
# ============================================================================

class BlueskyFetcher:
    """Fetch disaster-related tweets from Bluesky (based on Elijah's code)"""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.client = None
        
    def connect(self):
        """Connect to Bluesky"""
        if not BLUESKY_AVAILABLE:
            raise ImportError("atproto not installed. Run: pip install atproto")
        
        print("Connecting to Bluesky...")
        self.client = Client()
        self.client.login(self.config.BLUESKY_HANDLE, self.config.BLUESKY_PASSWORD)
        print(f"✓ Logged in as: {self.client.me.handle}\n")
    
    def fetch_tweets(self) -> List[Dict]:
        """Fetch tweets for all disaster queries"""
        if not self.client:
            self.connect()
        
        all_tweets = []
        total_posts = 0
        MAX_POSTS = self.config.MAX_POSTS
        
        for keyword in self.config.DISASTER_QUERIES:
            if total_posts >= MAX_POSTS:
                print(f"✓ Reached maximum post limit of {MAX_POSTS}")
                break
            
            print(f"Searching for posts with keyword: {keyword}")
            posts_needed = MAX_POSTS - total_posts
            limit = min(posts_needed, 100)  # API max is 100
            
            try:
                # Search for posts
                results = self.client.app.bsky.feed.search_posts(
                    params={
                        'q': keyword,
                        'limit': limit
                    }
                )
                
                for post in results.posts:
                    if total_posts >= MAX_POSTS:
                        break
                    
                    if hasattr(post.record, 'text') and post.record.text:
                        # Convert post to dict (matching Elijah's format)
                        post_dict = {
                            'text': post.record.text,
                            'uri': post.uri,
                            'cid': post.cid,
                            'author': {
                                'handle': post.author.handle,
                                'display_name': post.author.display_name
                            },
                            'created_at': post.record.created_at,
                            'like_count': post.like_count if hasattr(post, 'like_count') else 0,
                            'reply_count': post.reply_count if hasattr(post, 'reply_count') else 0,
                            'repost_count': post.repost_count if hasattr(post, 'repost_count') else 0,
                            'keyword': keyword
                        }
                        
                        all_tweets.append(post_dict)
                        total_posts += 1
                
                print(f"  Found {len(results.posts)} posts for '{keyword}'")
                
            except Exception as e:
                print(f"  Error fetching {keyword}: {e}")
        
        print(f"\n✓ Total posts collected: {total_posts}\n")
        return all_tweets


# ============================================================================
# STEP 2: CLEAN AND FORMAT TWEETS
# ============================================================================

class TweetCleaner:
    """Clean and format tweets to standard format"""
    
    DISASTER_KEYWORDS = ["earthquake", "flood", "wildfire", "hurricane"]
    
    @staticmethod
    def extract_keyword(text: str) -> Optional[str]:
        """Extract disaster keyword from text"""
        if not text:
            return None
        
        text_lower = text.lower()
        for keyword in TweetCleaner.DISASTER_KEYWORDS:
            if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
                return keyword
        
        return None
    
    @staticmethod
    def generate_id(author_handle: str, created_at: str) -> str:
        """Generate unique ID for tweet"""
        id_string = f"{author_handle}_{created_at}"
        return hashlib.md5(id_string.encode()).hexdigest()[:10]
    
    @staticmethod
    def clean_tweet(raw_tweet: Dict) -> Dict:
        """Clean and format a single tweet (matching Elijah's format)"""
        text = raw_tweet.get('text', '')
        author = raw_tweet.get('author', {})
        
        # Extract important fields (matching clean_tweets.py)
        cleaned = {
            'id': TweetCleaner.generate_id(
                author.get('handle', 'unknown'),
                raw_tweet.get('created_at', '')
            ),
            'text': text,
            'author': {
                'handle': author.get('handle'),
                'displayName': author.get('display_name')
            },
            'createdAt': raw_tweet.get('created_at'),
            'keyword': TweetCleaner.extract_keyword(text),
            'location': None,  # Will be extracted by LLM
            
            # Keep metadata
            'uri': raw_tweet.get('uri'),
            'cid': raw_tweet.get('cid'),
            'like_count': raw_tweet.get('like_count', 0),
            'reply_count': raw_tweet.get('reply_count', 0),
            'repost_count': raw_tweet.get('repost_count', 0),
            'original_keyword': raw_tweet.get('keyword')
        }
        
        return cleaned
    
    @staticmethod
    def clean_tweets(raw_tweets: List[Dict]) -> List[Dict]:
        """Clean all tweets"""
        print("Cleaning tweets...")
        cleaned = []
        errors = 0
        
        for raw_tweet in raw_tweets:
            try:
                cleaned.append(TweetCleaner.clean_tweet(raw_tweet))
            except Exception as e:
                print(f"  Error cleaning tweet: {e}")
                errors += 1
        
        print(f"✓ Cleaned {len(cleaned)} tweets")
        if errors > 0:
            print(f"  {errors} errors")
        print()
        
        return cleaned


# ============================================================================
# STEP 3: CLASSIFY TWEETS WITH ML
# ============================================================================

class DisasterClassifier:
    """XGBoost-based disaster classifier"""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.classifier = None
        self.vectorizer = None
        self.label_encoder = None
        self.model_config = None
    
    def load_model(self):
        """Load trained XGBoost model"""
        print("Loading ML classifier...")
        
        # Load config
        with open(self.config.CONFIG_PATH, 'r') as f:
            self.model_config = json.load(f)
        
        # Load model
        self.classifier = joblib.load(self.config.MODEL_PATH)
        
        # Load vectorizer
        self.vectorizer = joblib.load(self.config.VECTORIZER_PATH)
        
        # Load or create label encoder
        if Path(self.config.LABEL_ENCODER_PATH).exists():
            self.label_encoder = joblib.load(self.config.LABEL_ENCODER_PATH)
        else:
            from sklearn.preprocessing import LabelEncoder
            self.label_encoder = LabelEncoder()
            self.label_encoder.classes_ = np.array(self.model_config['classes'])
        
        print(f"✓ Model loaded")
        print(f"  Classes: {', '.join(self.label_encoder.classes_)}\n")
    
    def classify_tweets(self, tweets: List[Dict]) -> List[Dict]:
        """Classify all tweets"""
        if not self.classifier:
            self.load_model()
        
        print(f"Classifying {len(tweets)} tweets with XGBoost...")
        
        # Extract texts
        texts = [tweet['text'] for tweet in tweets]
        
        # Transform to features
        X = self.vectorizer.transform(texts)
        
        # Get predictions and probabilities
        probabilities = self.classifier.predict_proba(X)
        
        # Get optimal thresholds
        thresholds = self.model_config.get('thresholds_per_class', {})
        
        # Classify each tweet
        classified_tweets = []
        for tweet, probs in zip(tweets, probabilities):
            predicted_class_idx = np.argmax(probs)
            max_confidence = probs[predicted_class_idx]
            predicted_type = self.label_encoder.classes_[predicted_class_idx]
            
            # Check if meets threshold
            class_threshold = thresholds.get(predicted_type, 0.5)
            is_disaster = max_confidence >= class_threshold
            
            classified_tweet = {
                **tweet,
                'ml_classification': {
                    'is_disaster': bool(is_disaster),
                    'disaster_type': predicted_type if is_disaster else None,
                    'confidence': float(max_confidence),
                    'all_probabilities': {
                        str(cls): float(prob) 
                        for cls, prob in zip(self.label_encoder.classes_, probs)
                    }
                }
            }
            classified_tweets.append(classified_tweet)
        
        disaster_count = sum(1 for t in classified_tweets if t['ml_classification']['is_disaster'])
        print(f"✓ Classification complete: {disaster_count} disasters, {len(tweets) - disaster_count} non-disasters\n")
        
        return classified_tweets


# ============================================================================
# STEP 4: EXTRACT DETAILS WITH LLM
# ============================================================================

class DisasterState(TypedDict):
    """State for LangGraph workflow"""
    tweet_id: str
    tweet_text: str
    ml_classification: Dict
    extracted_data: Optional[Dict]
    error: Optional[str]


class LLMExtractor:
    """Extract detailed information using LLM"""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.llm = ChatOpenAI(
            model=config.LLM_MODEL,
            openai_api_key=config.HF_TOKEN,
            openai_api_base="https://router.huggingface.co/v1",
            temperature=0.5,
        )
        self.graph = self._build_graph()
        self.llm_calls_made = 0
        self.llm_calls_skipped = 0
    
    def _build_graph(self) -> StateGraph:
        """Build LangGraph workflow"""
        workflow = StateGraph(DisasterState)
        
        workflow.add_node("check_disaster", self._check_disaster)
        workflow.add_node("extract", self._extract_with_llm)
        workflow.add_node("skip", self._skip_extraction)
        
        def route(state: DisasterState) -> str:
            return "extract" if state["ml_classification"]["is_disaster"] else "skip"
        
        workflow.set_entry_point("check_disaster")
        workflow.add_conditional_edges("check_disaster", route, {"extract": "extract", "skip": "skip"})
        workflow.add_edge("extract", END)
        workflow.add_edge("skip", END)
        
        return workflow.compile()
    
    def _check_disaster(self, state: DisasterState) -> DisasterState:
        """Just pass through the ML classification"""
        return state
    
    def _extract_with_llm(self, state: DisasterState) -> DisasterState:
        """Extract details using LLM"""
        time.sleep(self.config.RATE_LIMIT_DELAY)
        self.llm_calls_made += 1
        
        ml_cls = state["ml_classification"]
        disaster_type = ml_cls.get("disaster_type", "unknown")
        confidence = ml_cls.get("confidence", 0)
        
        prompt = f"""Extract key information from this disaster tweet. Return ONLY valid JSON.

Tweet: "{state['tweet_text']}"

ML Classifier predicted: {disaster_type} (confidence: {confidence:.2f})

Extract these fields (use null if not found):
- disaster_type: string
- location: string (city, region, country)
- time: string (when it happened/will happen)
- severity: string (low, medium, high, critical)
- casualties_mentioned: boolean
- damage_mentioned: boolean
- needs_help: boolean
- key_details: string (brief summary)

Return ONLY this JSON:
{{
    "disaster_type": "...",
    "location": "...",
    "time": "...",
    "severity": "...",
    "casualties_mentioned": false,
    "damage_mentioned": false,
    "needs_help": false,
    "key_details": "..."
}}"""
        
        try:
            result = self.llm.invoke(prompt)
            state["extracted_data"] = self._parse_json(result.content)
        except Exception as e:
            state["error"] = f"LLM extraction failed: {str(e)}"
            state["extracted_data"] = None
        
        return state
    
    def _skip_extraction(self, state: DisasterState) -> DisasterState:
        """Skip LLM extraction for non-disasters"""
        self.llm_calls_skipped += 1
        state["extracted_data"] = None
        return state
    
    @staticmethod
    def _parse_json(content: str) -> Dict:
        """Parse JSON from LLM response"""
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        content = content.strip()
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            content = json_match.group()
        
        try:
            return json.loads(content)
        except:
            return None
    
    def process_tweet(self, tweet: Dict) -> Dict:
        """Process a single tweet"""
        initial_state: DisasterState = {
            "tweet_id": tweet['id'],
            "tweet_text": tweet['text'],
            "ml_classification": tweet['ml_classification'],
            "extracted_data": None,
            "error": None
        }
        
        final_state = self.graph.invoke(initial_state)
        
        return {
            **tweet,
            'llm_extraction': final_state['extracted_data'],
            'llm_error': final_state['error']
        }
    
    def process_tweets(self, tweets: List[Dict], limit: Optional[int] = None) -> List[Dict]:
        """Process all disaster tweets"""
        disaster_tweets = [t for t in tweets if t['ml_classification']['is_disaster']]
        non_disaster_tweets = [t for t in tweets if not t['ml_classification']['is_disaster']]

        if limit:
            print(f"Limiting LLM extraction to first {limit} disaster tweets for testing.")
            disaster_tweets = disaster_tweets[:limit]
        
        print(f"Extracting details for {len(disaster_tweets)} disaster tweets with LLM...")
        print(f"(Skipping {len(non_disaster_tweets)} non-disaster tweets)\n")
        
        processed = []
        for i, tweet in enumerate(disaster_tweets, 1):
            result = self.process_tweet(tweet)
            processed.append(result)
            
            if i % 10 == 0:
                print(f"  Processed {i}/{len(disaster_tweets)} tweets...")
        
        # Add non-disaster tweets without LLM extraction
        for tweet in non_disaster_tweets:
            processed.append({
                **tweet,
                'llm_extraction': None,
                'llm_error': None
            })
        
        print(f"\n✓ LLM extraction complete")
        print(f"  API calls made: {self.llm_calls_made}")
        print(f"  API calls saved: {self.llm_calls_skipped}\n")
        
        return processed

# ============================================================================
# STEP  5: STORE IN QDRANT
# ============================================================================

def ingest_into_qdrant(qdrant_client, embedder, jsonl_path):
    """Read tweets from JSONL and insert embeddings + metadata into Qdrant"""
    points = []

    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            tweet = json.loads(line)
            
            # Only process disaster tweets
            ml_classification = tweet.get("ml_classification") or {}
            if not ml_classification.get("is_disaster", False):
                continue  # Skip non-disaster tweets
            text = tweet.get("text", "").strip()
            if not text:
                continue

            # Compute embedding
            vector = embedder.encode(text).tolist()

            # Safely extract nested fields
            ml_classification = tweet.get("ml_classification") or {}
            llm_extraction = tweet.get("llm_extraction") or {}

            # Prepare metadata
            payload = {
                "id": tweet.get("id"),
                "text": text,
                "disaster_type": ml_classification.get("disaster_type"),
                "location": llm_extraction.get("location"),
                "severity": llm_extraction.get("severity"),
                "createdAt": tweet.get("createdAt"),
                # Add some additional useful fields
                "is_disaster": ml_classification.get("is_disaster", False),
                "confidence": ml_classification.get("confidence"),
                "casualties_mentioned": llm_extraction.get("casualties_mentioned"),
                "damage_mentioned": llm_extraction.get("damage_mentioned"),
                "needs_help": llm_extraction.get("needs_help"),
            }

            points.append(PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload=payload
            ))

    if points:
        qdrant_client.upsert(collection_name="disaster_tweets", points=points)
        print(f"✅ Inserted {len(points)} tweets into Qdrant")
    else:
        print("⚠️ No points to insert into Qdrant.")


# ============================================================================
# MAIN PIPELINE
# ============================================================================

class UnifiedPipeline:
    """Main pipeline orchestrator"""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.config.OUTPUT_DIR.mkdir(exist_ok=True)
    
    def save_jsonl(self, data: List[Dict], filepath: Path):
        """Save data as JSONL"""
        with open(filepath, 'w', encoding='utf-8') as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False, default=str) + '\n')
    
    def run(self, skip_fetch: bool = False, use_existing: Optional[str] = None):
        """Run the complete pipeline"""
        print("\n" + "=" * 70)
        print("UNIFIED DISASTER TWEET PIPELINE")
        print("=" * 70 + "\n")
        
        start_time = time.time()
        
        # Step 1: Fetch tweets
        if skip_fetch or use_existing:
            print("⏭Skipping tweet fetch (using existing data)\n")
            if use_existing:
                with open(use_existing, 'r') as f:
                    raw_tweets = [json.loads(line) for line in f if line.strip()]
            else:
                raw_tweets = []
        else:
            print("STEP 1: FETCH TWEETS")
            print("-" * 70)
            fetcher = BlueskyFetcher(self.config)
            raw_tweets = fetcher.fetch_tweets()
            self.save_jsonl(raw_tweets, self.config.RAW_TWEETS_FILE)
            print(f"Saved to: {self.config.RAW_TWEETS_FILE}\n")
        
        if not raw_tweets:
            print("No tweets to process!")
            return
        
        # Step 2: Clean tweets
        print("STEP 2: CLEAN & FORMAT TWEETS")
        print("-" * 70)
        cleaned_tweets = TweetCleaner.clean_tweets(raw_tweets)
        self.save_jsonl(cleaned_tweets, self.config.CLEANED_TWEETS_FILE)
        print(f"Saved to: {self.config.CLEANED_TWEETS_FILE}\n")
        
        # Step 3: Classify with ML
        print("STEP 3: CLASSIFY WITH XGBOOST")
        print("-" * 70)
        classifier = DisasterClassifier(self.config)
        classified_tweets = classifier.classify_tweets(cleaned_tweets)
        self.save_jsonl(classified_tweets, self.config.CLASSIFIED_TWEETS_FILE)
        print(f"Saved to: {self.config.CLASSIFIED_TWEETS_FILE}\n")
        
        # Step 4: Extract with LLM
        print("STEP 4: EXTRACT DETAILS WITH LLM")
        print("-" * 70)
        extractor = LLMExtractor(self.config)
        final_results = extractor.process_tweets(classified_tweets, limit=20)
        self.save_jsonl(final_results, self.config.FINAL_OUTPUT_FILE)
        print(f"Saved to: {self.config.FINAL_OUTPUT_FILE}\n")

        # STEP 5: INGEST INTO QDRANT
        print("STEP 5: INGEST INTO QDRANT")
        print("-" * 70)

        try:
            # Initialize embedding model
            embedder = SentenceTransformer("all-MiniLM-L6-v2")

            # Connect to local Qdrant with shorter timeout
            qdrant_client = QdrantClient(url="http://localhost:6333", timeout=5)
            
            # Test connection first
            try:
                qdrant_client.get_collections()
                print("✅ Successfully connected to Qdrant")
            except Exception as conn_err:
                raise ConnectionError(
                    f"Cannot connect to Qdrant at http://localhost:6333. "
                    f"Please start Qdrant with: docker run -p 6333:6333 qdrant/qdrant"
                ) from conn_err

            # Create collection (using the newer method to avoid deprecation warning)
            collection_name = "disaster_tweets"
            
            # Check if collection exists, delete if it does
            collections = qdrant_client.get_collections().collections
            if any(c.name == collection_name for c in collections):
                qdrant_client.delete_collection(collection_name=collection_name)
                print(f"Deleted existing collection: {collection_name}")
            
            # Create new collection
            qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE),
            )
            print(f"Created collection: {collection_name}")

            # Insert tweets
            ingest_into_qdrant(qdrant_client, embedder, self.config.FINAL_OUTPUT_FILE)
            print("✅ Qdrant ingestion complete!\n")

        except ConnectionError as e:
            print(f"❌ {e}\n")
        except Exception as e:
            print(f"❌ Qdrant ingestion failed: {e}\n")
            import traceback
            traceback.print_exc()

        
        # Summary
        elapsed = time.time() - start_time
        self._print_summary(final_results, elapsed)
    
    def _print_summary(self, results: List[Dict], elapsed: float):
        """Print pipeline summary"""
        print("=" * 70)
        print("Pipeline Complete")
        print("=" * 70)
        
        total = len(results)
        disasters = sum(1 for r in results if r['ml_classification']['is_disaster'])
        extracted = sum(1 for r in results if r.get('llm_extraction'))
        
        # Count by disaster type
        disaster_types = Counter(
            r['ml_classification']['disaster_type'] 
            for r in results 
            if r['ml_classification']['is_disaster']
        )
        
        print(f"\nSummary:")
        print(f"  Total tweets processed: {total}")
        print(f"  Disasters detected: {disasters}")
        print(f"  Non-disasters: {total - disasters}")
        print(f"  LLM extractions: {extracted}")
        print(f"  Total time: {elapsed:.1f}s ({elapsed/total:.2f}s per tweet)")
        
        print(f"\nDisaster breakdown:")
        for dtype, count in disaster_types.most_common():
            print(f"  {dtype:12s}: {count:3d} ({100*count/disasters:.1f}%)")
        
        print(f"\nOutput files:")
        print(f"  1. {self.config.RAW_TWEETS_FILE}")
        print(f"  2. {self.config.CLEANED_TWEETS_FILE}")
        print(f"  3. {self.config.CLASSIFIED_TWEETS_FILE}")
        print(f"  4. {self.config.FINAL_OUTPUT_FILE} ⭐")
        
        print("\n" + "=" * 70 + "\n")


# ============================================================================
# CLI
# ============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Unified disaster tweet pipeline')
    parser.add_argument('--skip-fetch', action='store_true', 
                       help='Skip fetching tweets (use existing files)')
    parser.add_argument('--use-existing', type=str,
                       help='Path to existing raw tweets JSONL file')
    parser.add_argument('--config', type=str,
                       help='Path to custom config file (not implemented)')
    
    args = parser.parse_args()
    
    # Run pipeline
    config = PipelineConfig()
    pipeline = UnifiedPipeline(config)
    
    try:
        pipeline.run(skip_fetch=args.skip_fetch, use_existing=args.use_existing)
    except KeyboardInterrupt:
        print("\n\nPipeline interrupted by user")
    except Exception as e:
        print(f"\n\nPipeline failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()