"""
Unified Disaster Tweet Pipeline - Multi-Token Edition
======================================================
Complete pipeline that:
1. Fetches tweets from Bluesky
2. Cleans and formats them
3. Classifies them with XGBoost
4. Extracts detailed info with LLM (using token rotation)

NEW FEATURES:
- Supports multiple HuggingFace tokens (HF_TOKEN1, HF_TOKEN2, etc.)
- Automatically rotates tokens when credit limit is hit
- Calculates optimal number of tokens needed
"""

import os
import json
import re
import hashlib
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict
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
    
    # LLM settings - MULTI-TOKEN SUPPORT
    HF_TOKENS = []  # Will be populated from environment
    LLM_MODEL = "meta-llama/Llama-3.1-8B-Instruct:novita"
    RATE_LIMIT_DELAY = 1.0  # seconds between LLM calls
    
    # Control flags
    SKIP_LLM = os.getenv('SKIP_LLM', 'false').lower() == 'true'
    MAX_LLM_CALLS = int(os.getenv('MAX_LLM_CALLS', '0'))  # 0 = unlimited
    
    # output paths
    OUTPUT_DIR = Path("pipeline_output")
    RAW_TWEETS_FILE = OUTPUT_DIR / "01_raw_tweets.jsonl"
    CLEANED_TWEETS_FILE = OUTPUT_DIR / "02_cleaned_tweets.jsonl"
    CLASSIFIED_TWEETS_FILE = OUTPUT_DIR / "03_classified_tweets.jsonl"
    FINAL_OUTPUT_FILE = OUTPUT_DIR / "04_final_results.jsonl"
    
    def __init__(self):
        """Initialize and load all HF tokens from environment"""
        self._load_hf_tokens()
    
    def _load_hf_tokens(self):
        """Load all HF_TOKEN1, HF_TOKEN2, ... from environment"""
        i = 1
        while True:
            token_key = f'HF_TOKEN{i}'
            token = os.getenv(token_key, '')
            if token:
                self.HF_TOKENS.append(token)
                i += 1
            else:
                break
        
        # Fallback to old HF_TOKEN if no numbered tokens found
        if not self.HF_TOKENS:
            old_token = os.getenv('HF_TOKEN', '')
            if old_token:
                self.HF_TOKENS.append(old_token)
        
        if self.HF_TOKENS:
            print(f"✓ Loaded {len(self.HF_TOKENS)} HuggingFace token(s)")
        else:
            print("⚠️  No HuggingFace tokens found in environment")


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
        
        # extract important fields
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
        
        disaster_count = sum(1 for t in classified_tweets 
                           if t['ml_classification']['is_disaster'])
        
        print(f"✓ Classification complete: {disaster_count} disasters, "
              f"{len(tweets) - disaster_count} non-disasters\n")
        
        return classified_tweets


# step 4: extract details with LLM (MULTI-TOKEN SUPPORT)
class DisasterState(TypedDict):
    """State for LangGraph workflow"""
    tweet_id: str
    tweet_text: str
    ml_classification: Dict
    extracted_data: Optional[Dict]
    error: Optional[str]


class TokenRotationManager:
    """Manages rotation between multiple HF tokens"""
    
    def __init__(self, tokens: List[str]):
        self.tokens = tokens
        self.current_token_idx = 0
        self.token_stats = {i: {'calls': 0, 'exhausted': False} 
                           for i in range(len(tokens))}
        self.total_rotations = 0
    
    def get_current_token(self) -> Optional[str]:
        """Get the current active token"""
        if not self.tokens:
            return None
        
        # Find next available token
        attempts = 0
        while attempts < len(self.tokens):
            if not self.token_stats[self.current_token_idx]['exhausted']:
                return self.tokens[self.current_token_idx]
            
            # This token is exhausted, try next
            self.current_token_idx = (self.current_token_idx + 1) % len(self.tokens)
            attempts += 1
        
        # All tokens exhausted
        return None
    
    def mark_token_exhausted(self):
        """Mark current token as exhausted and rotate to next"""
        self.token_stats[self.current_token_idx]['exhausted'] = True
        old_idx = self.current_token_idx
        self.current_token_idx = (self.current_token_idx + 1) % len(self.tokens)
        self.total_rotations += 1
        
        print(f"\n🔄 Token {old_idx + 1} exhausted, rotating to Token {self.current_token_idx + 1}")
        print(f"   Total rotations so far: {self.total_rotations}\n")
    
    def record_successful_call(self):
        """Record a successful API call for current token"""
        self.token_stats[self.current_token_idx]['calls'] += 1
    
    def all_tokens_exhausted(self) -> bool:
        """Check if all tokens are exhausted"""
        return all(stats['exhausted'] for stats in self.token_stats.values())
    
    def get_stats(self) -> Dict:
        """Get statistics about token usage"""
        total_calls = sum(stats['calls'] for stats in self.token_stats.values())
        exhausted_count = sum(1 for stats in self.token_stats.values() if stats['exhausted'])
        
        return {
            'total_tokens': len(self.tokens),
            'exhausted_tokens': exhausted_count,
            'total_calls': total_calls,
            'rotations': self.total_rotations,
            'per_token': self.token_stats
        }


