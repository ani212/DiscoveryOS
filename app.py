"""
DiscoveryOS FastAPI Backend.

Provides API endpoints to trigger AI feedback analysis, load raw mock feedback,
and fetch current prioritization matrices. Also serves the glassmorphic web dashboard.
"""

import os
import json
import sys
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import List

# Ensure we can load discovery_engine modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from discovery_engine import analyze_feedback, DiscoveryAnalysis, genai, load_dotenv

# Load configurations
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

app = FastAPI(title="DiscoveryOS AI Intelligence Portal")

# Resolve folders
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
DATA_INGEST_PATH = os.path.join(BASE_DIR, "data_ingest.json")
MATRIX_PATH = os.path.join(BASE_DIR, "prioritized_matrix.json")

# Ensure static folder exists
os.makedirs(STATIC_DIR, exist_ok=True)


class AnalyzeRequest(BaseModel):
    """
    Payload containing raw feedback text to prioritize.
    """
    feedback_text: str = Field(..., description="Unstructured customer feedback text lines.")
    model: str = Field("gemini-3.5-flash", description="Preferred Gemini model name.")


class ChatRequest(BaseModel):
    """
    Payload containing chat message query.
    """
    message: str = Field(..., description="The query string from the AI PM.")
    model: str = Field("gemini-3.5-flash", description="Preferred Gemini model name.")


class JiraRequest(BaseModel):
    """
    Payload to trigger mock Jira ticket creation.
    """
    feature_area: str = Field(..., description="The feature area identifier.")
    product_action: str = Field(..., description="Roadmap directive string.")


@app.get("/")
def read_root():
    """
    Serves the primary UI dashboard index.html.
    """
    index_path = os.path.join(STATIC_DIR, "index.html")
    if not os.path.exists(index_path):
        return HTMLResponse(
            content="<h3>DiscoveryOS frontend is initializing. Please refresh in a moment...</h3>",
            status_code=202
        )
    return FileResponse(index_path)


@app.get("/api/data")
def get_data():
    """
    Returns existing prioritization matrix outputs and raw mock databases.
    """
    # 1. Load mock ingest data
    raw_mock = []
    if os.path.exists(DATA_INGEST_PATH):
        try:
            with open(DATA_INGEST_PATH, 'r', encoding='utf-8') as f:
                raw_mock = json.load(f)
        except Exception:
            pass

    # 2. Load generated prioritized matrix
    matrix = {}
    if os.path.exists(MATRIX_PATH):
        try:
            with open(MATRIX_PATH, 'r', encoding='utf-8') as f:
                matrix = json.load(f)
        except Exception:
            pass

    return {
        "raw_mock": raw_mock,
        "matrix": matrix
    }


@app.post("/api/analyze")
def run_analysis(payload: AnalyzeRequest):
    """
    Triggers the AI prioritization analysis pipeline.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY environment variable is not configured on the server."
        )

    if not payload.feedback_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Feedback text cannot be empty."
        )

    try:
        # Initialize the GenAI Client
        client = genai.Client()
        # Trigger Pydantic structured output analysis
        analysis = analyze_feedback(client, payload.model, payload.feedback_text)
        
        # Save output to disk
        output_data = analysis.model_dump()
        with open(MATRIX_PATH, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2)
            
        # Dynamically trigger dashboard rendering to keep DASHBOARD.md synchronized
        try:
            from render_dashboard import render_markdown
            DASHBOARD_PATH = os.path.join(BASE_DIR, "DASHBOARD.md")
            render_markdown(output_data, DASHBOARD_PATH)
        except Exception as render_err:
            print(f"Warning: Dashboard markdown sync failed: {render_err}")
            
        return output_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat")
def run_chat(payload: ChatRequest):
    """
    RAG chat endpoint to answer user questions about current feedback databases.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY environment variable is not set.")

    # Read feedback dataset
    raw_context = ""
    if os.path.exists(DATA_INGEST_PATH):
        try:
            with open(DATA_INGEST_PATH, 'r', encoding='utf-8') as f:
                raw_context = f.read()
        except Exception:
            pass

    # Read matrix outputs
    matrix_context = ""
    if os.path.exists(MATRIX_PATH):
        try:
            with open(MATRIX_PATH, 'r', encoding='utf-8') as f:
                matrix_context = f.read()
        except Exception:
            pass

    prompt = (
        "You are an AI Product Manager assistant for DiscoveryOS.\n"
        "Provide a concise, helpful, and insightful response to the user's questions. "
        "Base your answer on the customer feedback dataset and generated prioritization matrix contexts provided below.\n\n"
        f"Context 1 (Raw Customer Feedback):\n{raw_context}\n\n"
        f"Context 2 (Prioritization Matrix):\n{matrix_context}\n\n"
        f"User Question: {payload.message}"
    )

    try:
        client = genai.Client()
        response = client.models.generate_content(
            model=payload.model,
            contents=prompt
        )
        return {"response": response.text.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/jira/create")
def create_jira_ticket(payload: JiraRequest):
    """
    Mock endpoint to generate a Jira ticket key and link it inside the JSON matrix.
    """
    if not os.path.exists(MATRIX_PATH):
        raise HTTPException(status_code=400, detail="Prioritization matrix file does not exist.")

    try:
        with open(MATRIX_PATH, 'r', encoding='utf-8') as f:
            matrix_data = json.load(f)

        items = matrix_data.get("items", [])
        target_item = None

        # Find matching item
        for item in items:
            if item.get("feature_area") == payload.feature_area and item.get("product_action") == payload.product_action:
                target_item = item
                break

        if not target_item:
            raise HTTPException(status_code=404, detail="Matching feedback item not found in matrix.")

        # Generate mock ticket key (e.g. DISC-742)
        import random
        ticket_num = random.randint(101, 999)
        ticket_key = f"DISC-{ticket_num}"

        # Save to item
        target_item["jira_key"] = ticket_key

        # Persist update
        with open(MATRIX_PATH, 'w', encoding='utf-8') as f:
            json.dump(matrix_data, f, indent=2)

        return {
            "status": "success",
            "jira_key": ticket_key,
            "jira_url": f"https://jira.atlassian.com/browse/{ticket_key}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Mount remaining static files directory
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


if __name__ == "__main__":
    import uvicorn
    # Start app server locally on port 8000
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
