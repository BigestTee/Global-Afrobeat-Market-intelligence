# Global Afrobeats Market Intelligence

## Identifying International Growth Opportunities for Emerging Afrobeats Artists

**Research question:** Which international markets offer the greatest growth opportunities for emerging Afrobeats artists?

## Project Overview

This academic capstone combines Spotify Top 200 chart visibility with a UK genre-chart reference and wider recorded-music industry context. It presents an evidence-led preliminary screen of where matched Afrobeats-chart songs appear internationally and which markets merit further audience and commercial validation.

The dashboard is a research tool, not a measure of the complete Afrobeats catalogue or total market demand. Its comparisons describe chart presence in the supplied datasets.

## Live Dashboard

**Deployment status:** Not yet deployed.

**Streamlit Community Cloud URL:** To be added after deployment.

## Dashboard Features

The dashboard has seven sections:

1. **Overview** — Full-workbook research coverage KPIs, filter-dependent Spotify chart metrics, featured matched tracks, country presence and a map. Full-sample totals are distinguished from filtered results.
2. **Global Market Performance** — Matched-song visibility across chart dates, with the GLOBAL chart reported separately from country markets.
3. **Country Comparison** — Country-level matched-song breadth, chart observations, rank and supplied stream summaries, alongside a separate GLOBAL entry.
4. **Track & Artist Performance** — Spotify Top 200 track and credited-artist rankings using the supplied chart fields and active date and market filters.
5. **Afrobeats Artists & Tracks** — The validated song–artist match catalogue, artist and track chart-presence summaries, track cards and an artwork audit. UK chart matching is a genre-chart signal, not a universal genre classification.
6. **Growth Opportunities** — The workbook’s preliminary international market shortlist, a separately presented Nigeria domestic benchmark, GLOBAL chart context and a selected-track market explorer.
7. **Data & Methodology** — Dataset coverage, matching process, metric definitions, source notes, limitations and project-file references.

## Research Data

