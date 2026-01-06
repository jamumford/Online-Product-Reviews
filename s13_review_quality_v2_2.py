"""
Version history
v2_2 = Altered to allow the vote for the current review to be included in
    calculation of reviewer history score.
v2_1 = Modified to produce output analyis files.
v2_0 = Produces quality outputs for ML ascription results as well as for raw
    annotation outputs.
v1_1 = Filters to remove potentially duplicitous reviews
v1_0 = Implements CQ equations with prior weights from Decision Tree Analysis.
"""

import json
import math
import matplotlib.pyplot as plt
import os


def ascription_scoring(review, ascription_feature, processed, data_source):

    # Annotator (dictionary) or ML (single value) output for consumer value
    if data_source == "summary_annotations" and ascription_feature == "Predicted Rating":
        output = review[data_source]["OVERALL"]
    else:
        output = review[data_source][ascription_feature]
    
    if data_source == "summary_annotations":
        sum_weighted = 0.0
        total_count = 0
        for key, count in output.items():
            # Treat "n/a" as 0; otherwise convert key to a float, unless ascription_feature
            # is "Predicted Rating", which should not have "n/a" as input.
            if key == "n/a":
                if ascription_feature == "Predicted Rating":
                    continue
                else:
                    value = 0.0
            else:
                value = float(key)
            sum_weighted += value * count
            total_count += count
            
        # Avoid division by zero; if there are no counts, default the mean value to 0.
        ascription_score = sum_weighted / total_count if total_count > 0 else 0
    
    elif data_source == "ML Ascription":
        ascription_score = 0.0 if (output is None or math.isnan(output)) else output
        
    else:
        raise ValueError(f"Unexpected data source: {data_source}")
        
    # For product rating feature: compare ascription with reviewer's product score
    if ascription_feature == "Predicted Rating":
        product_score = review.get("overall")
        processed["Product Rating"] = 5.0 - abs(ascription_score - product_score)
    else:      
        processed[ascription_feature] = ascription_score
        
    return processed


def compute_CQ(entry, w, features, feature_set):

    # Second factor: weighted average of revenue values using weights w
    denominator = 0
    for feature in feature_set:
        denominator += w[feature]
    if denominator != 1.0:
        raise ValueError("Sum of weights should be equal to 1.0")
    
    numerator = 0
    for feature in feature_set:
        #print(f"w[feature]: {w[feature]}")
        # Second factor: weighted average of revenue values using weights w
        #print(f"features[feature]: {features[feature]}")
        numerator += w[feature] * features[feature]
        
    simple_output = numerator / denominator

    return simple_output


def compute_quality(entry, w):

    features = {
            "FUrev": entry["Feature Usage"],
            "ITrev": entry["Interaction Time"],
            "CErev": entry["Context Experience"],
            "ARrev": entry["Author Rating"],
            "IErev": entry["Image Exists"],
            "Vrev": entry["Verified"],
            "CSrev": entry["Clarity of Sentiment"],
            "PRrev": entry["Product Rating"]
    }
    
    # Compute CQ1, CQ2, and CQ3:
    cq1 = compute_CQ(entry, w, features, ["FUrev", "ITrev", "CErev"])
    cq2 = compute_CQ(entry, w, features, ["ARrev", "IErev", "Vrev"])
    cq3 = compute_CQ(entry, w, features, ["CSrev", "PRrev"])
    
    quality = min(cq1, cq2, cq3)
    return cq1, cq2, cq3, quality


def consumer_value_scoring(review, consumer_val, processed, data_source):

    # Annotator (dictionary) or ML (single value) output for consumer value
    output = review[data_source][consumer_val]

    if data_source == "summary_annotations":
        # Find the key with the highest count.
        best_key = max(output, key=lambda k: output[k])
        processed[consumer_val] = 0.0 if best_key == "n/a" else 5.0
            
    elif data_source == "ML Ascription":
        processed[consumer_val] = 0.0 if (output is None or math.isnan(output)) else 5.0
    
    else:
        raise ValueError(f"Unexpected data source: {data_source}")
    
    return processed


