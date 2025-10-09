from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional
import json
import re
from pathlib import Path
from datetime import datetime

# Initialize Ollama model
llm = ChatOllama(
    model="llama3.1:8b", 
    temperature=0.2,       # low temp for consistent extraction
    streaming=False
)

# state of workflow
class DisasterState(TypedDict):
    tweet_id: str
    tweet_text: str
    is_disaster: bool
    extracted_data: Optional[dict]
    error: Optional[str]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def parse_json_response(content: str) -> dict:
    """
    Clean and parse JSON from LLM response
    Handles markdown code blocks and extra text
    """
    # remove markdown code blocks if present
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0]
    elif "```" in content:
        content = content.split("```")[1].split("```")[0]
     
    # find JSON object
    json_match = re.search(r'\{.*\}', content, re.DOTALL)
    if json_match:
        content = json_match.group()
    
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        # return empty structure if parsing fails
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

# load tweets from input JSONL file
def load_jsonl(file_path: str) -> list:
    tweets = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                tweets.append(json.loads(line))
    return tweets

# save processed results to output JSONL file
def save_results(results: list, output_path: str):
    with open(output_path, 'w', encoding='utf-8') as f:
        for result in results:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')
    print(f"\nResults saved to: {output_path}")

# node functions
def extract_disaster_info(state: DisasterState) -> DisasterState:
    """
    Extracts structured information from disaster tweet using LLM
    Only called if classifier determined tweet is about a disaster
    """
    prompt = f"""
Extract key information from this natural disaster tweet and return ONLY valid JSON.

Tweet: "{state['tweet_text']}"

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
        state["extracted_data"] = parse_json_response(result.content)
        state["error"] = None
    except Exception as e:
        state["error"] = f"LLM extraction failed: {str(e)}"
        state["extracted_data"] = None
    
    return state

def skip_extraction(state: DisasterState) -> DisasterState:
    """
    Skip LLM extraction if classifier says it's not a disaster
    """
    state["extracted_data"] = None
    state["error"] = "Not classified as disaster - skipped extraction"
    return state

# worflow graph
workflow = StateGraph(DisasterState)

# add nodes
workflow.add_node("extract", extract_disaster_info)
workflow.add_node("skip", skip_extraction)

# conditional routing based on classifier result
def route_based_on_classifier(state: DisasterState) -> str:
    """
    Route to extraction if disaster, skip if not
    """
    return "extract" if state["is_disaster"] else "skip"

# set entry point - starts at routing decision
workflow.set_conditional_entry_point(
    route_based_on_classifier,
    {
        "extract": "extract",
        "skip": "skip"
    }
)

# both paths end the workflow
workflow.add_edge("extract", END)
workflow.add_edge("skip", END)

# compile the graph
graph = workflow.compile()

# main processing function
def process_disaster_tweet(tweet_id: str, tweet_text: str, is_disaster: bool) -> dict:
    """
    Process a single tweet through the pipeline
    
    Args:
        tweet_id: Unique ID from the JSON data
        tweet_text: Raw tweet text
        is_disaster: Boolean from your classifier (target field)
    
    Returns:
        dict with processed results
    """
    initial_state: DisasterState = {
        "tweet_id": tweet_id,
        "tweet_text": tweet_text,
        "is_disaster": is_disaster,
        "extracted_data": None,
        "error": None
    }
    
    # run through the graph
    final_state = graph.invoke(initial_state)
    
    return {
        "id": final_state["tweet_id"],
        "is_disaster": final_state["is_disaster"],
        "extracted_data": final_state["extracted_data"],
        "error": final_state["error"],
        "original_tweet": tweet_text
    }

def process_batch(input_file: str, output_file: str = None, limit: int = None):
    """
    Process batch of tweets from JSONL file
    
    Args:
        input_file: Path to input JSONL file
        output_file: Path to output JSONL file (optional)
        limit: Process only first N tweets (optional, for testing)
    """
    # generate output filename if not provided
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"disaster_results_{timestamp}.jsonl"
    
    print(f"Loading tweets from: {input_file}")
    tweets = load_jsonl(input_file)
    
    if limit:
        tweets = tweets[:limit]
        print(f"Processing first {limit} tweets...")
    else:
        print(f"Processing {len(tweets)} tweets...")
    
    results = []
    
    for i, tweet in enumerate(tweets, 1):
        print(f"\n[{i}/{len(tweets)}] Processing tweet {tweet['id']}...")
        
        result = process_disaster_tweet(
            tweet_id=tweet['id'],
            tweet_text=tweet['text'],
            is_disaster=bool(tweet.get('target', 1))  # use target field as is_disaster
        )
        
        results.append(result)
        
        # print progress
        if result['extracted_data']:
            print(f"Extracted: {result['extracted_data']['disaster_type']} in {result['extracted_data']['location']}")
        else:
            print(f"{result['error']}")
    
    # save results
    save_results(results, output_file)
    
    # print summary
    print("\n" + "=" * 60)
    print("PROCESSING COMPLETE")
    print("=" * 60)
    extracted_count = sum(1 for r in results if r['extracted_data'] is not None)
    print(f"Total processed: {len(results)}")
    print(f"Extracted data: {extracted_count}")
    print(f"Skipped: {len(results) - extracted_count}")

# main execution
if __name__ == "__main__":
    INPUT_FILE = "kaggle_format_posts.jsonl"  
    OUTPUT_FILE = "processed_disasters.jsonl"  
    
    # process all tweets
    # process_batch(INPUT_FILE, OUTPUT_FILE)
    
    # i processed just first 10 for testing:
    process_batch(INPUT_FILE, OUTPUT_FILE, limit=10)