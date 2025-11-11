"""
Unified Disaster Tweet Pipeline
================================
Complete pipeline that:
1. Fetches tweets from Bluesky
2. Cleans and formats them
3. Classifies them with XGBoost
4. Extracts detailed info with LLM (incrementally)
"""

import os
import json
import re
import hashlib
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Set
import numpy as np
from collections import Counter
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from typing import TypedDict
import joblib

# import Bluesky
try:
    from atproto import Client
    BLUESKY_AVAILABLE = True
except ImportError:
    print("Warning: atproto not installed. Bluesky fetching will be disabled.")
    BLUESKY_AVAILABLE = False

load_dotenv()


# config
class PipelineConfig:
    """Configuration for the entire pipeline"""
    
    # Bluesky settings 
    BLUESKY_HANDLE = os.getenv('BLUESKY_USER', '')
    BLUESKY_PASSWORD = os.getenv('BLUESKY_PWD', '')
    
    # search queries for different disaster types
    DISASTER_QUERIES = [
        "earthquake",
        "flood",
        "wildfire", 
        "hurricane"
    ]
    
    # maximum total posts to fetch
    MAX_POSTS = 400
    
    # ML Model paths
    MODEL_PATH = "./xgboost_classifier/xgboost_model.joblib"
    VECTORIZER_PATH = "./xgboost_classifier/xgboost_vectorizer.joblib"
    CONFIG_PATH = "./xgboost_classifier/xgboost_config.json"
    LABEL_ENCODER_PATH = "./xgboost_classifier/label_encoder.joblib"

    # LLM settings
    HF_TOKEN = os.getenv('HF_TOKEN', '')
    LLM_MODEL = "meta-llama/Llama-3.1-8B-Instruct:novita"
    RATE_LIMIT_DELAY = 1.0  # seconds between LLM calls
    
    # output paths
    OUTPUT_DIR = Path("pipeline_output")
    RAW_TWEETS_FILE = OUTPUT_DIR / "01_raw_tweets.jsonl"
    CLEANED_TWEETS_FILE = OUTPUT_DIR / "02_cleaned_tweets.jsonl"
    CLASSIFIED_TWEETS_FILE = OUTPUT_DIR / "03_classified_tweets.jsonl"
    FINAL_OUTPUT_FILE = OUTPUT_DIR / "04_final_results.jsonl"


# step 1: fetch tweets from bluesky
class BlueskyFetcher:
    """Fetch disaster-related tweets from Bluesky"""
    
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
                # search for posts
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
                        # convert post to dict 
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

# step 2: clean and format tweets
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
        """Clean and format a single tweet"""
        text = raw_tweet.get('text', '')
        author = raw_tweet.get('author', {})
        
        # extract important fields (matching clean_tweets.py)
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
            'location': None,  # will be extracted by LLM
            
            # keep metadata
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

# step 3: classify tweets with classifier
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
        
        # load config
        with open(self.config.CONFIG_PATH, 'r') as f:
            self.model_config = json.load(f)
        
        # load model
        self.classifier = joblib.load(self.config.MODEL_PATH)
        
        # load vectorizer
        self.vectorizer = joblib.load(self.config.VECTORIZER_PATH)
        
        # load or create label encoder
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
        
        # extract texts
        texts = [tweet['text'] for tweet in tweets]
        
        # transform to features
        X = self.vectorizer.transform(texts)
        
        # get predictions and probabilities
        probabilities = self.classifier.predict_proba(X)
        
        # get optimal thresholds
        thresholds = self.model_config.get('thresholds_per_class', {})
        
        # classify each tweet
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


