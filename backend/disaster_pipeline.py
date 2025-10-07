"""
Natural Disaster Tweet Processing Pipeline
MVP: Tweet -> Classifier -> LLM Extraction -> Structured JSON Output
"""

from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional
import json
import re

# Initialize Ollama model
llm = ChatOllama(
    model="llama3.1:8b",  # or qwen2.5-coder:1.5b
    temperature=0.2,       # low temp for consistent extraction
    streaming=False
)

# Define the state of your workflow
class DisasterState(TypedDict):
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
    # Remove markdown code blocks if present
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0]
    elif "```" in content:
        content = content.split("```")[1].split("```")[0]
    
    # Remove any text before/after JSON
    content = content.strip()
    
    # Find JSON object
    json_match = re.search(r'\{.*\}', content, re.DOTALL)
    if json_match:
        content = json_match.group()
    
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        # Return empty structure if parsing fails
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

# ============================================================================
# NODE FUNCTIONS
# ============================================================================

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

# ============================================================================
# BUILD WORKFLOW GRAPH
# ============================================================================

workflow = StateGraph(DisasterState)

# Add nodes
workflow.add_node("extract", extract_disaster_info)
workflow.add_node("skip", skip_extraction)

# Conditional routing based on classifier result
def route_based_on_classifier(state: DisasterState) -> str:
    """
    Route to extraction if disaster, skip if not
    """
    return "extract" if state["is_disaster"] else "skip"

# Set entry point - starts at routing decision
workflow.set_conditional_entry_point(
    route_based_on_classifier,
    {
        "extract": "extract",
        "skip": "skip"
    }
)

# Both paths end the workflow
workflow.add_edge("extract", END)
workflow.add_edge("skip", END)

# Compile the graph
graph = workflow.compile()

# ============================================================================
# MAIN FUNCTION FOR FASTAPI
# ============================================================================

def process_disaster_tweet(tweet_text: str, is_disaster: bool) -> dict:
    """
    Main function to process tweet through the pipeline
    
    Args:
        tweet_text: Raw tweet text from your data
        is_disaster: Boolean from your classifier
    
    Returns:
        dict with:
            - is_disaster: bool
            - extracted_data: dict or None
            - error: str or None
    """
    initial_state: DisasterState = {
        "tweet_text": tweet_text,
        "is_disaster": is_disaster,
        "extracted_data": None,
        "error": None
    }
    
    # Run through the graph
    final_state = graph.invoke(initial_state)
    
    return {
        "is_disaster": final_state["is_disaster"],
        "extracted_data": final_state["extracted_data"],
        "error": final_state["error"],
        "original_tweet": tweet_text
    }

# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("Natural Disaster Tweet Processing Pipeline")
    print("=" * 60)
    
    # Test cases
    test_tweets = [
        {
            "text": "Major earthquake hits San Francisco. Buildings collapsed, casualties reported. Magnitude 7.2",
            "is_disaster": True
        },
        {
            "text": "Severe flooding in Houston. Roads closed, evacuations underway. Need emergency supplies.",
            "is_disaster": True
        },
        {
            "text": "Beautiful sunny day today! Going to the beach 🏖️",
            "is_disaster": False
        }
    ]
    
    for i, test in enumerate(test_tweets, 1):
        print(f"\n--- Test {i} ---")
        print(f"Tweet: {test['text']}")
        print(f"Classifier says disaster: {test['is_disaster']}")
        
        result = process_disaster_tweet(test['text'], test['is_disaster'])
        
        print(f"\nResult:")
        if result['extracted_data']:
            print(json.dumps(result['extracted_data'], indent=2))
        else:
            print(f"No extraction: {result['error']}")
        print("-" * 60)