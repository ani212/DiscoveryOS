"""
DiscoveryOS - Automated Product Intelligence Engine.

This script parses unstructured customer feedback (interviews, tickets, etc.)
and outputs a quantitative prioritization matrix using Gemini and Pydantic v2.
It leverages the google-genai SDK and implements defensive fallbacks for
model availability and thinking configuration compatibility.
"""

import os
import json
import argparse
import sys
from typing import List, Optional
from pydantic import BaseModel, Field, ValidationError
from dotenv import load_dotenv

# Try importing the new google-genai SDK
try:
    from google import genai
    from google.genai import types
except ImportError:
    print("Error: The 'google-genai' library is not installed.", file=sys.stderr)
    print("Please install it using: pip install google-genai", file=sys.stderr)
    sys.exit(1)


# Define Pydantic v2 Models for strict structured JSON output enforcement

class FeedbackItem(BaseModel):
    """
    Model representing a single parsed and prioritized feedback item.
    """
    feature_area: str = Field(
        ..., 
        description="The functional area of the product this feedback belongs to (e.g., Authentication, Exports, UI/UX)."
    )
    user_segment: str = Field(
        ..., 
        description="The segment of the user offering feedback (e.g., Enterprise, Growth, Churning)."
    )
    severity: int = Field(
        ..., 
        ge=1, 
        le=5, 
        description="Severity rating from 1 (lowest/minor annoyance) to 5 (highest/blocker)."
    )
    product_action: str = Field(
        ..., 
        description="A concise, 1-sentence roadmap directive or action to address this issue."
    )
    business_impact: str = Field(
        ..., 
        description="Description of the business impact (e.g., risk of churn, revenue loss, low user engagement)."
    )
    feedback_count: int = Field(
        1,
        description="The number of users who raised complaints related to this feature area and issue."
    )
    associated_emails: List[str] = Field(
        default_factory=list,
        description="A list of unique emails of users associated with these feedback complaints."
    )
    jira_key: Optional[str] = Field(
        None,
        description="Jira ticket key if already created (e.g., 'DISC-101'), default is None."
    )


class DiscoveryAnalysis(BaseModel):
    """
    Top-level model representing the complete discovery analysis report.
    """
    strategic_focus: str = Field(
        ..., 
        description="A top-level strategic focus summary brief synthesizing all feedback."
    )
    items: List[FeedbackItem] = Field(
        ..., 
        description="List of parsed feedback items with quantitative matrix attributes."
    )