# step 4: extract details with LLM
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
        
        prompt = f"""Analyze this tweet to verify if it's genuinely about a natural disaster and extract key information. Return ONLY valid JSON.

        Tweet: "{state['tweet_text']}"

        ML Model predicted this as: {disaster_type} (confidence: {confidence:.2f})

        First, carefully evaluate if this tweet is actually about a CURRENT or RECENT natural disaster:
        - KEY IDEA: Would an emergency responder find this information useful?
        - It should describe a real disaster event (not metaphorical use, jokes, or general discussion)
        - It should be about a current/recent event (not historical or hypothetical)
        - It should be about natural disasters (not man-made disasters or other emergencies)

        Then extract detailed information if it's valid.

        Return in this JSON format:
        {{
            "llm_classification": boolean,  // true ONLY if it's a valid current/recent natural disaster tweet
            "validation_notes": string,     // brief explanation of why it is/isn't valid
            "disaster_type": string,        // earthquake/flood/hurricane/wildfire/null
            "location": string,             // where is this happening
            "time": string,                 // when did it happen/is happening
            "severity": string,             // low/medium/high/critical
            "casualties_mentioned": boolean, // does it mention deaths/injuries
            "damage_mentioned": boolean,    // does it mention property damage
            "needs_help": boolean,          // does it request assistance/aid
            "key_details": string          // brief summary of main points
        }}

        Example of correct classification:
        - "Massive earthquake just hit San Francisco" = llm_classification: true
        - "This hurricane season might be bad" = llm_classification: false
        - "My life is a disaster rn" = llm_classification: false
        """
        
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
    
    def load_existing_processed_ids(self, filepath: Path) -> Set[str]:
        """Load IDs of already-processed tweets from existing output file"""
        existing_ids = set()
        
        if not filepath.exists():
            print(f"  No existing output file found at {filepath}")
            return existing_ids
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        tweet = json.loads(line)
                        tweet_id = tweet.get('id')
                        if tweet_id:
                            existing_ids.add(tweet_id)
            
            print(f"  Found {len(existing_ids)} existing processed tweets")
        except Exception as e:
            print(f"  Error loading existing tweets: {e}")
        
        return existing_ids
    
    def process_tweets_incrementally(self, tweets: List[Dict], output_file: Path) -> List[Dict]:
        """Process only new tweets and append to existing output"""
        
        # Load existing processed tweet IDs
        print("Checking for existing processed tweets...")
        existing_ids = self.load_existing_processed_ids(output_file)
        
        # Filter to only disaster tweets
        disaster_tweets = [t for t in tweets if t['ml_classification']['is_disaster']]
        non_disaster_count = len([t for t in tweets if not t['ml_classification']['is_disaster']])
        
        # Separate new tweets from already-processed tweets
        new_tweets = [t for t in disaster_tweets if t['id'] not in existing_ids]
        skipped_tweets = [t for t in disaster_tweets if t['id'] in existing_ids]
        
        print(f"\n📊 Tweet Processing Summary:")
        print(f"  Total disaster tweets: {len(disaster_tweets)}")
        print(f"  Already processed (skipping): {len(skipped_tweets)}")
        print(f"  New tweets to process: {len(new_tweets)}")
        print(f"  Non-disasters (filtered): {non_disaster_count}\n")
        
        if not new_tweets:
            print("✓ No new tweets to process!\n")
            return []
        
        # Process new tweets in batches
        BATCH_SIZE = 20
        total_new = len(new_tweets)
        
        print(f"Processing {total_new} new disaster tweets in batches of {BATCH_SIZE}...\n")
        
        newly_processed = []
        
        for batch_start in range(0, total_new, BATCH_SIZE):
            batch_end = min(batch_start + BATCH_SIZE, total_new)
            batch = new_tweets[batch_start:batch_end]
            batch_num = (batch_start // BATCH_SIZE) + 1
            total_batches = (total_new + BATCH_SIZE - 1) // BATCH_SIZE
            
            print(f"📦 Processing batch {batch_num}/{total_batches} (tweets {batch_start+1}-{batch_end})...")
            
            # Process this batch
            for i, tweet in enumerate(batch, 1):
                result = self.process_tweet(tweet)
                newly_processed.append(result)
                
                if i % 5 == 0:
                    print(f"  Batch progress: {i}/{len(batch)} tweets...")
            
            print(f"  ✓ Batch {batch_num} complete ({len(batch)} tweets)\n")
            
            # Brief pause between batches
            if batch_end < total_new:
                time.sleep(2)
        
        print(f"✓ All {total_new} new disaster tweets processed!")
        print(f"  Total API calls: {total_new}\n")
        
        return newly_processed

# main pipeline
class UnifiedPipeline:
    """Main pipeline orchestrator"""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.config.OUTPUT_DIR.mkdir(exist_ok=True)
    
    def save_jsonl(self, data: List[Dict], filepath: Path, mode='w'):
        """Save data as JSONL (mode='w' overwrites, mode='a' appends)"""
        with open(filepath, mode, encoding='utf-8') as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False, default=str) + '\n')
    
    def run(self, skip_fetch: bool = False, use_existing: Optional[str] = None):
        """Run the complete pipeline"""
        print("\n" + "=" * 70)
        print("UNIFIED DISASTER TWEET PIPELINE (INCREMENTAL MODE)")
        print("=" * 70 + "\n")
        
        start_time = time.time()
        
        # step 1: fetch tweets
        if skip_fetch or use_existing:
            print("⏭ Skipping tweet fetch (using existing data)\n")
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
        
        # step 2: clean tweets
        print("STEP 2: CLEAN & FORMAT TWEETS")
        print("-" * 70)
        cleaned_tweets = TweetCleaner.clean_tweets(raw_tweets)
        self.save_jsonl(cleaned_tweets, self.config.CLEANED_TWEETS_FILE)
        print(f"Saved to: {self.config.CLEANED_TWEETS_FILE}\n")
        
        # step 3: classify with ML
        print("STEP 3: CLASSIFY WITH XGBOOST")
        print("-" * 70)
        classifier = DisasterClassifier(self.config)
        classified_tweets = classifier.classify_tweets(cleaned_tweets)
        self.save_jsonl(classified_tweets, self.config.CLASSIFIED_TWEETS_FILE)
        print(f"Saved to: {self.config.CLASSIFIED_TWEETS_FILE}\n")
        
        # step 4: extract with LLM (INCREMENTAL)
        print("STEP 4: EXTRACT DETAILS WITH LLM (INCREMENTAL)")
        print("-" * 70)
        extractor = LLMExtractor(self.config)
        
        # Process only new tweets incrementally
        newly_processed = extractor.process_tweets_incrementally(
            classified_tweets, 
            self.config.FINAL_OUTPUT_FILE
        )
        
        # Append new results to existing file (don't overwrite!)
        if newly_processed:
            self.save_jsonl(newly_processed, self.config.FINAL_OUTPUT_FILE, mode='a')
            print(f"✓ Appended {len(newly_processed)} new tweets to: {self.config.FINAL_OUTPUT_FILE}\n")
        else:
            print(f"✓ No new tweets to append to: {self.config.FINAL_OUTPUT_FILE}\n")
        
        # summary
        elapsed = time.time() - start_time
        self._print_summary(newly_processed, elapsed)
    
    def _print_summary(self, newly_processed: List[Dict], elapsed: float):
        """Print pipeline summary"""
        print("=" * 70)
        print("Pipeline Complete")
        print("=" * 70)
        
        # Count total tweets in final output file
        total_in_file = 0
        if self.config.FINAL_OUTPUT_FILE.exists():
            with open(self.config.FINAL_OUTPUT_FILE, 'r', encoding='utf-8') as f:  # ← ADD encoding='utf-8'
                total_in_file = sum(1 for line in f if line.strip())
        
        new_count = len(newly_processed)
        
        print(f"\nSummary:")
        print(f"  Newly processed tweets: {new_count}")
        print(f"  Total tweets in output file: {total_in_file}")
        
        if new_count > 0:
            print(f"  Processing time: {elapsed:.1f}s ({elapsed/new_count:.2f}s per new tweet)")
            
            # Count by disaster type (only for newly processed)
            disaster_types = Counter(
                t['ml_classification']['disaster_type'] 
                for t in newly_processed 
                if t['ml_classification']['is_disaster']
            )
            
            print(f"\nNew disaster breakdown:")
            for dtype, count in disaster_types.most_common():
                print(f"  {dtype:12s}: {count:3d}")
        else:
            print(f"  Processing time: {elapsed:.1f}s")
        
        print(f"\nOutput files:")
        print(f"  1. {self.config.RAW_TWEETS_FILE}")
        print(f"  2. {self.config.CLEANED_TWEETS_FILE}")
        print(f"  3. {self.config.CLASSIFIED_TWEETS_FILE}")
        print(f"  4. {self.config.FINAL_OUTPUT_FILE} (incremental)")
        
        print("\n" + "=" * 70 + "\n")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Unified disaster tweet pipeline')
    parser.add_argument('--skip-fetch', action='store_true', help='Skip fetching tweets (use existing files)')
    parser.add_argument('--use-existing', type=str, help='Path to existing raw tweets JSONL file')
    parser.add_argument('--config', type=str, help='Path to custom config file (not implemented)')
    
    args = parser.parse_args()
    
    # run pipeline
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