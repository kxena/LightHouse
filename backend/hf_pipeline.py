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
    openai_api_key="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",
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
    1. ML Classifier (XGBoost/Random Forest/Logistic Regression) determines:
       - Is this a disaster tweet? (binary classification)
       - What type of disaster? (multi-class classification)
       - Confidence scores
    
    2. LLM Extraction (only for disaster tweets) extracts:
       - Detailed structured information
       - Location, time, severity
       - Casualties, damage, help requests
    """
    
    def __init__(self, model_dir: str = './models', 
                 model_name: str = 'xgboost',
                 use_optimal_thresholds: bool = True):
        """
        Initialize the integrated pipeline.
        
        Args:
            model_dir: Directory containing trained models
            model_name: Which classifier to use ('xgboost', 'random_forest', 'logistic_regression')
            use_optimal_thresholds: Use precision-optimized thresholds
        """
        self.model_name = model_name
        self.use_optimal_thresholds = use_optimal_thresholds
        self.classifier = None
        
        # Try to load the classifier
        if DisasterClassifier:
            try:
                self.load_classifier(model_dir)
            except Exception as e:
                print(f"Warning: Could not load classifier: {e}")
                print("Pipeline will run in LLM-only mode.")
        
        # Build the LangGraph workflow
        self.graph = self._build_graph()
    
    def load_classifier(self, model_dir: str):
        """Load the trained ML classifier"""
        print(f"\nLoading ML classifier from {model_dir}...")
        self.classifier = DisasterClassifier()
        self.classifier.load_models_from_directory(model_dir)
        print(f"✓ Loaded {self.model_name} classifier\n")
    
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
        """
        if self.classifier is None:
            # Fallback: assume all tweets are disasters (LLM will handle it)
            state["is_disaster"] = True
            state["disaster_type"] = "unknown"
            state["confidence"] = 0.5
            state["error"] = "ML classifier not available - using LLM only mode"
            return state
        
        try:
            # Get prediction from ML classifier
            predictions = self.classifier.predict(
                [state["tweet_text"]], 
                model_name=self.model_name,
                use_optimal_threshold=self.use_optimal_thresholds
            )
            
            # Get confidence scores
            probabilities, classes = self.classifier.predict_proba(
                [state["tweet_text"]], 
                model_name=self.model_name
            )
            
            predicted_type = predictions[0]
            confidence = probabilities[0].max()
            
            # Determine if it's a disaster (anything except 'not_disaster' or similar)
            # You may need to adjust this based on your actual class labels
            is_disaster = predicted_type.lower() not in ['not_disaster', 'unknown', 'none']
            
            state["is_disaster"] = is_disaster
            state["disaster_type"] = predicted_type if is_disaster else None
            state["confidence"] = float(confidence)
            state["error"] = None
            
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
        if not state.get("error"):
            state["error"] = f"ML classifier: not a disaster (confidence: {state.get('confidence', 0):.2f})"
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
        print(f"ML Classifier: {self.model_name}")
        print(f"Optimal Thresholds: {self.use_optimal_thresholds}")
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
                    tweets.append(json.loads(line))
                    if limit and len(tweets) >= limit:
                        break
        return tweets
    
    @staticmethod
    def _save_results(results: list, output_path: str):
        """Save processed results to output JSONL file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            for result in results:
                f.write(json.dumps(result, ensure_ascii=False) + '\n')
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
        
        print(f"Total processed: {len(results)}")
        print(f"Total time: {elapsed:.2f}s")
        print(f"Average per tweet: {elapsed/len(results):.2f}s")
        print(f"\nML Classification:")
        print(f"  Disasters detected: {disaster_count}")
        print(f"  Non-disasters: {len(results) - disaster_count}")
        print(f"\nLLM Extraction:")
        print(f"  Successful extractions: {extracted_count}")
        print(f"  Errors: {error_count}")
        print("="*70 + "\n")


# Example usage and main execution
if __name__ == "__main__":
    # Configuration
    INPUT_FILE = "kaggle_format_posts.jsonl"
    OUTPUT_FILE = "processed_disasters_integrated.jsonl"
    MODEL_DIR = "./models"  # Directory where your trained models are saved
    
    # Choose which ML model to use:
    # 'xgboost' - Best overall performance (recommended)
    # 'random_forest' - Good balance of speed and accuracy
    # 'logistic_regression' - Fastest, good baseline
    MODEL_NAME = "xgboost"
    
    # Initialize the integrated pipeline
    pipeline = IntegratedDisasterPipeline(
        model_dir=MODEL_DIR,
        model_name=MODEL_NAME,
        use_optimal_thresholds=True  # Use precision-optimized thresholds
    )
    
    # Process tweets
    # Adjust limit and max_workers 
    pipeline.process_batch(
        input_file=INPUT_FILE,
        output_file=OUTPUT_FILE,
        limit=20,  # None = process all tweets, or set a number like 100
        max_workers=5  # Parallel workers for LLM calls
    )
    
    # Example: Process a single tweet
    print("\nExample single tweet processing:")
    result = pipeline.process_tweet(
        tweet_id="example_001",
        tweet_text="Massive earthquake hits California, multiple buildings collapsed"
    )
    print(json.dumps(result, indent=2))