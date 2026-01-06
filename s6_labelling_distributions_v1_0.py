"""
Created on Wed July 05 00:29:20 2023

@author: Truffles

This script processes the annotator outputs and plots the related distributions
across the product categories.

Change log:
v1_0 = Functional code.
"""

import json
import os


def main():
    # Load and process the JSON data
    analysis_dir = 'Summary_Annotations'
    init_vals = {"1":0, "2":0, "3":0, "4":0, "5":0, "n/a":0}
    subjects = {
              "Feature Usage": init_vals.copy(),
              "Interaction Time": init_vals.copy(),
              "Context Experience": init_vals.copy(),
              "Efficiency": init_vals.copy(),
              "Excellence": init_vals.copy(),
              "Status": init_vals.copy(),
              "Esteem": init_vals.copy(),
              "Play": init_vals.copy(),
              "Aesthetics": init_vals.copy(),
              "Ethics": init_vals.copy(),
              "Spirituality": init_vals.copy(),
              "OVERALL": init_vals.copy(),
              "Clarity of Sentiment": init_vals.copy()
              }
    
    for file_name in os.listdir(analysis_dir):
        with open(os.path.join(analysis_dir, file_name), 'r') as f:
            annotator_data = json.load(f)
        for review_idx, options_dict in annotator_data.items():
            for option, cat_dict in options_dict.items():
                if option not in subjects.keys():
                    raise ValueError(f"Option {option} for file {file_name}, review_idx {review_idx}, \
                          not represented in pre-defined subjects nested dictionary!")
                else:
                    for category, cat_val in cat_dict.items():
                        if category not in subjects[option].keys():
                            raise ValueError(f"Category {category} for file {file_name}, review_idx {review_idx}, \
                                  option {option} not represented in pre-defined subjects nested dictionary!")
                        else:
                            subjects[option][category] += cat_val

    for subject, category_dict in subjects.items():
        print("Subject is:", subject)
        print(category_dict, '\n')
    
    return


if __name__ == "__main__":
    main()