"""
Version history
v1_0 = Adds ML CQ features ascription outputs to ML datasets.
"""

import os
import json
import pandas as pd


# Helper to add unique_id to each JSON object
def add_unique_id_to_data(data):
    """
    Given a list of dicts, concatenates reviewerID + asin + unixReviewTime
    (all cast to str) into a new 'unique_id' field on each object.
    """
    for obj in data:
        reviewer = str(obj.get('reviewerID', ''))
        unixtime = str(obj.get('unixReviewTime', ''))
        obj['unique_id'] = f"{reviewer}_{unixtime}"


def main(datasets_dir, df, ml_keys):
    for category, group in df.groupby('category'):
        aligned_category = category.replace(" ", "_")
        json_file = os.path.join(datasets_dir, f"{aligned_category}_extended.json")
        if not os.path.isfile(json_file):
            print(f"File not found: {json_file}")
            continue
               
        # Load JSON array
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Inject unique_id into every object
        add_unique_id_to_data(data)
               
        # Build a map from unique_id to object
        lookup = { item.get('unique_id'): item for item in data }
               
        # Iterate rows in this category
        for _, row in group.iterrows():
            uid = f"{row['reviewerID']}_{row['unixReviewTime']}"
            obj = lookup.get(uid)
            if obj is None:
                print(f"unique_id {uid} not found in {json_file}")
                continue
               
            # Build the nested ML Ascription dict from the row
            ml_block = { key: row.get(key) for key in ml_keys }
            # Insert or update under "ML Ascription"
            obj.setdefault('ML Ascription', {}).update(ml_block)
               
        # Write back the updated JSON
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
               
    print("Done updating all JSON files.")


if __name__ == "__main__":

    # Datasets directories
    ml_output_dir = 'ML_ascription_outputs'
    datasets_dir = 'ML_datasets'
    
    # Load the Excel file
    csv_path = os.path.join(ml_output_dir, 'ML_Predictions_Feature_Scores_Full_Set.csv')
    df = pd.read_csv(csv_path)
    
    # Define the ML Ascription fields you want to copy
    ml_keys = [
        "Feature Usage", "Interaction Time", "Context Experience", "Clarity of Sentiment",
        "Predicted Rating", "Efficiency", "Excellence", "Status", "Esteem", "Play", 
        "Aesthetics", "Ethics", "Spirituality"
    ]
    
    # For each category, open its JSON once, update all rows, then save
    main(datasets_dir, df, ml_keys)
