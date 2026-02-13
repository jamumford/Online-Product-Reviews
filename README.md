# Review Annotation + Quality Analysis Toolkit

A set of Python scripts for:

1. **Annotating Amazon reviews** via a Tkinter GUI  
2. Providing **raw annotation transparency data** (`Raw_Annotations/[A|B|C]/...`)  
3. Analysing **inter-annotator agreement** + **label distributions** from **summarised** annotations  
4. **Appending ML feature-ascription outputs** into JSON datasets  
5. Computing **review-quality scores** (CQ1/CQ2/CQ3 + overall) for both humans and ML  
6. Computing **correlations** between human vs ML quality metrics

> **Important notes**
> - The scripts use **relative paths**. Run them from the **repository root**.
> - The `Annotations/` folder is **not included** in the repository (it is created locally by the GUI).
> - For transparency, this repo includes `Raw_Annotations/[Annotator]/` where `[Annotator]` is `A`, `B`, or `C`.

---

## Repository layout

Expected folders (key ones used as inputs by these scripts):

```text
.
├── Amazon/
│   ├── Review_data/
│   │   ├── <Category>.json
│   │   └── ...
│   └── Meta_data/
│       ├── meta_<Category>.json
│       └── ...
├── Raw_Annotations/
│   ├── A/
│   │   ├── <Category>_annotated.json
│   │   └── ...
│   ├── B/
│   └── C/
├── Summary_Annotations/
│   ├── <Category>_summary.json   (name can vary; must be valid JSON)
│   └── ...
├── ML_ascription_outputs/
│   └── ML_Predictions_Feature_Scores_Full_Set.csv
├── ML_datasets/
│   ├── <Category>_extended.json
│   └── ...
├── Analysis/                     (created by you; outputs are written here)
└── s*.py                         (scripts)
```

### What each folder contains

#### `Amazon/Review_data/`
Line-delimited JSON (one JSON object per line) for each product category:

- `Amazon/Review_data/<Category>.json`

The GUI expects at minimum fields like:

- `reviewText` (string)
- `overall` (numeric rating)
- `asin` (product id)

#### `Amazon/Meta_data/`
Line-delimited JSON for product metadata:

- `Amazon/Meta_data/meta_<Category>.json`

Expected fields used by the GUI:

- `asin`
- `title`
- `description` (often a list; GUI uses the first element)

#### `Raw_Annotations/[A|B|C]/` (included for transparency)
Raw per-annotator annotation JSON files, grouped by anonymised annotator:

- `Raw_Annotations/A/<Category>_annotated.json`
- `Raw_Annotations/B/<Category>_annotated.json`
- `Raw_Annotations/C/<Category>_annotated.json`

These are the *direct outputs* of the annotation workflow for each annotator/category.

#### `Annotations/` (NOT in repo)
Local working directory created by the GUI, used to save/load ongoing annotation progress:

- `Annotations/<Category>_annotated.json`

> Add `Annotations/` to your `.gitignore` if you don’t want local files tracked.

#### `Summary_Annotations/`
Summarised/aggregated annotation data (used by the agreement & distribution scripts).  
Each JSON file is expected to look conceptually like:

```json
{
  "0": {
    "Feature Usage": {"1": 0, "2": 1, "3": 2, "4": 0, "5": 0, "n/a": 0},
    "Interaction Time": {"1": 0, "2": 0, "3": 3, "4": 0, "5": 0, "n/a": 0}
  },
  "1": { "...": "..." }
}
```

Where keys like `"0"`, `"1"` are review indices, and each option contains a dictionary of label-counts (typically aggregated across 3 annotators).

#### `ML_ascription_outputs/`
A CSV of model outputs:

- `ML_ascription_outputs/ML_Predictions_Feature_Scores_Full_Set.csv`

Must include columns:

- `category`, `reviewerID`, `unixReviewTime`
- and the ML fields you want to append (see script section below)

#### `ML_datasets/`
JSON arrays (one file per category), e.g.:

- `ML_datasets/<Category>_extended.json`

These are modified **in place** by the ML-append and quality scripts.

#### `Analysis/`
Create this folder before running scripts that output plots/CSVs:

- `Analysis/cq_box_plot_<source>.png`
- `Analysis/quality_correlations.csv`

---