- **Spotify Top 200 charts:** The cleaned [Spotify chart dataset](data/spotify_top200_cleaned.csv) contains track–market–date observations, including rank, supplied streams, track IDs and credited metadata. The project’s [inspection note](data/data_inspection.txt), [data dictionary](data/spotify_data_dictionary.txt) and [dataset summary](data/spotify_data_summary.txt) document its fields and preparation. The inspection note records the annual source archives as downloaded from Zenodo.
- **Official UK Afrobeats Chart:** Weekly UK chart pages from the [Official Charts Company](https://www.officialcharts.com/charts/afrobeats-chart/) were used as a chart-based reference for matching songs. The research extracted 2,900 track-week records from 145 weekly chart pages. UK chart membership is not treated as a universal Afrobeats definition.
- **IFPI industry context:** The workbook references the [IFPI Global Music Report 2025](https://www.ifpi.org/wp-content/uploads/2024/03/GMR2025_SOTI.pdf) for 2024 regional recorded-music revenue growth and the [IFPI Global Music Report 2026](https://www.ifpi.org/wp-content/uploads/2026/03/GMR2026_SOTI.pdf) for 2025 context. These figures describe the broader recorded-music industry, not Afrobeats-specific revenue or demand.

The final workbook’s `5. Sources & Method` sheet records the source references, definitions and interpretation limits.

## Key Research Coverage

| Measure | Coverage |
| --- | ---: |
| Spotify chart observations | 324,800 |
| Unique Spotify track IDs in the Spotify dataset | 31,376 |
| Spotify chart markets | 38 |
| Spotify chart dates | 146 |
| Official UK Afrobeats Chart track-week records | 2,900 |
| Matched song–market–week observations | 939 |
| Matched normalized title-and-artist combinations | 57 |
| Matched Spotify track IDs | 68 |
| Complete-coverage comparison dates | 37 |
| Markets with matched presence in the balanced comparison | 27 country markets, plus a separate GLOBAL entry |

The 939 matched observations and the 37-date comparison are workbook-based. The 27 country markets and GLOBAL are counted separately.

## Methodology and Limitations

The matching workflow compared a shortlist of 250 Spotify tracks with extracted weekly Official UK Afrobeats Chart entries using normalized track titles and credited artist names. It identified 68 Spotify IDs grouped into 57 distinct normalized title-and-artist combinations, representing 534 matched UK chart weekly entries. Multiple Spotify IDs were grouped to reduce alternate-version double counting; exact recording-version equivalence has not been independently confirmed for every group.

The Spotify panel is unbalanced: the 146 chart dates do not contain the same markets throughout. Only 37 dates have complete coverage across all 38 Spotify markets; the remaining dates have narrower coverage. The main cross-market presence comparison therefore uses those 37 complete-coverage dates. This reduces coverage imbalance for that comparison but does not make the sample complete or representative.

Interpret findings within these limits:

- Spotify chart appearances show visibility in the supplied charts. They do not equal total listening demand, unique listeners, market size, revenue, profitability or audience size.
- Chart presence alone does not establish causal growth or predict future performance.
- The UK Official Afrobeats Chart is a UK chart-based genre reference; it may reflect UK repertoire and chart rules and is not a universal or independent classification for every market.
- The matched catalogue is a shortlist-based sample, not a complete or representative catalogue of Afrobeats releases.
- Supplied stream values are summed only where available; their counting scope is not confirmed.
- IFPI regional revenue growth provides broad industry context and is not evidence of Afrobeats-specific or country-level revenue. The project does not combine these sources into an unsupported composite score.
- The 37-date balanced comparison and the first-12-versus-latest-12 snapshot comparison answer different questions. Snapshot windows should not be read as consecutive months unless independently established.

The market shortlist is preliminary and intended to guide further research and market testing, not to declare a definitive market-size or growth ranking.

## Project Structure

Key files and folders currently present in the project:

```text
.
├── app.py                                      # Active Streamlit dashboard
├── app_redesign_test.py                        # Existing temporary review copy
├── app.py.backup-20261113-200247-before-redesign-install
├── requirements.txt
├── data/
│   ├── spotify_top200_cleaned.csv
│   ├── spotify_data_dictionary.txt
│   ├── spotify_data_summary.txt
│   ├── data_inspection.txt
│   ├── afrobeats_first20_review.csv             # Earlier pilot review
│   └── afrobeats_classification_codebook.txt     # Earlier classification guidance
├── Research/
│   ├── Afrobeats_Capstone_Final_Research_Workbook.xlsx
│   └── QA/spotify_chart_cleaning_QA.xlsx
├── Report/
│   ├── Afrobeats_Global_Market_Intelligence_Final_Report.docx
│   └── Afrobeats_Global_Market_Intelligence_Final_Report.pdf
├── Presentation/
│   └── Afrobeats_Global_Market_Intelligence_Capstone_Presentation.pptx
├── src/
│   ├── build_afrobeats_candidate_pool.py
│   ├── clean_spotify_data.py
│   ├── create_afrobeats_screening_shortlist.py
│   ├── create_classification_pilot.py
│   ├── inspect_spotify_data.py
│   └── match_afrobeats_candidates.py
└── Archive/
    ├── app_backups/
    ├── duplicate_reports/
    ├── legacy_csv_exports/
    └── legacy_workbooks/
```

The dashboard’s active workbook and Spotify dataset are the files under `Research/` and `data/` shown above. The earlier first-20 review CSV and codebook are retained as pilot materials; the dashboard’s validated Afrobeats analysis uses the final research workbook.

## Installation and Running Locally

Python 3.13 is used for this project. From the project root in PowerShell, install the dependencies declared in [`requirements.txt`](requirements.txt) and start the dashboard:

```powershell
py -3.13 -m pip install -r requirements.txt
py -3.13 -m streamlit run app.py
```

Streamlit prints the local address in the terminal. The dashboard expects the cleaned Spotify CSV at `data/spotify_top200_cleaned.csv` and the final research workbook at `Research/Afrobeats_Capstone_Final_Research_Workbook.xlsx`.

## Technology Stack

- **Python 3.13** — dashboard and research utilities.
- **Streamlit** — dashboard interface, navigation, filters and session-specific display name.
- **Pandas** — dataset loading, joins and analysis.
- **Plotly** — interactive charts.
- **openpyxl** — Excel workbook access through Pandas.
- **Apple iTunes Search API** — optional track artwork lookup with designed placeholders when a confident match is unavailable.

The Python dependencies are listed in `requirements.txt`; artwork lookup uses Python’s standard-library URL tools and does not add a package dependency.

## Research Outputs

- [Final capstone report — DOCX](Report/Afrobeats_Global_Market_Intelligence_Final_Report.docx)
- [Final capstone report — PDF](Report/Afrobeats_Global_Market_Intelligence_Final_Report.pdf)
- [Capstone presentation](Presentation/Afrobeats_Global_Market_Intelligence_Capstone_Presentation.pptx)
- [Final validated research workbook](Research/Afrobeats_Capstone_Final_Research_Workbook.xlsx)

## Author / Project Context

- **Author:** Christiana Thomas Elumelu
- **Project:** Global Afrobeats Market Intelligence: Identifying International Growth Opportunities for Emerging Afrobeats Artists.
- **Programme:** GenData Data Analytics Programme
- **Project Type:** Final Capstone Project
- **Year:** 2026