def plot_cq_distributions(all_cq1, all_cq2, all_cq3, all_quality, data_source, analysis_dir):
    # Output filename
    output_path = os.path.join(analysis_dir, f"cq_box_plot_{data_source}.png")

    # Flatten each dict of lists into a single list of numbers
    flat_cq1     = [value for lst in all_cq1.values()     for value in lst]
    flat_cq2     = [value for lst in all_cq2.values()     for value in lst]
    flat_cq3     = [value for lst in all_cq3.values()     for value in lst]
    flat_quality = [value for lst in all_quality.values() for value in lst]

    # --- BOX PLOT ---
    plt.figure(figsize=(8,5))
    plt.boxplot(
        [flat_cq1, flat_cq2, flat_cq3, flat_quality],
        labels=["CQ1", "CQ2", "CQ3", "Quality"],
        showfliers=True,
        notch=True
    )
    #plt.title("Distributions of CQ1, CQ2, CQ3 and Overall Quality")
    plt.ylabel("Score")
    plt.tight_layout()
    
    # Save to file
    plt.savefig(output_path, dpi=300)
    plt.close()


def process_review(review, consumer_values, ascriptions, non_ascriptions, data_source):
    """
    Given one review object, process both the annotation fields and non-annotation fields.
    """
    processed = {}
    processed["Review ID"] = f'{review["reviewerID"]}_{review["unixReviewTime"]}'
    
    # Only process reviews with at least two annotators' evaluation and have no flags for deception
    num_annotators  = sum(review["summary_annotations"]["Clarity of Sentiment"].values())
    deception_flags = ["Bot", "Desc. not Aligned", "Disingenuous"]
    count_deception = sum(review["summary_annotations"]["Review Flagged"][label] for label in deception_flags)
    if data_source not in review or num_annotators < 1 or count_deception != 0:
        return None
        
    # For consumer values determine if majority is n/a or other to return a binary output.
    for consumer_val in consumer_values:
        processed = consumer_value_scoring(review, consumer_val, processed, data_source)

    # Process ascriptions: for each annotation, find the key in summary_annotations with the highest count.
    for ascription_feature in ascriptions:
        processed = ascription_scoring(review, ascription_feature, processed, data_source)

    # For "verified", simply return the Boolean.
    if "verified" in non_ascriptions:
        if review.get("verified")  == True:
            processed["Verified"] = 5
        else:
            processed["Verified"] = 0

    # For "image", check if the "image" key exists and is non-empty.
    # (If your data uses a different key such as "imageURL", adjust here accordingly.)
    if "image" in non_ascriptions:
        if bool(review.get("image")):
            processed["Image Exists"] = 5
        else:
            processed["Image Exists"] = 0
    
    # For "reviewer_history", we sum the values (after converting to int),
    # then divide by the total count.
    if "reviewer_history" in non_ascriptions:
        history = review.get("reviewer_history", [])
        if history and len(history) >= 1:
            try:
                values = [int(x) for x in history]
            except ValueError:
                # Handle the case where conversion to integer might fail.
                values = [0 for _ in history]
            numerator = sum(values)
            denominator = len(values)
            average = numerator / denominator if denominator != 0 else 0
            processed["Author Rating"] = (min(average, 5) + min(denominator, 5)) / 2
        else:
            processed["Author Rating"] = 0
            
    return processed


def return_key_info(product_category, entry, cq1, cq2, cq3, quality):
    quality_return = {}
    quality_return["Product Category"] = product_category
    quality_return["Review ID"] = entry["Review ID"]
    quality_return["CQ1"] = cq1
    quality_return["CQ2"] = cq2
    quality_return["CQ3"] = cq3
    quality_return["CQ Sum"] = cq1 + cq2 + cq3
    quality_return["Review Quality"] = quality   
    return quality_return