def load_feedback_data(filepath: str) -> str:
    """
    Loads mock unstructured feedback records from a JSON file and formats them.

    Args:
        filepath: The path to the json feedback file.

    Returns:
        A formatted string representation of all feedback items.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Feedback data file not found at: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Format unstructured text for LLM ingestion
    formatted_texts = []
    for item in data:
        formatted_texts.append(
            f"Feedback ID: {item.get('feedback_id', 'N/A')}\n"
            f"Source: {item.get('source', 'N/A')}\n"
            f"User Email: {item.get('user_email', 'N/A')}\n"
            f"Text: {item.get('text', '')}\n"
            f"---"
        )
    return "\n\n".join(formatted_texts)


def run_analysis_for_model(client: genai.Client, model_name: str, feedback_text: str) -> DiscoveryAnalysis:
    """
    Attempts to call Gemini with a structured output schema, with and without thinking config.

    Args:
        client: The Gemini API client instance.
        model_name: The name of the Gemini model to invoke.
        feedback_text: The formatted string containing feedback records.

    Returns:
        A validated DiscoveryAnalysis Pydantic object.
    """
    # Define prompt instructions for analysis
    prompt = (
        "You are a Principal Software Engineer and AI Product Manager. "
        "Analyze the following unstructured user feedback records. Group similar complaints into a single feature_area. "
        "For each grouped item, calculate the feedback_count (the number of users reporting this issue) and collect all unique associated_emails (the emails of the users reporting this issue). "
        "For each grouped item, define the severity (1 to 5), a 1-sentence product_action roadmap directive, and business_impact. "
        "Synthesize all items to write a high-level strategic_focus summary brief.\n\n"
        f"Feedback Records:\n{feedback_text}"
    )

    # Attempt 1: Structured JSON + Thinking Config (if supported by model/SDK version)
    try:
        print(f" -> Attempting analysis with model '{model_name}' and thinking budget config...")
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=DiscoveryAnalysis,
            thinking_config=types.ThinkingConfig(
                thinking_budget=1024,
            ),
            temperature=0.1,
        )
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config,
        )
        return DiscoveryAnalysis.model_validate_json(response.text)
    except Exception as e:
        print(f"    [Info] Thinking budget execution failed or is not supported: {e}")
        print("    [Info] Falling back to standard structured output configuration...")

    # Attempt 2: Structured JSON without Thinking Config
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=DiscoveryAnalysis,
        temperature=0.1,
    )
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=config,
    )
    return DiscoveryAnalysis.model_validate_json(response.text)


def analyze_feedback(client: genai.Client, initial_model: str, feedback_text: str) -> DiscoveryAnalysis:
    """
    Tries a list of candidate models sequentially to perform feedback analysis.

    Args:
        client: The Gemini API client instance.
        initial_model: The user's preferred model.
        feedback_text: The feedback text.

    Returns:
        The validated DiscoveryAnalysis model.
    """
    # Build list of fallback models
    models_to_try = [initial_model]
    fallbacks = ["gemini-3.5-flash", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
    for f in fallbacks:
        if f not in models_to_try:
            models_to_try.append(f)

    last_error = None
    for model in models_to_try:
        try:
            result = run_analysis_for_model(client, model, feedback_text)
            print(f" -> Successfully analyzed using model '{model}'.")
            return result
        except Exception as e:
            print(f"    [Warning] Failed with model '{model}': {e}")
            last_error = e

    print("Error: All fallback attempts failed.", file=sys.stderr)
    raise last_error


def main():
    # Load environment variables
    # Try current folder first, then parent directory (root folder of the workspace)
    load_dotenv()
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

    # Argument Parser
    parser = argparse.ArgumentParser(description="DiscoveryOS - Automated Product Intelligence Engine")
    parser.add_argument(
        "--input", 
        default="data_ingest.json", 
        help="Path to the input JSON file (default: data_ingest.json)"
    )
    parser.add_argument(
        "--output", 
        default="prioritized_matrix.json", 
        help="Path to the output JSON file (default: prioritized_matrix.json)"
    )
    parser.add_argument(
        "--model", 
        default="antigravity-preview-05-2026", 
        help="Gemini model name to use (default: antigravity-preview-05-2026)"
    )
    args = parser.parse_args()

    # Resolve paths relative to this script's directory if they are relative
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = args.input if os.path.isabs(args.input) else os.path.join(script_dir, args.input)
    output_path = args.output if os.path.isabs(args.output) else os.path.join(script_dir, args.output)

    print("=== DiscoveryOS Product Intelligence Engine ===")
    
    # 1. Ingest
    try:
        print(f"Ingesting unstructured data from: {input_path}")
        feedback_text = load_feedback_data(input_path)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Failed to parse input file '{input_path}' as valid JSON.", file=sys.stderr)
        sys.exit(1)

    # 2. Authenticate & Analyze
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Warning: GEMINI_API_KEY environment variable is not set.", file=sys.stderr)
        print("Please check your .env file or set it in your environment.", file=sys.stderr)
        print("Attempting client initialization without an explicit key...", file=sys.stderr)

    try:
        # Initialize Google GenAI client (picks up GEMINI_API_KEY from environment automatically)
        client = genai.Client()
        analysis = analyze_feedback(client, args.model, feedback_text)
    except Exception as e:
        print(f"\nExecution error while calling Gemini API: {e}", file=sys.stderr)
        sys.exit(1)

    # 3. Export
    try:
        # Pydantic v2 serializes model to python dict / json
        output_data = analysis.model_dump()
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2)
        print(f"Success: Matrix successfully written to {output_path}")
    except Exception as e:
        print(f"Error: Failed to write output file: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
