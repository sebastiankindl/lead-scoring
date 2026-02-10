import time
import pandas as pd
import streamlit as st
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine import normalize_url, fetch_html, extract_context_texts, score_lead

# country list (ISO 3166)
ALL_COUNTRIES = [
    "Afghanistan","Albania","Algeria","Andorra","Angola","Antigua and Barbuda","Argentina","Armenia","Australia",
    "Austria","Azerbaijan","Bahamas","Bahrain","Bangladesh","Barbados","Belarus","Belgium","Belize","Benin","Bhutan",
    "Bolivia","Bosnia and Herzegovina","Botswana","Brazil","Brunei","Bulgaria","Burkina Faso","Burundi","Cabo Verde",
    "Cambodia","Cameroon","Canada","Central African Republic","Chad","Chile","China","Colombia","Comoros","Congo",
    "Costa Rica","Côte d’Ivoire","Croatia","Cuba","Cyprus","Czechia","Denmark","Djibouti","Dominica","Dominican Republic",
    "Ecuador","Egypt","El Salvador","Equatorial Guinea","Eritrea","Estonia","Eswatini","Ethiopia","Fiji","Finland","France",
    "Gabon","Gambia","Georgia","Germany","Ghana","Greece","Grenada","Guatemala","Guinea","Guinea-Bissau","Guyana","Haiti",
    "Honduras","Hungary","Iceland","India","Indonesia","Iran","Iraq","Ireland","Israel","Italy","Jamaica","Japan","Jordan",
    "Kazakhstan","Kenya","Kiribati","Kuwait","Kyrgyzstan","Laos","Latvia","Lebanon","Lesotho","Liberia","Libya",
    "Liechtenstein","Lithuania","Luxembourg","Madagascar","Malawi","Malaysia","Maldives","Mali","Malta","Marshall Islands",
    "Mauritania","Mauritius","Mexico","Micronesia","Moldova","Monaco","Mongolia","Montenegro","Morocco","Mozambique",
    "Myanmar","Namibia","Nauru","Nepal","Netherlands","New Zealand","Nicaragua","Niger","Nigeria","North Korea",
    "North Macedonia","Norway","Oman","Pakistan","Palau","Panama","Papua New Guinea","Paraguay","Peru","Philippines",
    "Poland","Portugal","Qatar","Romania","Russia","Rwanda","Saint Kitts and Nevis","Saint Lucia",
    "Saint Vincent and the Grenadines","Samoa","San Marino","Sao Tome and Principe","Saudi Arabia","Senegal","Serbia",
    "Seychelles","Sierra Leone","Singapore","Slovakia","Slovenia","Solomon Islands","Somalia","South Africa","South Korea",
    "South Sudan","Spain","Sri Lanka","Sudan","Suriname","Sweden","Switzerland","Syria","Taiwan","Tajikistan","Tanzania",
    "Thailand","Timor-Leste","Togo","Tonga","Trinidad and Tobago","Tunisia","Turkey","Turkmenistan","Tuvalu","Uganda",
    "Ukraine","United Arab Emirates","United Kingdom","United States","Uruguay","Uzbekistan","Vanuatu","Vatican City",
    "Venezuela","Vietnam","Yemen","Zambia","Zimbabwe"
]

st.set_page_config(page_title="WERBA Lead Engine Pro", layout="wide")
st.title("Lead Scoring Engine")
st.markdown("### Strategic Sales Tool")

# target regions
default_regions = ["Sweden", "Norway", "Denmark", "Finland", "Belgium", "Netherlands", "Luxembourg", "Italy"]
target_regions = st.multiselect(
    "Target Regions",
    options=ALL_COUNTRIES,
    default=[c for c in default_regions if c in ALL_COUNTRIES],
)

uploaded_file = st.file_uploader("Upload Lead List", type="csv")

