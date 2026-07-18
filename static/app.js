/**
 * DiscoveryOS - Client Controller Script.
 * 
 * Handles pre-loading, button clicks, API payloads, loading states,
 * and dynamic table/KPI card updates.
 */

document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements
  const feedbackInput = document.getElementById("feedback-input");
  const modelSelect = document.getElementById("model-select");
  const btnPrefill = document.getElementById("btn-prefill");
  const btnRun = document.getElementById("btn-run");
  const statusBadge = document.getElementById("status-badge");
  
  const loadingState = document.getElementById("loading-state");
  const placeholderState = document.getElementById("placeholder-state");
  const outputContent = document.getElementById("output-content");
  
  const kpiTotalItems = document.getElementById("kpi-total-items");
  const kpiMaxSeverity = document.getElementById("kpi-max-severity");
  const kpiFeaturesCount = document.getElementById("kpi-features-count");
  
  const strategicBriefText = document.getElementById("strategic-brief-text");
  const matrixTbody = document.getElementById("matrix-tbody");

  // In-memory cache for data loaded on start
  let mockFeedbackData = [];

  /**
   * Fetches initial project data on application boot.
   */
  async function loadInitialData() {
    try {
      const response = await fetch("/api/data");
      if (!response.ok) throw new Error("Failed to load project database.");
      const data = await response.json();
      
      // Store mock feedback for prefill action
      if (data.raw_mock && data.raw_mock.length > 0) {
        mockFeedbackData = data.raw_mock;
      }
      
      // If a matrix has already been generated, render it immediately
      if (data.matrix && data.matrix.items && data.matrix.items.length > 0) {
        renderAnalysisResult(data.matrix);
      }
    } catch (err) {
      console.warn("Could not pre-load existing prioritized matrix data:", err.message);
    }
  }

  /**
   * Returns a label and emoji for numerical severity ratings.
   */
  function getSeverityLabel(severity) {
    switch (severity) {
      case 5: return "🔴 Critical (5)";
      case 4: return "🟠 High (4)";
      case 3: return "🟡 Medium (3)";
      case 2: return "🟢 Low (2)";
      default: return "⚪ Minor (1)";
    }
  }

  /**
   * Renders the prioritization matrix payload inside the dashboard.
   */
  function renderAnalysisResult(matrix) {
    // 1. Update status badge
    statusBadge.textContent = "Analysis Complete";
    statusBadge.className = "badge badge-active";
    
    // 2. Hide loading/placeholders, show output content
    loadingState.classList.add("hidden");
    placeholderState.classList.add("hidden");
    outputContent.classList.remove("hidden");
    
    // 3. Update KPI metrics
    const items = matrix.items || [];
    kpiTotalItems.textContent = items.length;
    
    const maxSeverity = items.length > 0 ? Math.max(...items.map(i => i.severity)) : 0;
    kpiMaxSeverity.textContent = maxSeverity > 0 ? getSeverityLabel(maxSeverity) : "-";
    
    const uniqueFeatures = [...new Set(items.map(i => i.feature_area))];
    kpiFeaturesCount.textContent = uniqueFeatures.length;
    
    // 4. Set strategic PM brief text
    strategicBriefText.textContent = matrix.strategic_focus || "No strategic brief generated.";
    
    // 5. Build and render priority matrix rows (sorted by severity descending)
    matrixTbody.innerHTML = "";
    
    const sortedItems = [...items].sort((a, b) => b.severity - a.severity);
    sortedItems.forEach(item => {
      const tr = document.createElement("tr");
      
      const tdArea = document.createElement("td");
      tdArea.innerHTML = `<strong>${item.feature_area}</strong>`;
      
      const tdSegment = document.createElement("td");
      tdSegment.textContent = item.user_segment;
      
      const tdSev = document.createElement("td");
      tdSev.innerHTML = `<span class="sev-pill sev-${item.severity}">${getSeverityLabel(item.severity)}</span>`;
      
      const tdImpact = document.createElement("td");
      tdImpact.textContent = item.business_impact;
      
      const tdAction = document.createElement("td");
      tdAction.textContent = item.product_action;
      
      tr.appendChild(tdArea);
      tr.appendChild(tdSegment);
      tr.appendChild(tdSev);
      tr.appendChild(tdImpact);
      tr.appendChild(tdAction);
      
      matrixTbody.appendChild(tr);
    });
  }

  // Prefill Button Action
  btnPrefill.addEventListener("click", () => {
    if (mockFeedbackData.length === 0) {
      alert("No mock data found to prefill. Please make sure data_ingest.json exists.");
      return;
    }
    
    // Format mock text cleanly into the textarea
    const formatted = mockFeedbackData.map(item => {
      return `Feedback ID: ${item.feedback_id}\nSource: ${item.source}\nUser Email: ${item.user_email}\nText: ${item.text}\n---`;
    }).join("\n\n");
    
    feedbackInput.value = formatted;
  });

  // Run Button Action
  btnRun.addEventListener("click", async () => {
    const textValue = feedbackInput.value.strip ? feedbackInput.value.strip() : feedbackInput.value.trim();
    if (!textValue) {
      alert("Please paste some unstructured feedback before running analysis.");
      return;
    }
    
    // Toggle Loading states
    placeholderState.classList.add("hidden");
    outputContent.classList.add("hidden");
    loadingState.classList.remove("hidden");
    
    statusBadge.textContent = "Analyzing via AI...";
    statusBadge.className = "badge badge-inactive";
    btnRun.disabled = true;
    btnPrefill.disabled = true;
    
    try {
      const payload = {
        feedback_text: textValue,
        model: modelSelect.value
      };
      
      const response = await fetch("/api/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Server error running analysis.");
      }
      
      const result = await response.json();
      renderAnalysisResult(result);
    } catch (err) {
      console.error(err);
      alert(`Prioritization Failed: ${err.message}`);
      
      // Reset layout states on error
      loadingState.classList.add("hidden");
      placeholderState.classList.remove("hidden");
      statusBadge.textContent = "Error";
      statusBadge.className = "badge badge-inactive";
    } finally {
      btnRun.disabled = false;
      btnPrefill.disabled = false;
    }
  });

  // Initialize page on load
  loadInitialData();
});
