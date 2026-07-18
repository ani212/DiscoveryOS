# DiscoveryOS Advanced PM Features Plan

We are adding advanced product management workflows to **DiscoveryOS**:
1. **Semantic Aggregation & Volume Tracking**: The Pydantic model will group complaints and output user counts (`feedback_count`) and lists of affected user emails (`associated_emails`).
2. **"Ask My Feedback" AI RAG Chat**: A backend endpoint `/api/chat` using Gemini to query the feedback database in real time.
3. **Mock Jira Ticket Integrations**: A backend endpoint `/api/jira/create` to simulate ticket creations, linking them inside the prioritization matrix.
4. **Enhanced UI**: Adding a RAG chat console, volume markers, and a "Create Jira Ticket" button column to the dashboard.

---

## User Review Required

1. **Jira Integration**: Since we do not have live Jira credentials, the Jira API calls will be mocked. It will generate a realistic project ticket key (e.g., `DISC-101`) and standard Jira URL, saving the ticket status into `prioritized_matrix.json` dynamically.
2. **Schema Upgrade**: The Pydantic schema will be updated to include `feedback_count`, `associated_emails`, and optional `jira_key` variables.

---

## Proposed Changes

### Component: AI Engine & Data Models

#### [MODIFY] [discovery_engine.py](file:///e:/WORK/Antigravity/DiscoveryOS/discovery_engine.py)
* Update `FeedbackItem` schema:
  - Add `feedback_count: int` (number of similar complaints).
  - Add `associated_emails: List[str]` (emails of users who complained about this).
  - Add `jira_key: Optional[str] = None` (linked Jira ticket ID).

### Component: FastAPI Backend Server

#### [MODIFY] [app.py](file:///e:/WORK/Antigravity/DiscoveryOS/app.py)
* Add `POST /api/chat` endpoint:
  - Takes a user prompt.
  - Sends a context-aware prompt to Gemini combining all customer feedback and the generated matrix.
  - Returns the AI-generated answer.
* Add `POST /api/jira/create` endpoint:
  - Takes a `feature_area` and `product_action`.
  - Generates a ticket key (e.g., `DISC-101`).
  - Updates the corresponding item in `prioritized_matrix.json` to persist the `jira_key`.

### Component: Interactive Dashboard UI

#### [MODIFY] [static/index.html](file:///e:/WORK/Antigravity/DiscoveryOS/static/index.html)
* Update table headers to include **Volume** and **Action**.
* Add a new section **💬 Chat with Product Feedback** below the matrix table containing a chat logs feed and input field.

#### [MODIFY] [static/style.css](file:///e:/WORK/Antigravity/DiscoveryOS/static/style.css)
* Add styling for chat container, user/system message bubbles, and action buttons.
* Add hover states for interactive rows showing affected users.

#### [MODIFY] [static/app.js](file:///e:/WORK/Antigravity/DiscoveryOS/static/app.js)
* Update table builder to render volume counts and Jira buttons.
* Implement AJAX request for creating Jira tickets and updating the specific row dynamically.
* Implement chat form submission to `/api/chat` showing a typing indicator.

---

## Verification Plan

### Automated / CLI Verification
1. Re-run `discovery_engine.py` to confirm the schema upgrade parses correctly.
2. Run the FastAPI server: `.\venv\Scripts\python app.py`.

### Manual / Browser Verification
1. Visit `http://localhost:8000`.
2. Load mock data and run analysis.
3. Check if the table displays **Volume** (e.g. `👥 1 user`) and a **[🎫 Create Ticket]** button.
4. Click **Create Ticket**, verify it displays a link to Jira (e.g. `DISC-101`), and check `prioritized_matrix.json` to verify the state persisted.
5. Paste a query into the feedback chat box (e.g., *"Why are growth users unhappy?"*) and verify the AI response is displayed.