## Installation

Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate  # (Windows: .venv\Scripts\activate)
pip install -U pip
pip install numpy pandas matplotlib scipy scikit-learn statsmodels
```

Notes:
- `tkinter` is part of the Python standard library on many systems, but may need OS-level installation on some Linux distros.

---

## Scripts and how to run them

### 1) GUI annotation tool — `s2_gui_v1_9.py`

Launches a Tkinter GUI to annotate reviews.

**Inputs**
- `Amazon/Review_data/<Category>.json`
- `Amazon/Meta_data/meta_<Category>.json`

**Outputs (local)**
- `Annotations/<Category>_annotated.json` (auto-created folder + file)

Run:
```bash
python s2_gui_v1_9.py
```

How it works (high level):
- Category list is derived from filenames in `Amazon/Review_data/`.
- When you select a category, the script loads the category review file and matching meta file.
- It writes progress to `Annotations/<Category>_annotated.json`, and also reads it back to restore previously saved selections.

---

### 2) Inter-annotator agreement — `s5_annotator_agreement_v2_2.py`

Computes:
- Step 1: **Binary agreement** (n/a vs ordinal) via Fleiss’ kappa (+ observed/expected agreement)
- Step 2: **Ordinal agreement** via Fleiss’ kappa (ordinal-only rows) and mean **quadratic weighted kappa** (pairwise)

**Inputs**
- All JSON files in `Summary_Annotations/`

Run:
```bash
python s5_annotator_agreement_v2_2.py
```

Output:
- Printed statistics to stdout.

---

### 3) Label distributions — `s6_labelling_distributions_v1_0.py`

Aggregates label counts across all files in `Summary_Annotations/` and prints totals per subject/option.

**Inputs**
- All JSON files in `Summary_Annotations/`

Run:
```bash
python s6_labelling_distributions_v1_0.py
```

Output:
- Printed distributions to stdout.

---

### 4) Append ML ascription outputs into datasets — `s12_append_ml_ascription_v1_0.py`

Adds an `"ML Ascription"` block into each review JSON object in `ML_datasets/<Category>_extended.json`, matching rows by:

- `reviewerID` + `unixReviewTime`

**Inputs**
- `ML_ascription_outputs/ML_Predictions_Feature_Scores_Full_Set.csv`
- `ML_datasets/<Category>_extended.json` (one per category)

**Outputs**
- Overwrites each `ML_datasets/<Category>_extended.json` **in place**, adding/updating:
  - `unique_id`
  - `ML Ascription` (dict of ML fields)

Run:
```bash
python s12_append_ml_ascription_v1_0.py
```

Fields appended by default (see `ml_keys` in the script):
- `Feature Usage`, `Interaction Time`, `Context Experience`, `Clarity of Sentiment`
- `Predicted Rating`
- `Efficiency`, `Excellence`, `Status`, `Esteem`, `Play`, `Aesthetics`, `Ethics`, `Spirituality`

---

### 5) Compute review quality (CQ1/CQ2/CQ3 + overall) — `s13_review_quality_v2_2.py`

Computes CQ scores and overall review quality for:
- `summary_annotations` (human aggregated)
- `ML Ascription` (model outputs)

**Inputs**
- All JSON files in `ML_datasets/` (each must be a JSON **list**)
- Each review object should contain:
  - `reviewerID`, `unixReviewTime`
  - `overall` (rating)
  - `verified` (bool) and optionally `image`
  - `reviewer_history` (list) if you want author-rating scoring
  - `summary_annotations` dict (for human run)
  - `ML Ascription` dict (for ML run; typically added via `s12`)

**Outputs**
- Optionally overwrites `ML_datasets/*.json` in place by adding:
  - `cq1`, `cq2`, `cq3`, `quality` under each data source block
- Saves boxplots to:
  - `Analysis/cq_box_plot_summary_annotations.png`
  - `Analysis/cq_box_plot_ML Ascription.png`

Before running, create `Analysis/`:

```bash
mkdir -p Analysis
python s13_review_quality_v2_2.py
```

Filtering behaviour (important):
- Reviews flagged with deception labels (`Bot`, `Desc. not Aligned`, `Disingenuous`) in `summary_annotations["Review Flagged"]` are skipped.
- Reviews with insufficient annotation coverage are skipped.

---

### 6) Correlate human vs ML quality metrics — `s15_quality_correlation_stats_v1_1.py`

Computes Pearson and Spearman correlations between:
- `summary_annotations` vs `ML Ascription`
for variables:
- `cq1`, `cq2`, `cq3`, `quality`

**Inputs**
- `ML_datasets/*.json` with both sources present and numeric fields already computed
  - (typically produced by running `s13_review_quality_v2_2.py` first)

**Outputs**
- Prints correlation table to stdout
- Writes CSV:
  - `Analysis/quality_correlations.csv`

Run:
```bash
mkdir -p Analysis
python s15_quality_correlation_stats_v1_1.py
```

---

## Typical workflow

1. (Optional) Use the GUI to annotate locally:
   ```bash
   python s2_gui_v1_9.py
   ```
   This creates `Annotations/` locally.

2. Use the included transparency data:
   - Inspect `Raw_Annotations/A|B|C/` as the raw per-annotator files.

3. Ensure you have `Summary_Annotations/` available (pre-generated or generated by your own summarisation step).

4. Agreement + distributions:
   ```bash
   python s5_annotator_agreement_v2_2.py
   python s6_labelling_distributions_v1_0.py
   ```

5. Append ML outputs to datasets:
   ```bash
   python s12_append_ml_ascription_v1_0.py
   ```

6. Compute CQ/quality metrics + outputs:
   ```bash
   mkdir -p Analysis
   python s13_review_quality_v2_2.py
   ```

7. Correlate human vs ML:
   ```bash
   mkdir -p Analysis
   python s15_quality_correlation_stats_v1_1.py
   ```

---

## License

This repository is released under the **Creative Commons Zero v1.0 Universal (CC0 1.0)** public-domain dedication (often referred to as “CC0 1.0 Universal”).  
You may copy, modify, distribute, and perform the work, even for commercial purposes, all without asking permission.

- Human-readable summary (deed): https://creativecommons.org/publicdomain/zero/1.0/
- Full legal code: https://creativecommons.org/publicdomain/zero/1.0/legalcode

> CC0 includes a warranty disclaimer and limitation of liability. See the legal code for details.