def write_outputs(quality_return, min_max_type):
    print(f'\nProduct Category: {quality_return["Product Category"]}')
    print(f'{min_max_type} Quality Review ID: {quality_return["Review ID"]}')
    print(f'CQ1: {quality_return["CQ1"]}')
    print(f'CQ2: {quality_return["CQ2"]}')
    print(f'CQ3: {quality_return["CQ3"]}')
    print(f'CQ Sum: {quality_return["CQ Sum"]}')
    print(f'Review Quality: {quality_return["Review Quality"]}', '\n')


def main(data_dir, consumer_values, ascriptions, non_ascriptions, w, data_source, analysis_dir, save_outputs): 

    review_scores = {}
    max_quality = 0
    max_cq_sum = 0
    min_quality = 999999
    min_cq_sum = 999999
    all_cq1 = {}
    all_cq2 = {}
    all_cq3 = {}
    all_quality = {}
    
    
    for file_name in os.listdir(data_dir):
        print(f"Processing {file_name}")
        file_path = os.path.join(data_dir, file_name)
        with open(os.path.join(data_dir, file_name), 'r') as f:
            review_data = json.load(f)
        
        product_category = file_name[:-14]
        
        all_cq1[product_category] = []
        all_cq2[product_category] = []
        all_cq3[product_category] = []
        all_quality[product_category] = []
        
        # Process each review in the dataset.
        for review in review_data:
            entry = process_review(review, consumer_values, ascriptions, non_ascriptions, data_source)
            if entry is None:
                continue       
            
            cq1, cq2, cq3, quality = compute_quality(entry, w)
            cq_sum = cq1 + cq2 + cq3
            
            # Append to the summary dictionaries
            all_cq1[product_category].append(cq1)
            all_cq2[product_category].append(cq2)
            all_cq3[product_category].append(cq3)
            all_quality[product_category].append(quality)
            
            # Attach the computed values under the data_source key in the original review dict:
            review[data_source]["cq1"] = cq1
            review[data_source]["cq2"] = cq2
            review[data_source]["cq3"] = cq3
            review[data_source]["quality"] = quality
    
            if quality >= max_quality and cq_sum > max_cq_sum:
                max_quality_return = return_key_info(product_category, entry, cq1, cq2, cq3, quality)
                max_quality = quality
                max_cq_sum = cq_sum
                
            if quality <= min_quality and cq_sum < min_cq_sum:
                min_quality_return = return_key_info(product_category, entry, cq1, cq2, cq3, quality)
                min_quality = quality
                min_cq_sum = cq_sum

        # After processing all reviews in this file, overwrite it with the new data
        if save_outputs:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(review_data, f, indent=4, ensure_ascii=False)
    
    if save_outputs:
        plot_cq_distributions(all_cq1, all_cq2, all_cq3, all_quality, data_source, analysis_dir)
    write_outputs(min_quality_return, "Minimum")
    write_outputs(max_quality_return, "Maximum")       
    
    return


if __name__ == "__main__":
    # Load and process the JSON data from data directory, and set output analysis directory
    data_dir     = 'ML_datasets'
    analysis_dir = "Analysis"
    save_outputs = True
      
    consumer_values = [
              "Efficiency",
              "Excellence",
              "Status",
              "Esteem",
              "Play",
              "Aesthetics",
              "Ethics",
              "Spirituality"
              ]   
              
    ascriptions = [              
              "Feature Usage",
              "Interaction Time",
              "Context Experience",
              "Clarity of Sentiment",
              "Predicted Rating"
              ]
    
    non_ascriptions = [
              "reviewer_history",
              "verified",
              "image"
              ]
    
    w = {"FUrev": 0.023912, "ITrev": 0.126529, "CErev": 0.849559, "ARrev": 0.761987, "IErev": 0.023478, "Vrev": 0.214535, "CSrev": 0.195492, "PRrev": 0.804508} 
    
    main(data_dir, consumer_values, ascriptions, non_ascriptions, w, "summary_annotations", analysis_dir, save_outputs)
    main(data_dir, consumer_values, ascriptions, non_ascriptions, w, "ML Ascription", analysis_dir, save_outputs)
