# DiscoveryOS 🧠

**Author:** Aniket Bhattacharjee

DiscoveryOS is an advanced AI-powered product intelligence platform designed to extract actionable insights from unstructured customer feedback. It automatically processes data from support tickets, portal requests, and surveys to generate a prioritized matrix and a comprehensive markdown dashboard.

Powered by the latest `google-genai` SDK and Pydantic (v2), it ensures strict schema validation on LLM outputs and features robust fallback mechanisms and model thinking configurations.

## 🚀 Features
- **Structured JSON schemas**: Strictly validated via Pydantic v2.
- **Robust Model Fallbacks**: Automatically fall back to alternative Gemini models if the requested preview model is unavailable.
- **Thinking Budget Config**: Utilizes the thinking capability of Gemini models (e.g. `gemini-3.5-flash`) for deep, strategic PM summaries.
- **Markdown Dashboard**: Renders a beautiful report with blockquotes, KPI metrics, and a prioritization matrix sorted by severity.

---

## 🛠️ Getting Started

### 1. Installation
Clone the repository and install the dependencies in a virtual environment:
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
.\venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 2. Configuration
Create a `.env` file in the root folder and add your Gemini API key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Usage

#### Run the prioritize engine:
Parse unstructured inputs from `data_ingest.json` and generate `prioritized_matrix.json`:
```bash
python discovery_engine.py
```

#### Generate the presentation-ready dashboard:
Convert the prioritization matrix to a beautiful dashboard file `DASHBOARD.md`:
```bash
python render_dashboard.py
```

---

## 📁 Repository Structure
- `app.py`: FastAPI server serving static layouts and hosting `/api/chat` and `/api/jira/create` endpoints.
- `static/`: HTML, CSS, and JS web dashboard frontend codes.
- `data_ingest.json`: Mock database of unstructured customer feedback items.
- `discovery_engine.py`: AI extraction, reasoning, and local schema validation.
- `render_dashboard.py`: Parses the JSON matrix and renders the presentation dashboard.
- `DASHBOARD.md`: Generated intelligence dashboard markdown report.
- `docs/`: Technical specifications containing the [implementation_plan.md](docs/implementation_plan.md), [walkthrough.md](docs/walkthrough.md), and [task.md](docs/task.md) checklists.
