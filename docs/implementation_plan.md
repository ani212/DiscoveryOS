# DiscoveryOS Export & Sharing Features Plan

We are adding structured sharing and export tools to **DiscoveryOS**, focusing on **high readability, clean layouts, and non-confusing user interfaces**.

---

## User Review Required

* **Client-Side Processing**: We will build these tools using client-side JavaScript and CSS print configurations. This guarantees zero server lag, instantaneous downloads, and maximum reliability.
* **Aesthetic Focus (Clean Business Style)**: 
  - The printed/saved PDF layout will convert to a high-contrast corporate brief style (black text, clean gridlines, no dark backgrounds) to ensure perfect printing on paper.
  - Buttons will feature descriptive labels (e.g., *"📄 Export PDF Report"* instead of just *"PDF"*) to be completely self-explanatory.

---

## Proposed Changes

### Component: Dashboard UI & Styling

#### [MODIFY] [static/index.html](file:///e:/WORK/Antigravity/DiscoveryOS/static/index.html)
* Add an **Export & Sharing Toolbar** inside the results panel header.
* Include descriptive action buttons:
  - `[📄 Export PDF Report]`
  - `[📊 Download Excel/CSV]`
  - `[📋 Copy Notion Markdown]`

#### [MODIFY] [static/style.css](file:///e:/WORK/Antigravity/DiscoveryOS/static/style.css)
* Style the sharing toolbar to fit cleanly inside the header.
* Add a comprehensive `@media print` style block:
  - Automatically hides inputs, panels, scrollbars, and buttons.
  - Switches the dark-theme colors to standard document formats (charcoal text on clean white pages).
  - Handles table page-breaks (`page-break-inside: avoid`) to prevent rows from being split across page sheets.

#### [MODIFY] [static/app.js](file:///e:/WORK/Antigravity/DiscoveryOS/static/app.js)
* Connect event listeners to compile and format structured outputs:
  - **Export PDF Report**: Opens browser print options.
  - **Download CSV**: Generates a clean table with appropriate CSV columns (Feature, Segment, Severity, Volume, Business Impact, Product Action) for Excel.
  - **Copy Notion Markdown**: Copies a fully formatted table block. Temporarily changes button text to `[✓ Copied!]` for clear user feedback.

---

## Verification Plan

### Manual / Browser Verification
1. Visit the local dashboard (`http://localhost:8000`).
2. Run an analysis to populate the table.
3. Click **Download Excel/CSV**: Confirm the file is readable and columns match.
4. Click **Copy Notion Markdown**: Verify that pasting into Notion or Slack displays a clean grid table.
5. Click **Export PDF Report**: Inspect the print layout preview to ensure it is clean, legible, and formatted like a professional document.
