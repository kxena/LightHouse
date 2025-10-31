import sys
from pathlib import Path
# Add parent directory to Python path so we can import fetch_tweets
sys.path.insert(0, str(Path(__file__).parent.parent))

from fetch_tweets.bluesky_connection import scrape_bluesky_tweets
from fetch_tweets.clean_tweets import clean_tweets
from xgboost_classifier.classifier import load_disaster_classifier
import os
import json
from collections import Counter
import numpy as np


def step1_retrieve_tweets():
    
    # Step 1: Retrieve disaster-related tweets from Bluesky
    print("-" * 10)
    print("STEP 1: RETRIEVING TWEETS FROM BLUESKY \n")
    
    # Run the bluesky_connection main function
    scrape_bluesky_tweets()
    
    # Count tweets in output file
    tweet_count = 0
    tweets_file = Path('../fetch_tweets/bluesky_tweets.jsonl')
    if tweets_file.exists():
        with open(tweets_file, 'r') as f:
            tweet_count = sum(1 for _ in f)
    
    print(f"✓ Step 1 complete: {tweet_count} tweets retrieved\n")
    return tweet_count


def step2_clean_tweets():

    # Step 2: Clean and extract important fields from tweets
    print("-" * 10)
    print("STEP 2: CLEANING TWEETS \n")
    
    # Run the clean_tweets main function
    clean_tweets()
    
    # Count cleaned tweets
    cleaned_count = 0
    cleaned_file = Path('../fetch_tweets/clean_tweets.jsonl')
    if cleaned_file.exists():
        with open(cleaned_file, 'r') as f:
            cleaned_count = sum(1 for line in f if not line.startswith('ERROR'))
    
    print(f"✓ Step 2 complete: {cleaned_count} tweets cleaned\n")
    return cleaned_count


def step3_classify_tweets(
    input_file='../fetch_tweets/clean_tweets.jsonl',
    output_file='../DATA_PIPELINE/classified_tweets.jsonl',
    model_dir='../xgboost_classifier'
):
    # Step 3: Classify tweets using XGBoost disaster classifier
    print("-" * 10)
    print("STEP 3: CLASSIFYING TWEETS WITH XGBOOST \n")
    
    # Find the model files
    model_path = Path(model_dir)
    
    xgb_model = model_path / 'xgboost_model.joblib'
    xgb_vectorizer = model_path / 'xgboost_vectorizer.joblib'
    xgb_config = model_path / 'xgboost_config.json'
    
    # Check if files exist
    if not xgb_model.exists():
        raise FileNotFoundError(f"XGBoost model not found at: {xgb_model}")
    if not xgb_vectorizer.exists():
        raise FileNotFoundError(f"Vectorizer not found at: {xgb_vectorizer}")
    if not xgb_config.exists():
        raise FileNotFoundError(f"Config not found at: {xgb_config}")
    
    # Load config first to get classes
    with open(xgb_config, 'r') as f:
        config = json.load(f)
    
    print(f"  Loading model from: {model_dir}")
    
    # Load the classifier
    classifier = load_disaster_classifier(
        model_path=str(xgb_model),
        vectorizer_path=str(xgb_vectorizer),
        config_path=str(xgb_config)
    )
    
    print(f"✓ Model loaded successfully")
    print(f"  Available classes: {', '.join(config['classes'])}")  # Use classes from config
    
    # Read tweets
    print(f"\n  Reading tweets from: {input_file}")
    tweets = []
    tweet_data = []
    
    with open(input_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            try:
                tweet_obj = json.loads(line)
                tweet_text = tweet_obj.get('text', '')
                
                if tweet_text:
                    tweets.append(tweet_text)
                    tweet_data.append(tweet_obj)
                else:
                    print(f"  WARNING: Empty tweet text on line {line_num}")
            except json.JSONDecodeError as e:
                print(f"  WARNING: Error parsing line {line_num}: {e}")

    print(f"✓ Found {len(tweets)} tweets to classify")
    
    if not tweets:
        print("No tweets to classify!")
        return 0
    
    # Classify all tweets
    print("\n  Classifying tweets...")
    predictions = classifier.predict(
        tweets, 
        model_name='xgboost',
        use_optimal_threshold=True
    )
    
    # Get probability scores
    probabilities, classes = classifier.predict_proba(tweets, model_name='xgboost')
    
    # Write results
    print(f"  Writing results to: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        for tweet_obj, prediction, probs in zip(tweet_data, predictions, probabilities):
            confidence = float(probs.max())
            
            classified_tweet = {
                **tweet_obj,
                'classification': {
                    'disaster_type': str(prediction),
                    'confidence': confidence,
                    'probabilities': {
                        str(cls): float(prob) 
                        for cls, prob in zip(classes, probs)
                    }
                }
            }
            
            f.write(json.dumps(classified_tweet) + '\n')
    
    print(f"✓ Classification complete!\n")
    
    # Print summary
    print("-" * 10)
    print("CLASSIFICATION SUMMARY \n")
    
    prediction_counts = Counter(predictions)
    
    print(f"\nTotal tweets classified: {len(predictions)}")
    print(f"\nDisaster type distribution:")
    for disaster_type, count in prediction_counts.most_common():
        percentage = (count / len(predictions)) * 100
        print(f"  {disaster_type:15s}: {count:3d} ({percentage:5.1f}%)")
    
    return len(predictions)


def run_pipeline(model_dir='../xgboost_classifier'):
    
    # Run the complete disaster tweet classification pipeline
    print("DISASTER TWEET CLASSIFICATION PIPELINE")
    print("-" * 10 + "\n")
    
    try:
        # Step 1: Retrieve tweets
        total_retrieved = step1_retrieve_tweets()
        
        # Step 2: Clean tweets
        total_cleaned = step2_clean_tweets()
        
        # Step 3: Classify tweets
        total_classified = step3_classify_tweets(model_dir=model_dir)
        
        # Final summary
        print("\n" + "=" * 60)
        print("✓ PIPELINE COMPLETE!")
        print("=" * 60)
        print(f"\nSummary:")
        print(f"  • Retrieved: {total_retrieved} tweets")
        print(f"  • Cleaned: {total_cleaned} tweets")
        print(f"  • Classified: {total_classified} tweets")
        print(f"\nOutput files:")
        print(f"  • fetch_tweets/bluesky_tweets.jsonl (raw tweets)")
        print(f"  • fetch_tweets/clean_tweets.jsonl (cleaned tweets)")
        print(f"  • DATA_PIPELINE/classified_tweets.jsonl (classified results)")
        print("\n" + "=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Complete pipeline: Retrieve, clean, and classify disaster tweets from Bluesky'
    )
    parser.add_argument(
        '--models-dir', 
        default='../xgboost_classifier', 
        help='Directory containing saved models (default: ../xgboost_classifier)'
    )
    
    args = parser.parse_args()
    
    success = run_pipeline(model_dir=args.models_dir)
    
    exit(0 if success else 1)


if __name__ == "__main__":
    main()