class LLMExtractor:
    """Extract detailed information using LLM with token rotation"""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.llm = None
        self.graph = None
        self.llm_calls_made = 0
        self.llm_calls_skipped = 0
        
        # Token rotation manager
        self.token_manager = TokenRotationManager(config.HF_TOKENS)
        
        # Only initialize LLM if not skipping and tokens available
        if not config.SKIP_LLM and config.HF_TOKENS:
            self._initialize_llm()
            if self.llm:
                self.graph = self._build_graph()
        else:
            if not config.HF_TOKENS:
                print("⚠️  No HuggingFace tokens available")
            self.config.SKIP_LLM = True
    
    def _initialize_llm(self):
        """Initialize LLM with current token"""
        current_token = self.token_manager.get_current_token()
        if not current_token:
            print("⚠️  No available tokens to initialize LLM")
            return
        
        try:
            self.llm = ChatOpenAI(
                model=self.config.LLM_MODEL,
                openai_api_key=current_token,
                openai_api_base="https://router.huggingface.co/v1",
                temperature=0.5,
            )
            print(f"✓ LLM initialized with Token {self.token_manager.current_token_idx + 1}")
        except Exception as e:
            print(f"⚠️  Warning: Could not initialize LLM: {e}")
            self.config.SKIP_LLM = True
    
    def _rotate_to_next_token(self) -> bool:
        """Rotate to next available token and reinitialize LLM"""
        self.token_manager.mark_token_exhausted()
        
        if self.token_manager.all_tokens_exhausted():
            print("❌ All tokens exhausted! Cannot continue LLM extraction.\n")
            return False
        
        # Reinitialize LLM with new token
        current_token = self.token_manager.get_current_token()
        if not current_token:
            return False
        
        try:
            self.llm = ChatOpenAI(
                model=self.config.LLM_MODEL,
                openai_api_key=current_token,
                openai_api_base="https://router.huggingface.co/v1",
                temperature=0.5,
            )
            print(f"✓ Successfully switched to Token {self.token_manager.current_token_idx + 1}\n")
            return True
        except Exception as e:
            print(f"⚠️  Failed to initialize new token: {e}")
            return False
    
    def _build_graph(self) -> StateGraph:
        """Build LangGraph workflow"""
        workflow = StateGraph(DisasterState)
        
        workflow.add_node("check_disaster", self._check_disaster)
        workflow.add_node("extract", self._extract_with_llm)
        workflow.add_node("skip", self._skip_extraction)
        
        def route(state: DisasterState) -> str:
            return "extract" if state["ml_classification"]["is_disaster"] else "skip"
        
        workflow.set_entry_point("check_disaster")
        workflow.add_conditional_edges("check_disaster", route,
                                      {"extract": "extract", "skip": "skip"})
        workflow.add_edge("extract", END)
        workflow.add_edge("skip", END)
        
        return workflow.compile()
    
    def _check_disaster(self, state: DisasterState) -> DisasterState:
        """Just pass through the ML classification"""
        return state
    
    def _extract_with_llm(self, state: DisasterState) -> DisasterState:
        """Extract details using LLM with token rotation"""
        # Check if all tokens exhausted
        if self.token_manager.all_tokens_exhausted():
            state["error"] = "All HuggingFace tokens exhausted"
            state["extracted_data"] = None
            self.llm_calls_skipped += 1
            return state
        
        # Check if we've hit the max calls limit
        if self.config.MAX_LLM_CALLS > 0 and self.llm_calls_made >= self.config.MAX_LLM_CALLS:
            state["error"] = f"Reached maximum LLM calls limit ({self.config.MAX_LLM_CALLS})"
            state["extracted_data"] = None
            self.llm_calls_skipped += 1
            return state
        
        time.sleep(self.config.RATE_LIMIT_DELAY)
        
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

