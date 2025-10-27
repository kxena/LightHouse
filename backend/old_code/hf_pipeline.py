import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional
import json
import re
from datetime import datetime
import time
from concurrent.futures import ThreadPoolExecutor
import joblib
from pathlib import Path
import numpy as np

# Import the classifier
try:
    from classifier import DisasterClassifier
except ImportError:
    print("Warning: Could not import DisasterClassifier. Make sure classifier.py is in the same directory.")
    DisasterClassifier = None

load_dotenv()

# Initialize LLM
llm = ChatOpenAI(
    model="meta-llama/Llama-3.1-8B-Instruct:novita",
    openai_api_key=(os.getenv('HF_TOKEN')),
    openai_api_base="https://router.huggingface.co/v1",
    temperature=0.5,
)

# Define the state of workflow
class DisasterState(TypedDict):
    tweet_id: str
    tweet_text: str
    is_disaster: bool
    disaster_type: Optional[str]  # From ML classifier
    confidence: Optional[float]    # Confidence score from ML classifier
    extracted_data: Optional[dict] # From LLM extraction
    error: Optional[str]


class IntegratedDisasterPipeline:
    """
    Integrated pipeline combining ML classifier with LLM extraction.
    
    The pipeline works in 2 stages:
    1. ML Classifier (XGBoost) determines:
       - Is this a disaster tweet? (using confidence threshold)
       - What type of disaster? (earthquake, flood, hurricane, wildfire)
       - Confidence scores
    
    2. LLM Extraction (only for disaster tweets) extracts:
       - Detailed structured information
       - Location, time, severity
       - Casualties, damage, help requests
    """
    
    def __init__(self, 
                 model_path: str = 'xgboost_model_20251018_093203.joblib',
                 vectorizer_path: str = 'xgboost_vectorizer_20251018_093203.joblib',
                 config_path: str = 'xgboost_config_20251018_093203.json',
                 label_encoder_path: str = 'label_encoder_20251018_093203.joblib',
                 disaster_threshold: float = 0.5):
        """
        Initialize the integrated pipeline.
        
        Args:
            model_path: Path to trained XGBoost model
            vectorizer_path: Path to TF-IDF vectorizer
            config_path: Path to model config JSON
            label_encoder_path: Path to label encoder
            disaster_threshold: Minimum confidence to classify as disaster (0-1)
        """
        self.disaster_threshold = disaster_threshold
        self.classifier = None
        self.vectorizer = None
        self.label_encoder = None
        self.config = None
        
        # Load the classifier components
        try:
            self.load_classifier(model_path, vectorizer_path, config_path, label_encoder_path)
        except Exception as e:
            print(f"Warning: Could not load classifier: {e}")
            print("Pipeline will run in LLM-only mode.")
        
        # Build the LangGraph workflow
        self.graph = self._build_graph()
    
    def load_classifier(self, model_path: str, vectorizer_path: str, 
                       config_path: str, label_encoder_path: str):
        """Load the trained ML classifier components"""
        print(f"\nLoading ML classifier components...")
        
        # Load config
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        print(f"  ✓ Loaded config")
        
        # Load model
        self.classifier = joblib.load(model_path)
        print(f"  ✓ Loaded XGBoost model")
        
        # Load vectorizer
        self.vectorizer = joblib.load(vectorizer_path)
        print(f"  ✓ Loaded TF-IDF vectorizer")
        
        # Load label encoder or create from config
        if Path(label_encoder_path).exists():
            self.label_encoder = joblib.load(label_encoder_path)
            print(f"  ✓ Loaded label encoder")
        else:
            # Create label encoder from config classes
            from sklearn.preprocessing import LabelEncoder
            self.label_encoder = LabelEncoder()
            self.label_encoder.classes_ = np.array(self.config['classes'])
            print(f"  ✓ Created label encoder from config (file not found)")
        
        print(f"  Classes: {self.label_encoder.classes_}")
        print(f"  Optimal thresholds: {self.config.get('thresholds_per_class', {})}\n")
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(DisasterState)
        
        # Add nodes
        workflow.add_node("classify", self._classify_with_ml)
        workflow.add_node("extract", self._extract_with_llm)
        workflow.add_node("skip", self._skip_extraction)
        
        # Define routing logic
        def route_based_on_classification(state: DisasterState) -> str:
            return "extract" if state["is_disaster"] else "skip"
        
        # Set up the graph flow
        workflow.set_entry_point("classify")
        workflow.add_conditional_edges(
            "classify",
            route_based_on_classification,
            {"extract": "extract", "skip": "skip"}
        )
        workflow.add_edge("extract", END)
        workflow.add_edge("skip", END)
        
        return workflow.compile()
    
    def _classify_with_ml(self, state: DisasterState) -> DisasterState:
        """
        Stage 1: Use ML classifier to determine if tweet is about a disaster
        and what type of disaster it is.
        
        The classifier only knows 4 types: earthquake, flood, hurricane, wildfire
        We use confidence scores to determine if it's a disaster at all.
        """
        if self.classifier is None:
            # Fallback: assume all tweets are disasters (LLM will handle it)
            state["is_disaster"] = True
            state["disaster_type"] = "unknown"
            state["confidence"] = 0.5
            state["error"] = "ML classifier not available - using LLM only mode"
            return state
        
        try:
            # Transform text to features
            X = self.vectorizer.transform([state["tweet_text"]])
            
            # Get prediction probabilities
            probabilities = self.classifier.predict_proba(X)[0]
            
            # Get the predicted class and its probability
            predicted_class_idx = np.argmax(probabilities)
            max_confidence = probabilities[predicted_class_idx]
            predicted_type = self.label_encoder.classes_[predicted_class_idx]
            
            # Use optimal thresholds if available
            thresholds = self.config.get('thresholds_per_class', {})
            class_threshold = thresholds.get(predicted_type, self.disaster_threshold)
            
            # Determine if it's a disaster based on confidence
            # High confidence in any disaster type = it's a disaster
            is_disaster = max_confidence >= class_threshold
            
            state["is_disaster"] = is_disaster
            state["disaster_type"] = predicted_type if is_disaster else None
            state["confidence"] = float(max_confidence)
            state["error"] = None
            
            # Debug info (optional)
            if max_confidence < class_threshold:
                state["error"] = f"Low confidence: {max_confidence:.3f} < {class_threshold:.3f}"
            
        except Exception as e:
            state["error"] = f"ML classification failed: {str(e)}"
            state["is_disaster"] = True  # Fallback to LLM extraction
            state["disaster_type"] = "unknown"
            state["confidence"] = 0.0
        
        return state
    
    def _extract_with_llm(self, state: DisasterState) -> DisasterState:
        """
        Stage 2: Extract detailed structured information using LLM.
        Only runs if ML classifier determined this is a disaster tweet.
        """
        # Include ML prediction in the prompt to guide LLM
        disaster_context = ""
        if state.get("disaster_type"):
            disaster_context = f"\nML Classifier predicted: {state['disaster_type']} (confidence: {state['confidence']:.2f})"
        
        prompt = f"""Extract key information from this natural disaster tweet and return ONLY valid JSON.

Tweet: "{state['tweet_text']}"{disaster_context}

Extract the following fields (use null if not found):
- disaster_type: string (e.g., "earthquake", "flood", "hurricane", "wildfire", "tornado", "tsunami")
- location: string (city, region, or country mentioned)
- time: string (when did/will it happen - extract date/time if mentioned)
- severity: string (low, medium, high, or critical based on language used)
- casualties_mentioned: boolean (true if deaths/injuries mentioned)
- damage_mentioned: boolean (true if property damage mentioned)
- needs_help: boolean (true if this is a call for help/assistance)
- key_details: string (brief summary of the most important details)

Return ONLY this JSON format with no other text:
{{
    "disaster_type": "...",
    "location": "...",
    "time": "...",
    "severity": "...",
    "casualties_mentioned": true,
    "damage_mentioned": true,
    "needs_help": false,
    "key_details": "..."
}}
"""
        
        try:
            result = llm.invoke(prompt)
            state["extracted_data"] = self._parse_json_response(result.content)
        except Exception as e:
            state["error"] = f"LLM extraction failed: {str(e)}"
            state["extracted_data"] = None
        
        return state
    
    def _skip_extraction(self, state: DisasterState) -> DisasterState:
        """Skip LLM extraction for non-disaster tweets"""
        state["extracted_data"] = None
        return state
    
    @staticmethod
    def _parse_json_response(content: str) -> dict:
        """Clean and parse JSON from LLM response"""
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
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            return {
                "disaster_type": None,
                "location": None,
                "time": None,
                "severity": None,
                "casualties_mentioned": False,
                "damage_mentioned": False,
                "needs_help": False,
                "key_details": None
            }
    
    def process_tweet(self, tweet_id: str, tweet_text: str) -> dict:
        """
        Process a single tweet through the integrated pipeline.
        
        Returns:
            dict with classification results and extracted data
        """
        initial_state: DisasterState = {
            "tweet_id": tweet_id,
            "tweet_text": tweet_text,
            "is_disaster": False,
            "disaster_type": None,
            "confidence": None,
            "extracted_data": None,
            "error": None
        }
        
        final_state = self.graph.invoke(initial_state)
        
        return {
            "id": final_state["tweet_id"],
            "original_tweet": tweet_text,
            "ml_classification": {
                "is_disaster": final_state["is_disaster"],
                "disaster_type": final_state["disaster_type"],
                "confidence": final_state["confidence"]
            },
            "llm_extraction": final_state["extracted_data"],
            "error": final_state["error"]
        }
    
    def process_batch(self, input_file: str, output_file: str = None,
                     limit: int = None, max_workers: int = 3):
        """
        Process batch of tweets from JSONL file.
        
        Args:
            input_file: Path to input JSONL file
            output_file: Path to output JSONL file
            limit: Process only first N tweets (None = all)
            max_workers: Number of parallel workers
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"disaster_results_{timestamp}.jsonl"
        
        print(f"\n{'='*70}")
        print("INTEGRATED DISASTER PIPELINE - BATCH MODE")
        print(f"{'='*70}\n")
        print(f"ML Classifier: XGBoost")
        print(f"Disaster Threshold: {self.disaster_threshold}")
        print(f"Loading tweets from: {input_file}")
        
        tweets = self._load_jsonl(input_file, limit)
        
        if limit:
            print(f"Processing first {limit} tweets with {max_workers} workers...")
        else:
            print(f"Processing {len(tweets)} tweets with {max_workers} workers...")
        
        start_time = time.time()
        results = []
        
        print(f"\nStarting parallel processing...\n")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(self.process_tweet, tweet['id'], tweet['text'])
                for tweet in tweets
            ]
            
            for i, future in enumerate(futures, 1):
                result = future.result()
                results.append(result)
                
                # Print progress
                ml_cls = result['ml_classification']
                print(f"[{i}/{len(tweets)}] Tweet {result['id']}", end='')
                
                if ml_cls['is_disaster']:
                    print(f" → {ml_cls['disaster_type']} ({ml_cls['confidence']:.2f})", end='')
                    if result['llm_extraction']:
                        loc = result['llm_extraction'].get('location', 'unknown')
                        print(f" in {loc}")
                    else:
                        print(" [LLM extraction failed]")
                else:
                    print(f" → Not disaster ({ml_cls['confidence']:.2f})")
        
        elapsed = time.time() - start_time
        
        # Save results
        self._save_results(results, output_file)
        
        # Print summary
        self._print_summary(results, elapsed)
    
    @staticmethod
    def _load_jsonl(file_path: str, limit: int = None) -> list:
        """Load tweets from JSONL file"""
        tweets = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    # Handle different possible field names
                    tweet_text = data.get('text') or data.get('tweet_text') or data.get('tweet')
                    tweet_id = data.get('id') or data.get('tweet_id') or str(len(tweets))
                    
                    tweets.append({
                        'id': tweet_id,
                        'text': tweet_text
                    })
                    
                    if limit and len(tweets) >= limit:
                        break
        return tweets
    
    @staticmethod
    def _save_results(results: list, output_path: str):
        """Save processed results to output JSONL file"""
        def convert_to_serializable(obj):
            """Convert numpy types to Python native types"""
            if isinstance(obj, np.bool_):
                return bool(obj)
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: convert_to_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_serializable(item) for item in obj]
            return obj
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for result in results:
                serializable_result = convert_to_serializable(result)
                f.write(json.dumps(serializable_result, ensure_ascii=False) + '\n')
        print(f"\nResults saved to: {output_path}")
    
    @staticmethod
    def _print_summary(results: list, elapsed: float):
        """Print processing summary"""
        print("\n" + "="*70)
        print("PROCESSING COMPLETE")
        print("="*70)
        
        disaster_count = sum(1 for r in results if r['ml_classification']['is_disaster'])
        extracted_count = sum(1 for r in results if r['llm_extraction'] is not None)
        error_count = sum(1 for r in results if r['error'] and 'failed' in r['error'].lower())
        
        # Count disasters by type
        disaster_types = {}
        for r in results:
            if r['ml_classification']['is_disaster']:
                dtype = r['ml_classification']['disaster_type']
                disaster_types[dtype] = disaster_types.get(dtype, 0) + 1
        
        print(f"Total processed: {len(results)}")
        print(f"Total time: {elapsed:.2f}s")
        print(f"Average per tweet: {elapsed/len(results):.2f}s")
        print(f"\nML Classification:")
        print(f"  Disasters detected: {disaster_count}")
        print(f"  Non-disasters: {len(results) - disaster_count}")
        
        if disaster_types:
            print(f"\n  Disaster Types:")
            for dtype, count in sorted(disaster_types.items()):
                print(f"    - {dtype}: {count}")
        
        print(f"\nLLM Extraction:")
        print(f"  Successful extractions: {extracted_count}")
        print(f"  Errors: {error_count}")
        print("="*70 + "\n")


# Example usage and main execution
if __name__ == "__main__":
    # Configuration
    INPUT_FILE = "kaggle_format_posts.jsonl"
    OUTPUT_FILE = "processed_disasters_integrated.jsonl"
    
    # Path to your trained model files (in current directory)
    MODEL_PATH = "xgboost_model_20251018_093203.joblib"
    VECTORIZER_PATH = "xgboost_vectorizer_20251018_093203.joblib"
    CONFIG_PATH = "xgboost_config_20251018_093203.json"
    LABEL_ENCODER_PATH = "label_encoder_20251018_093203.joblib"  # Will be created if missing
    
    # Initialize the integrated pipeline
    pipeline = IntegratedDisasterPipeline(
        model_path=MODEL_PATH,
        vectorizer_path=VECTORIZER_PATH,
        config_path=CONFIG_PATH,
        label_encoder_path=LABEL_ENCODER_PATH,
        disaster_threshold=0.75  # Can adjust this - lower = more sensitive
    )
    
    # Process tweets
    pipeline.process_batch(
        input_file=INPUT_FILE,
        output_file=OUTPUT_FILE,
        limit=20,  # None = process all tweets
        max_workers=10  # Parallel workers for LLM calls
    )
    
    # Example: Process a single tweet
    print("\nExample single tweet processing:")
    print("-" * 70)
    
    test_tweets = [
        "Massive earthquake hits California, multiple buildings collapsed",
        "I love sunny days at the beach",
        "Hurricane warning issued for Florida coast",
        "Traffic is terrible today"
    ]
    
    for tweet in test_tweets:
        result = pipeline.process_tweet(
            tweet_id="test",
            tweet_text=tweet
        )
        print(f"\nTweet: {tweet}")
        print(f"Is Disaster: {result['ml_classification']['is_disaster']}")
        if result['ml_classification']['is_disaster']:
            print(f"Type: {result['ml_classification']['disaster_type']}")
            print(f"Confidence: {result['ml_classification']['confidence']:.3f}")
            if result['llm_extraction']:
                print(f"Location: {result['llm_extraction'].get('location')}")
                print(f"Severity: {result['llm_extraction'].get('severity')}")
        print("-" * 70)