if uploaded_file:
    def read_csv_robust(file):
        try:
            return pd.read_csv(file, encoding="utf-8")
        except UnicodeDecodeError:
            file.seek(0)
            try:
                return pd.read_csv(file, encoding="cp1252")  # windows/excel
            except UnicodeDecodeError:
                file.seek(0)
                return pd.read_csv(file, encoding="latin-1")

    input_df = read_csv_robust(uploaded_file)

    # country column selection
    country_col = st.selectbox(
        "Select the column containing the Country (optional):",
        options=["—"] + list(input_df.columns),
        index=1 if "Country" in input_df.columns else 0,
    )

    # apply country filter - preview
    filtered_df = input_df.copy()
    if target_regions and country_col != "—":
        filtered_df = filtered_df[filtered_df[country_col].isin(target_regions)]

    if len(filtered_df) == 0:
        st.warning("No leads left after region filter. Please adjust Target Regions or Country column.")
        st.stop()

    shown_regions = ", ".join(target_regions) if target_regions else "—"
    st.write(
        f"Loaded {len(input_df)} potential leads "
        f"({len(filtered_df)} after region filter). "
        f"Target Regions: {shown_regions}."
    )

    url_col = st.selectbox("Select the column containing the Website URL:", input_df.columns)
    lead_col = st.selectbox("Select the column containing the Lead Name:", input_df.columns, index=0)

    limit = st.slider("Max Leads", 5, 500, min(50, len(filtered_df)))

    if st.button("Start Batch Audit", type="primary"):
        progress_bar = st.progress(0)
        out_rows = []

        test_df = filtered_df.head(limit).copy()

        for idx, (_, row) in enumerate(test_df.iterrows(), start=1):
            raw_url = row.get(url_col, "")
            lead_name = row.get(lead_col, "")
            url = normalize_url(str(raw_url)) if pd.notna(raw_url) else ""

            try:
                if not url or url.strip().lower() in ("nan", "none"):
                    raise ValueError

                html = fetch_html(url, timeout=8)
                ctx = extract_context_texts(html)
                res = score_lead(ctx)

                out_rows.append({
                    "Lead": lead_name,
                    "Website": raw_url,
                    "Strategic Fit": res.strategic_fit,
                    "Primary Sector": res.primary_sector,
                    "Strategic Score": res.strategic_score,
                    "Confidence": res.confidence,
                    "Priority": "",
                    "Score Percentile": 0,
                    "High Signal Count": res.high_signal_count,
                    "Why Call Next": res.why_call_next,
                    "Recommended Action": res.recommended_action,
                    "Key Signals": "; ".join(res.key_signals[:12]),
                })

            except Exception:
                out_rows.append({
                    "Lead": lead_name,
                    "Website": raw_url,
                    "Strategic Fit": "Connection Failed",
                    "Primary Sector": "—",
                    "Strategic Score": 0.0,
                    "Confidence": "—",
                    "Priority": "C",
                    "Score Percentile": 0,
                    "High Signal Count": 0,
                    "Why Call Next": "Could not fetch or parse website content.",
                    "Recommended Action": "Manual review / Fix URL",
                    "Key Signals": "",
                })

            progress_bar.progress(idx / len(test_df))
            time.sleep(0.1)

        EXPECTED_COLS = [
            "Lead", "Website", "Strategic Fit", "Primary Sector", "Strategic Score", "Confidence",
            "Priority", "Score Percentile", "High Signal Count", "Why Call Next",
            "Recommended Action", "Key Signals"
        ]

        final_df = pd.DataFrame(out_rows, columns=EXPECTED_COLS)

        if final_df.empty:
            st.warning("No rows were processed. Check filters / URLs and try again.")
            st.stop()

        # percentiles + priority
        mask_ok = final_df["Strategic Score"] > 0
        if mask_ok.any():
            final_df.loc[mask_ok, "Score Percentile"] = (
                final_df.loc[mask_ok, "Strategic Score"].rank(pct=True) * 100
            ).round(0).astype(int)
        else:
            final_df["Score Percentile"] = 0

        # ensure numeric percentiles - robust against "" and strings
        final_df["Score Percentile"] = pd.to_numeric(final_df["Score Percentile"], errors="coerce").fillna(0).astype(int)

        final_df["Priority"] = final_df["Score Percentile"].apply(
            lambda p: "A" if p >= 80 else ("B" if p >= 50 else "C")
        )

        final_df = final_df.sort_values(
            by=["Priority", "Strategic Score"],
            key=lambda s: s.map({"A": 0, "B": 1, "C": 2}) if s.name == "Priority" else s,
            ascending=True
        )

        # KPI box
        total = len(final_df)
        a_count = int((final_df["Priority"] == "A").sum())
        b_count = int((final_df["Priority"] == "B").sum())
        lift = (a_count / total * 100) if total else 0.0

        c1, c2, c3 = st.columns(3)
        c1.metric("Leads processed", total)
        c2.metric("High priority (A)", f"{a_count} | B: {b_count}")
        c3.metric("A lead concentration", f"{lift:.0f}%")

        st.success("Batch Analysis Complete!")

        st.dataframe(
            final_df[
                [
                    "Lead", "Website", "Priority", "Score Percentile",
                    "Primary Sector", "Strategic Score", "Confidence",
                    "Why Call Next", "Recommended Action",
                    "High Signal Count", "Key Signals"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "Download Enriched Sales List",
            final_df.to_csv(index=False).encode("utf-8"),
            "werba_enriched_leads.csv",
            "text/csv"
        )
