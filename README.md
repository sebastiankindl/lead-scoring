# Lead Scoring Tool

A lightweight **strategic lead intelligence tool** that turns unstructured company websites into **actionable sales priorities** using an explainable scoring model.

## Why This Exists
Industrial sales teams often spend significant time manually screening leads before deciding who to contact first.
This tool automates the first-pass qualification step and produces a **ranked outreach list** with:
- **Priority bucket (A/B/C)**
- **Primary sector fit**
- **Why call next**
- **Recommended action**
- **Key signals**

## Demo
- CSV upload
- Country-based filtering for target regions
- Batch website audit
- Ranked output + enriched CSV download

> Screenshot: `assets/screenshot_ui.png`

## How It Works
1. Fetch website HTML
2. Extract text by context: `title`, `h1`, `body`, `footer`
3. Apply weighted keyword ontology
4. Compute:
   - Strategic score
   - Percentile + Priority bucket
   - Confidence
   - Optional: Executive output fields (“Why call next”, “Recommended action”)

## Project Structure
- `engine/` — reusable scoring engine (ontology + scraper + scoring)
- `ui/` — streamlit interface
- `data/` — sample CSV
- `assets/` — screenshots

## Quickstart
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

PYTHONPATH=. streamlit run ui/app.py
```

## Input Format (CSV)
Minimum required:
- Company_Name (or similar)
- Website

Optional:
- Country

An example file is provided in
```markdown
data/sample_leads.csv
```

## Domain Adaptation
The engine is designed as a flexible framework and must be adapted to the specific use case.
To deliver meaningful results, it needs to be tailored by:
- defining relevant keywords and ontology mappings
- selecting appropriate data sources for web scraping
- adjusting the scoring model to match the business objective

## Notes / Limitations
- This tool is designed for demonstation and internal analysis
- Results depend on website content and quality