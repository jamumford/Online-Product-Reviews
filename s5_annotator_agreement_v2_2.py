"""
Created on Wed July 05 00:29:20 2023

@author: Truffles

This script processes the json files containing the amazon reviews and
produces a gui for users to annotate.

Change log:
v2_2 = Adjusted proportion of annotations to reflect categories and not counts.
v2_1 = Added additional summary statistics such as actual vs expected agreement.
v2_0 = Adapted to two stage agreement: first for n/a vs ordinal agreement; then weighted
    agreement across ordinal values.
v1_1 = Added in reporting of highest and lowest kappas.
v1_0 = Functional code.
"""

import json
import os
import numpy as np
from statsmodels.stats.inter_rater import fleiss_kappa
from sklearn.metrics import cohen_kappa_score
from itertools import combinations


def fleiss_kappa_components(matrix):
    """
    Computes Fleiss' kappa along with the observed and expected agreement.
    
    Parameters:
        matrix (np.ndarray): A 2D array where each row corresponds to an item 
                             and each column corresponds to a category. 
                             The entries are the number of raters 
                             assigning that category to the item.
    
    Returns:
        kappa (float): The Fleiss' kappa statistic.
        observed_agreement (float): The average observed agreement across items.
        expected_agreement (float): The expected agreement by chance.
    """
    n_items, n_categories = matrix.shape
    # Assume that every item is rated by the same number of raters:
    n_raters = np.sum(matrix[0])
    
    # Calculate the proportion of all assignments for each category.
    p = np.sum(matrix, axis=0) / (n_items * n_raters)
    
    # Compute observed agreement for each item:
    # For each row, sum over categories: (n_ij^2 - n_raters)
    P_i = (np.sum(matrix**2, axis=1) - n_raters) / (n_raters * (n_raters - 1))
    
    # Average observed agreement across items.
    observed_agreement = np.mean(P_i)
    
    # Expected agreement is the sum of squared category proportions.
    expected_agreement = np.sum(p**2)
    
    # Compute Fleiss' kappa.
    kappa = (observed_agreement - expected_agreement) / (1 - expected_agreement)
    
    return kappa, observed_agreement, expected_agreement


def load_annotations(directory):
    annotations = {}
    for file_name in os.listdir(directory):
        with open(os.path.join(directory, file_name), 'r') as f:
            annotations[file_name] = json.load(f)
    return annotations


def prepare_binary_matrix(annotator_data):
    binary_matrix = []
    total_annotations = 0
    for review_idx, options_dict in annotator_data.items():
        for subject, cat_dict in options_dict.items():
            if subject not in ["OVERALL", "Clarity of Sentiment"]:
                count_na = cat_dict.get("n/a", 0)
                count_ordinal = sum(cat_dict[label] for label in ['1','2','3','4','5'])
                total_annotations += 1
                if (count_na + count_ordinal) == 3: # Ensure exactly three annotations per row
                    binary_matrix.append([count_na, count_ordinal])
    return np.array(binary_matrix), total_annotations


def prepare_ordinal_matrix(annotator_data):
    ordinal_matrix = []
    total_annotations = 0
    for review_idx, options_dict in annotator_data.items():
        for subject, cat_dict in options_dict.items():
            if subject != "OVERALL":
                count_na = cat_dict.get("n/a", 0)
                count_ordinal = sum(cat_dict[label] for label in ['1','2','3','4','5'])
                if count_ordinal > 0 and count_na == 0:
                    total_annotations += 1
                if count_ordinal == 3: # Ensure exactly three annotations per row
                    ordinal_matrix.append([cat_dict[label] for label in ['1','2','3','4','5']])
    return np.array(ordinal_matrix), total_annotations


def calculate_weighted_kappa(ordinal_matrices):
    expanded_annotations = []
    for counts in ordinal_matrices:
        labels = []
        for idx, count in enumerate(counts):
            labels.extend([idx + 1] * count)
        if len(labels) == 3:
            expanded_annotations.append(labels)

    pairwise_kappas = []
    for annotator_a, annotator_b in combinations(range(3), 2):
        labels_a = [annotation[annotator_a] for annotation in expanded_annotations]
        labels_b = [annotation[annotator_b] for annotation in expanded_annotations]
        pairwise_kappas.append(cohen_kappa_score(labels_a, labels_b, weights='quadratic'))

    return np.mean(pairwise_kappas)


def main():
    analysis_dir = 'Summary_Annotations'
    annotations = load_annotations(analysis_dir)

    binary_matrices = []
    ordinal_matrices = []
    total_binary_annotations = 0
    total_ordinal_annotations = 0

    for file_name, annotator_data in annotations.items():
        binary_matrix, binary_annotations = prepare_binary_matrix(annotator_data)
        ordinal_matrix, ordinal_annotations = prepare_ordinal_matrix(annotator_data)

        total_binary_annotations += binary_annotations
        total_ordinal_annotations += ordinal_annotations

        if binary_matrix.size > 0:
            binary_matrices.append(binary_matrix)
        if len(ordinal_matrix) > 0:
            ordinal_matrices.extend(ordinal_matrix)

    print("Step 1: Binary Agreement (n/a vs Ordinal)")
    if binary_matrices:
        binary_full_matrix = np.vstack(binary_matrices)
        #filtered_binary_annotations = np.sum(binary_full_matrix)
        num_rows, num_columns = binary_full_matrix.shape
        proportion_binary = num_rows / total_binary_annotations
        binary_fleiss_kappa, actual_agreement, expected_agreement = fleiss_kappa_components(binary_full_matrix)
        print(f"Total Binary Annotations: {total_binary_annotations}")
        print(f"Filtered Binary Annotations: {num_rows}")
        print(f"Proportion Included: {proportion_binary:.4f}")
        print(f"Fleiss' Kappa (binary): {binary_fleiss_kappa:.4f}")
        print(f"Observed Agreement: {actual_agreement:.4f}")
        print(f"Expected Agreement: {expected_agreement:.4f}\n")
    else:
        print("No valid data for binary Fleiss' Kappa calculation.\n")

    print("Step 2: Ordinal Agreement (Quadratic Weighted Kappa)")
    if ordinal_matrices:
        #filtered_ordinal_annotations = np.sum(ordinal_matrices)
        ordinal_full_matrix = np.vstack(ordinal_matrices)
        num_rows, num_columns = ordinal_full_matrix.shape
        proportion_ordinal = num_rows / total_ordinal_annotations
        ordinal_fleiss_kappa, actual_agreement, expected_agreement = fleiss_kappa_components(ordinal_full_matrix)
        weighted_kappa_score = calculate_weighted_kappa(ordinal_matrices)
        print(f"Total Ordinal Annotations: {total_ordinal_annotations}")
        print(f"Filtered Ordinal Annotations: {num_rows}")
        print(f"Proportion Included: {proportion_ordinal:.4f}")
        print(f"Fleiss' Kappa (ordinal): {ordinal_fleiss_kappa:.4f}")
        print(f"Observed Agreement: {actual_agreement:.4f}")
        print(f"Expected Agreement: {expected_agreement:.4f}")
        print(f"Weighted Kappa: {weighted_kappa_score:.4f}\n")
    else:
        print("No valid ordinal annotations found for weighted kappa calculation.\n")


if __name__ == "__main__":
    main()