Then extract detailed information if it's valid. Return in this JSON format:

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
        
        # Try to make the API call with retry on token exhaustion
        max_retries = len(self.config.HF_TOKENS)
        for attempt in range(max_retries):
            try:git checkout --theirs backend/pipeline_output/01_raw_tweets.jsonl

                result = self.llm.invoke(prompt)
                state["extracted_data"] = self._parse_json(result.content)
                self.llm_calls_made += 1
                self.token_manager.record_successful_call()
                return state
                
            except Exception as e:
                error_msg = str(e)
                
                # Check if it's a credit limit error
                if "402" in error_msg or "exceeded" in error_msg.lower() or "credits" in error_msg.lower():
                    print(f"⚠️  Token {self.token_manager.current_token_idx + 1} hit credit limit")
                    
                    # Try to rotate to next token
                    if self._rotate_to_next_token():
                        # Retry with new token
                        continue
                    else:
                        # All tokens exhausted
                        state["error"] = "All HuggingFace tokens exhausted"
                        state["extracted_data"] = None
                        self.llm_calls_skipped += 1
                        return state
                else:
                    # Other error, don't retry
                    state["error"] = f"LLM extraction failed: {error_msg}"
                    state["extracted_data"] = None
                    return state
        
        # If we get here, all retries failed
        state["error"] = "LLM extraction failed after all token retries"
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
    
    def process_all_tweets_in_batches(self, tweets: List[Dict]) -> List[Dict]:
        """Process all disaster tweets in batches"""
        # Check if LLM is disabled
        if self.config.SKIP_LLM:
            print("⏭  LLM extraction is disabled (SKIP_LLM=true)")
            print("   Returning ML-classified tweets without LLM extraction.\n")
            disaster_tweets = [t for t in tweets if t['ml_classification']['is_disaster']]
            for tweet in disaster_tweets:
                tweet['llm_extraction'] = None
                tweet['llm_error'] = "LLM extraction skipped (SKIP_LLM=true)"
            return disaster_tweets
        
        # Process all disaster tweets in batches of 20
        disaster_tweets = [t for t in tweets if t['ml_classification']['is_disaster']]
        non_disaster_count = len([t for t in tweets if not t['ml_classification']['is_disaster']])
        total_disasters = len(disaster_tweets)
        
        BATCH_SIZE = 20
        
        print(f"Processing {total_disasters} disaster tweets in batches of {BATCH_SIZE}...")
        print(f"(Filtering out {non_disaster_count} non-disaster tweets)")
        print(f"Using {len(self.config.HF_TOKENS)} HuggingFace token(s)\n")
        
        if self.config.MAX_LLM_CALLS > 0:
            print(f"⚠️  LLM call limit set to: {self.config.MAX_LLM_CALLS}\n")
        
        all_processed = []
        
        # Process in batches
        for batch_start in range(0, total_disasters, BATCH_SIZE):
            # Stop if all tokens exhausted
            if self.token_manager.all_tokens_exhausted():
                print(f"\n❌ All tokens exhausted!")
                print(f"   Processed {len(all_processed)}/{total_disasters} tweets.\n")
                # Add remaining tweets with error message
                for tweet in disaster_tweets[batch_start:]:
                    tweet['llm_extraction'] = None
                    tweet['llm_error'] = "All HuggingFace tokens exhausted"
                    all_processed.append(tweet)
                break
            
            batch_end = min(batch_start + BATCH_SIZE, total_disasters)
            batch = disaster_tweets[batch_start:batch_end]
            
            batch_num = (batch_start // BATCH_SIZE) + 1
            total_batches = (total_disasters + BATCH_SIZE - 1) // BATCH_SIZE
            
            print(f"📦 Batch {batch_num}/{total_batches} (tweets {batch_start+1}-{batch_end})...")
            print(f"   Current token: Token {self.token_manager.current_token_idx + 1}")
            
            # Process this batch
            for i, tweet in enumerate(batch, 1):
                result = self.process_tweet(tweet)
                all_processed.append(result)
                
                if i % 5 == 0:
                    print(f"   Progress: {i}/{len(batch)} tweets...")
                
                # Stop if all tokens exhausted
                if self.token_manager.all_tokens_exhausted():
                    break
            
            if not self.token_manager.all_tokens_exhausted():
                print(f"   ✓ Batch complete\n")
                
                # Brief pause between batches
                if batch_end < total_disasters:
                    time.sleep(2)
        
        # Print final statistics
        stats = self.token_manager.get_stats()
        print(f"\n{'='*70}")
        print("TOKEN USAGE STATISTICS")
        print(f"{'='*70}")
        print(f"Total tokens available: {stats['total_tokens']}")
        print(f"Tokens exhausted: {stats['exhausted_tokens']}")
        print(f"Total LLM calls made: {stats['total_calls']}")
        print(f"Token rotations: {stats['rotations']}")
        print(f"\nPer-token breakdown:")
        for idx, token_stats in stats['per_token'].items():
            status = "❌ EXHAUSTED" if token_stats['exhausted'] else "✓ Available"
            print(f"  Token {idx + 1}: {token_stats['calls']} calls - {status}")
        print(f"{'='*70}\n")
        
        return all_processed


# main pipeline
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
        print("UNIFIED DISASTER TWEET PIPELINE - MULTI-TOKEN EDITION")
        print("=" * 70 + "\n")
        
        # Show configuration
        if self.config.SKIP_LLM:
            print("⚠️  LLM extraction is DISABLED\n")
        elif self.config.MAX_LLM_CALLS > 0:
            print(f"⚠️  LLM calls limited to: {self.config.MAX_LLM_CALLS}\n")
        
        start_time = time.time()
        
        # step 1: fetch tweets
        if skip_fetch or use_existing:
            print("⏭  Skipping tweet fetch (using existing data)\n")
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
        
        # step 4: extract with LLM
        print("STEP 4: EXTRACT DETAILS WITH LLM")
        print("-" * 70)
        extractor = LLMExtractor(self.config)
        
        # Process in batches with token rotation
        final_results = extractor.process_all_tweets_in_batches(classified_tweets)
        
        # save the results
        self.save_jsonl(final_results, self.config.FINAL_OUTPUT_FILE)
        print(f"Saved to: {self.config.FINAL_OUTPUT_FILE}\n")
        
        # summary
        elapsed = time.time() - start_time
        timestamp_file = self.config.OUTPUT_DIR / 'last_update.json'
        timestamp_data = {
            "last_update": datetime.now().isoformat(),
            "next_update": (datetime.now() + timedelta(hours=6)).isoformat()
        }

        with open(timestamp_file, 'w') as f:
            json.dump(timestamp_data, f, indent=2)
        print(f"Timestamp updated for frontend\n")
        self._print_summary(final_results, elapsed)
    
    def _print_summary(self, results: List[Dict], elapsed: float):
        """Print pipeline summary"""
        print("=" * 70)
        print("Pipeline Complete")
        print("=" * 70)
        
        total = len(results)
        disasters = sum(1 for r in results 
                       if r['ml_classification']['is_disaster'])
        extracted = sum(1 for r in results if r.get('llm_extraction'))
        errors = sum(1 for r in results if r.get('llm_error'))
        
        # count by disaster type
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
        print(f"  LLM errors: {errors}")
        print(f"  Total time: {elapsed:.1f}s ({elapsed/total:.2f}s per tweet)")
        
        print(f"\nDisaster breakdown:")
        for dtype, count in disaster_types.most_common():
            print(f"  {dtype:12s}: {count:3d} ({100*count/disasters:.1f}%)")
        
        print(f"\nOutput files:")
        print(f"  1. {self.config.RAW_TWEETS_FILE}")
        print(f"  2. {self.config.CLEANED_TWEETS_FILE}")
        print(f"  3. {self.config.CLASSIFIED_TWEETS_FILE}")
        print(f"  4. {self.config.FINAL_OUTPUT_FILE}")
        
        print("\n" + "=" * 70 + "\n")


def calculate_optimal_tokens(tweets_per_run: int, runs_per_day: int, 
                            disaster_percentage: float = 0.25,
                            calls_per_token: int = 500):
    """
    Calculate optimal number of HF tokens needed
    
    Args:
        tweets_per_run: Number of tweets fetched per run (e.g., 400)
        runs_per_day: How many times pipeline runs per day (e.g., 2)
        disaster_percentage: Expected % of tweets classified as disasters (default 25%)
        calls_per_token: Free tier limit per token per month (default ~500)
    
    Returns:
        Dictionary with recommendations
    """
    # Calculate daily and monthly needs
    disaster_tweets_per_run = int(tweets_per_run * disaster_percentage)
    daily_llm_calls = disaster_tweets_per_run * runs_per_day
    monthly_llm_calls = daily_llm_calls * 30  # 30 days
    
    # Calculate tokens needed
    tokens_needed = int(np.ceil(monthly_llm_calls / calls_per_token))
    
    # Calculate with safety margin
    tokens_with_margin = int(np.ceil(tokens_needed * 1.2))  # 20% safety margin
    
    return {
        'tweets_per_run': tweets_per_run,
        'runs_per_day': runs_per_day,
        'disaster_tweets_per_run': disaster_tweets_per_run,
        'daily_llm_calls': daily_llm_calls,
        'monthly_llm_calls': monthly_llm_calls,
        'tokens_needed_minimum': tokens_needed,
        'tokens_recommended': tokens_with_margin,
        'calls_per_token_assumed': calls_per_token
    }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Unified disaster tweet pipeline with multi-token support')
    parser.add_argument('--skip-fetch', action='store_true',
                       help='Skip fetching tweets (use existing files)')
    parser.add_argument('--use-existing', type=str,
                       help='Path to existing raw tweets JSONL file')
    parser.add_argument('--skip-llm', action='store_true',
                       help='Skip LLM extraction (faster, ML only)')
    parser.add_argument('--max-llm-calls', type=int, default=0,
                       help='Maximum number of LLM API calls (0=unlimited)')
    parser.add_argument('--calculate-tokens', action='store_true',
                       help='Calculate optimal number of tokens needed')
    
    args = parser.parse_args()
    
    # Calculate optimal tokens if requested
    if args.calculate_tokens:
        print("\n" + "=" * 70)
        print("TOKEN REQUIREMENT CALCULATOR")
        print("=" * 70 + "\n")
        
        # Default scenario: 400 tweets, 2 runs per day
        result = calculate_optimal_tokens(
            tweets_per_run=400,
            runs_per_day=2,
            disaster_percentage=0.25,  # Assume 25% are disasters after ML filtering
            calls_per_token=500  # Conservative estimate for HF free tier
        )
        
        print(f"Scenario: {result['tweets_per_run']} tweets per run, {result['runs_per_day']} runs per day")
        print(f"\nEstimates (assuming {result['disaster_tweets_per_run']} disaster tweets per run):")
        print(f"  Daily LLM calls needed: {result['daily_llm_calls']}")
        print(f"  Monthly LLM calls needed: {result['monthly_llm_calls']}")
        print(f"  Calls per token (free tier): ~{result['calls_per_token_assumed']}")
        print(f"\n✓ MINIMUM tokens needed: {result['tokens_needed_minimum']}")
        print(f"✓ RECOMMENDED tokens (with 20% margin): {result['tokens_recommended']}")
        print(f"\n💡 TIP: Create {result['tokens_recommended']} HuggingFace accounts")
        print(f"   and add them to .env as HF_TOKEN1, HF_TOKEN2, ... HF_TOKEN{result['tokens_recommended']}")
        print("\n" + "=" * 70 + "\n")
        return
    
    # Override config with command-line args
    if args.skip_llm:
        os.environ['SKIP_LLM'] = 'true'
    if args.max_llm_calls > 0:
        os.environ['MAX_LLM_CALLS'] = str(args.max_llm_calls)
    
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
