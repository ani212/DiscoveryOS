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


# Mount remaining static files directory
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


if __name__ == "__main__":
    import uvicorn
    # Start app server locally on port 8000
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
