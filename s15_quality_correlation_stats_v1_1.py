"""
Version history
v1_1 = Add statistical significance tests.
v1_0 = Produces Pearson and Spearman correlation stats for review quality and CQs, 
      comparing annotator vs ML. 
"""

import csv
import json
import numpy as np
import os
from scipy.stats import pearsonr, spearmanr


def compute_correlations(pairs_dict):
    """
    Given a dict mapping variable names to (list1, list2),
    compute Pearson’s r and its two‐tailed p‐value. Returns a dict:
      var_name -> (n_pairs, r_value, p_value).
    If fewer than 2 observations exist, returns (n_pairs, None, None).
    """
    results = {}
    for var, (vals1, vals2) in pairs_dict.items():
        n = len(vals1)
        if n < 2:
            results[var] = (n, None, None)
            continue

        arr1 = np.array(vals1, dtype=float)
        arr2 = np.array(vals2, dtype=float)
        # pearsonr returns (r_value, p_value)
        r_val, p_val = pearsonr(arr1, arr2)
        results[var] = (n, r_val, p_val)
    return results


def compute_spearman(pairs_dict):
    """
    Given a dict mapping variable names to (list1, list2),
    compute Spearman’s rho and its two‐tailed p‐value. Returns a dict:
      var_name -> (n_pairs, rho_value, p_value).
    If fewer than 2 observations exist, returns (n_pairs, None, None).
    """
    results = {}
    for var, (vals1, vals2) in pairs_dict.items():
        n = len(vals1)
        if n < 2:
            results[var] = (n, None, None)
            continue

        rho_val, p_val = spearmanr(vals1, vals2)
        results[var] = (n, rho_val, p_val)
    return results


def gather_pairs(data_dir, source1, source2):
    """
    Traverse all JSON files in data_dir. For each review in each file, if both
    source1 and source2 appear as keys, extract the four numeric variables and
    collect paired lists. Returns a dict mapping variable names to a tuple of 
    two lists: (values_from_source1, values_from_source2).
    """
    var_names = ["cq1", "cq2", "cq3", "quality"]
    # Initialise empty lists for each variable
    pairs = {
        var: ([], [])  # pairs[var][0] will collect from source1; pairs[var][1] from source2
        for var in var_names
    }

    for fname in os.listdir(data_dir):
        if not fname.lower().endswith(".json"):
            continue

        full_path = os.path.join(data_dir, fname)
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                reviews = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Skipping file '{fname}' (could not read/parse): {e}")
            continue

        if not isinstance(reviews, list):
            print(f"Warning: Expected a list of review dicts in '{fname}', got {type(reviews)}. Skipping.")
            continue

        for review in reviews:
            if not isinstance(review, dict):
                continue

            # Check that both data sources exist in this review
            if source1 not in review or source2 not in review:
                continue

            sub1 = review[source1]
            sub2 = review[source2]
            if not isinstance(sub1, dict) or not isinstance(sub2, dict):
                continue

            # Attempt to extract each variable
            missing_field = False
            for var in var_names:
                if var not in sub1 or var not in sub2:
                    missing_field = True
                    break
                if not isinstance(sub1[var], (int, float)) or not isinstance(sub2[var], (int, float)):
                    missing_field = True
                    break
            if missing_field:
                # Skip if any variable is missing or not numeric
                continue

            # Append to the respective lists
            for var in var_names:
                pairs[var][0].append(sub1[var])
                pairs[var][1].append(sub2[var])

    return pairs


def print_comparison(pearson_res, spearman_res, source1, source2):
    """
    Nicely prints a side‐by‐side table of:
      variable | N_pairs | Pearson r (p‐value) | Spearman rho (p‐value)
    """
    header = (
        f"\nComparison of '{source1}' vs '{source2}':\n\n"
        f"{'Variable':<10}  {'N':>5}  {'Pearson r':>10}   {'p-pearson':>10}   "
        f"{'Spearman ρ':>10}   {'p-spearman':>10}"
    )
    print(header)
    print("-" * len(header))

    for var in pearson_res:
        n_p, r_val, p_r = pearson_res[var]
        n_s, rho_val, p_rho = spearman_res[var]
        # In normal usage, n_p == n_s. If not, show both as n_p/n_s.
        n_display = n_p if n_p == n_s else f"{n_p}/{n_s}"

        if r_val is None:
            r_str = "N/A"
            p_str = "N/A"
        else:
            r_str = f"{r_val:>10.4f}"
            p_str = f"{p_r:>10.4e}"

        if rho_val is None:
            rho_str = "N/A"
            p_rho_str = "N/A"
        else:
            rho_str = f"{rho_val:>10.4f}"
            p_rho_str = f"{p_rho:>10.4e}"

        print(f"{var:<10}  {n_display:>5}  {r_str}   {p_str}   {rho_str}   {p_rho_str}")
    print()


def save_to_csv(pearson_res, spearman_res, source1, source2, analysis_dir):
    """
    Save results to a CSV file with columns:
      variable, n_pairs, pearson_r, p_pearson, spearman_rho, p_spearman, source1, source2
    """
    output_path = os.path.join(analysis_dir, "quality_correlations.csv")
    fieldnames = [
        "variable",
        "n_pairs",
        "pearson_r",
        "p_pearson",
        "spearman_rho",
        "p_spearman",
        "source1",
        "source2"
    ]
    try:
        with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for var in pearson_res:
                n_p, r_val, p_r = pearson_res[var]
                n_s, rho_val, p_rho = spearman_res[var]
                # If n_p != n_s, choose the smaller one for CSV (or store both as “n_p/n_s”).
                n_pairs = n_p if n_p == n_s else f"{n_p}/{n_s}"

                writer.writerow({
                    "variable": var,
                    "n_pairs": n_pairs,
                    "pearson_r": "" if r_val is None else f"{r_val:.6f}",
                    "p_pearson": "" if p_r is None else f"{p_r:.4e}",
                    "spearman_rho": "" if rho_val is None else f"{rho_val:.6f}",
                    "p_spearman": "" if p_rho is None else f"{p_rho:.4e}",
                    "source1": source1,
                    "source2": source2
                })
        print(f"Results saved to CSV at: {output_path}")
    except IOError as e:
        print(f"Error: Unable to write CSV file at '{output_path}': {e}")


def main():
    data_dir = "ML_datasets"
    analysis_dir = "Analysis"
    source1 = "summary_annotations"
    source2 = "ML Ascription"
    
    # Step 1: gather all paired values across your JSON files
    pairs = gather_pairs(data_dir, source1, source2)

    # Step 2: compute Pearson correlations
    pearson_results = compute_correlations(pairs)

    # Step 3: compute Spearman's rho correlations
    spearman_results = compute_spearman(pairs)

    # Step 4: print side‐by‐side
    print_comparison(pearson_results, spearman_results, source1, source2)

    # Step 5: save both results to one CSV
    save_to_csv(pearson_results, spearman_results, source1, source2, analysis_dir)


if __name__ == "__main__":
    main()
