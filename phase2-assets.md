# Phase 2: Assets (2026-10-25)

## 1. GitHub audit (github.com/Jawad123453)

**What a client sees today:** 83 public repos. About 70 are 2023 tutorial exercises (Vue to-do lists, calculators, "for-fun" projects), and the bio says "Front End Developer". There's no Python and nothing biomedical, so the profile contradicts the niche you're now selling. That mismatch probably cost you replies before.

### Your 3 best existing projects and how to fix them
| Project | Why it's worth keeping | Fix needed |
|---|---|---|
| **dental_site** (Nuxt 3 + Tailwind, clinic site with WhatsApp booking, i18n) | Healthcare-adjacent, real production stack, and the best proof for backup niche C (clinics) | ⚠️ **Fix first.** It names a doctor in Beirut ("Dr. Ahmad Khalil, 15 years, 2,000 patients, 4.9★ from 120+ reviews") and shows patient testimonials. If those aren't real, it reads as fabricated reviews. Add a top banner and README line saying *"Concept site: fictional clinic, placeholder reviews"*, or swap in obviously fictional data. Add a live demo link and 2 screenshots. |
| **Customer-Data** / **Cars-Sales-Dashboard** (SQL cleaning + Power BI) | Shows the full workflow: raw CSV → SQL cleaning → dashboard | Add a README to each: question asked, cleaning steps, 1 screenshot of the dashboard, 3 findings. `.pbix` files can't be previewed on GitHub, so screenshots are essential. |
| **Sales-DASHBOARD** (multi-country SQL + Power BI) | Same as above | Same README treatment. Otherwise, merge the 5 data repos into one `data-analysis-portfolio` repo with a clean index. |

### Profile cleanup (about 30 minutes)
1. **Pin 4 repos:** the two new biosignal proof pieces (once they're in their own repos), dental_site, and the data portfolio.
2. **Bio:** "Biomedical engineer · ECG/HRV & biosignal analysis in Python · data dashboards".
3. **Archive or make private** the ~60 tutorial repos (calculators, to-do lists, "for-fun" projects). They dilute the signal. *Your call. Nothing has been touched.*
4. **Update the blog link** from the old Netlify portfolio to the new `/portfolio` site once it's deployed.

## 2. Positioning statement
> **Biomedical engineer who turns raw ECG and physiological recordings into clean, validated analysis, figures and dashboards, in Python, reproducibly.**

## 3. Profile bio

**Upwork title:** `Biomedical Engineer | ECG, HRV & Biosignal Data Analysis (Python)`

**Upwork / LinkedIn "About"** (edit the [brackets]):
> Got a folder of raw ECG, PPG or wearable recordings and need clean, trustworthy numbers out of it?
>
> I'm a biomedical engineer ([University], [year]) who builds Python pipelines for physiological data: R-peak detection, RR intervals, HRV (time and frequency domain), signal quality checks, group statistics and publication-ready figures.
>
> **How I work**
> • I validate before I report. My sample R-peak pipeline is benchmarked against cardiologist annotations on all 48 MIT-BIH records.
> • Every record gets a quality score, and bad segments are flagged, not silently averaged in.
> • You get reproducible code, CSV outputs and a short methods paragraph you can drop into a paper or report.
>
> **Typical projects:** batch ECG → HRV for a study, cleaning wearable data, re-analysing a thesis dataset, figures for a manuscript, a simple dashboard to explore results.
>
> Tools: Python (NeuroKit2, wfdb, SciPy, pandas, matplotlib), Excel, SQL/Power BI, React/Next.js for dashboards.
>
> Sample projects on public PhysioNet data: [portfolio link]
>
> Send me 1–2 sample files and your question. I'll reply within 24 hours with a fixed quote.

*Why this version: it opens with the client's problem, names concrete deliverables, and replaces "years of experience" (which you don't have yet) with verifiable proof. It claims nothing you haven't done. I'll revise it once you send your old profile.*

## 4. Productized offers (niche A)

### Offer 1 (Starter): **ECG → HRV Quick Pipeline**: $150, delivered in 3 days
**For:** a researcher or student with a small batch of ECG recordings.
**Scope:**
- Up to **20 ECG recordings** (EDF, WFDB, CSV or TXT; one sampling rate)
- R-peak detection + artifact correction, with a signal-quality score per recording
- RR-interval CSV per recording + one HRV table (MeanNN, SDNN, RMSSD, pNN50, LF, HF, LF/HF)
- 3 figures (example trace with peaks, tachogram, HRV summary) as PNG and SVG
- Python script + a 1-paragraph methods description
- 1 revision round
**Not included:** custom statistics, more than 20 files, multi-lead or arrhythmia classification (→ Offer 2).
*The price is deliberately low to win the first 2–3 reviews. Raise it to $250 after 3 five-star reviews.*

### Offer 2 (Core): **Biosignal Study Analysis Package**: $650, delivered in 7–10 days
**For:** labs, PhD students, and wearable or health-tech startups with a full study dataset.
**Scope:**
- Up to **200 recordings** (ECG, PPG or respiration), plus matching metadata (groups or conditions)
- Quality-control report: flagged recordings, % artifacts and ectopic beats, and what was excluded and why
- Full HRV feature set + group comparison (appropriate tests, multiple-comparison correction, effect sizes)
- 4–6 publication-ready figures matched to the target journal's style
- Reproducible repo (README, requirements, one-command rerun) + a methods and results section draft
- 30-minute video call to walk through the results, plus 2 revision rounds
**Add-ons:** interactive results dashboard (+$300), detector validation against your annotations (+$200).

**Payment terms (both offers):** 50% upfront, 50% on delivery for direct clients, via the methods you confirm work in Lebanon. On Upwork, use milestones.

## 5. Proof pieces (built in this repo, labelled as sample projects)
- `proof/01-ecg-hrv-pipeline/`: 40 Fantasia subjects, batch ECG → RR → HRV, young vs elderly comparison
- `proof/02-rpeak-validation/`: 3 R-peak detectors vs cardiologist annotations on 48 MIT-BIH records
- `portfolio/index.html`: one-page site presenting both
