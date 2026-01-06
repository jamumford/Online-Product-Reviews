"""
Created on Wed July 05 00:29:20 2023

@author: Truffles

This script processes the json files containing the amazon reviews and
produces a gui for users to annotate.
"""

import json
import os
import tkinter as tk
from tkinter import ttk
from tkinter import *


"""
def display_review_text clears the previous review's text and uploads
the new review's text, as well as the review rating.
"""
def display_review_text(specific_box, specific_text):
    specific_box.delete(1.0, tk.END)  # Clear the text box
    specific_box.insert(tk.END, specific_text)
    return


"""
def find_asin searches for a product code 'asin' in the meta_data
in order to find the product information.
"""
def find_asin(meta_data, asin):
    for i, entry in enumerate(meta_data):
        asin_value = entry.get('asin')
        if asin_value == asin:
            return i
    print(f"Could not find product code in meta_data: {asin}") 
    return 'error'


"""
def get_categories gets a list of all of the Amazon categories
from the file names in the relevant directory.
"""
def get_categories():
    # Load review JSON data
    json_dir = 'Amazon'
    review_path = 'Review_data'
    directory = os.path.join(json_dir, review_path)
    category_list = []

    # Iterate over the files in the directory
    for file in os.listdir(directory):
        # Check if the file is a regular file
        if os.path.isfile(os.path.join(directory, file)):
            # Remove the file extension and add the file name to the list
            category = os.path.splitext(file)[0]
            category_list.append(category)
    return category_list
    

"""
def handle_category executes when the user selects a category. 
It loads the data for that category and sets the save path.
"""
def handle_category(category):
    # Establish write directory for saving review annotations
    global savepath
    save_dir = 'Annotations'
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    savepath = os.path.join(save_dir, category + '_annotated.json') 
    
    # Load review and meta data
    file_path, meta_path = load_data(category)
    
    # Create a label for the text above the product text box
    json_name = os.path.splitext(os.path.basename(file_path))[0]
    json_name = json_name.replace("_", " ")
    text_above_product_box = "Product:"
    return savepath, text_above_product_box
    

"""
def handle_rating executes when the user presses the reveal rating button. 
It reveals the rating assigned to the product by the reviewer.
"""
def handle_rating(index):
    if index >= 0 and index < len(data):
        review_rating = data[index]['overall']
        rating_text = f"Product Rating: {review_rating}"
        rating_label.configure(text=rating_text)   
    return


"""
def handle_submit executes when the user presses the submit button. It
saves the user's inputs to a json file as a dictionary entry where the
key is the review index and the values are the option values. This
facilitates easy lookup for later navigation.
"""
def handle_submit():
    selected_options = []
    for option, var in checkboxes.items():
        dropdown_value = var['dropdown'].get()
        text_value = var['text'].get()
        if dropdown_value or text_value:
            selected_options.append({
                'option': option,
                'dropdown': dropdown_value,
                'text': text_value
            })
    
    # Create a dictionary with selected options and review details
    review_index = current_review_index.get()
    review_data = data[review_index]
    review_data['selected_options'] = selected_options

    # Save the data to a JSON file
    existing_reviews = {}
    if os.path.isfile(savepath):
        with open(savepath, 'r') as file:
            existing_reviews = json.load(file) 
    existing_reviews[str(review_index)] = review_data
    with open(savepath, 'w') as file:
        json.dump(existing_reviews, file, indent=4)
    
    print(f"Selected options for Review {review_index + 1} saved to {savepath}")
    submit_label.config(text="Annotations Submitted!")
    
    return


"""
def load_data loads the review data and product meta_data for the category
"""
def load_data(category):
    # Load review JSON data
    json_dir = 'Amazon'
    review_path = 'Review_data'
    meta_path = 'Meta_data'
    
    # Sets data and meta_data as global variables
    global data
    global meta_data
    
    # Load the review JSON data
    file_path = os.path.join(json_dir, review_path, category + '.json')
    with open(file_path, 'r') as file:
        data = [json.loads(line) for line in file]
    
    # Load the meta JSON data
    meta_file_path = os.path.join(json_dir, meta_path, 'meta_' + category + '.json')
    with open(meta_file_path, 'r') as meta_file:
        meta_data = [json.loads(line) for line in meta_file]
    
    return file_path, meta_file_path


"""
def navigate_to_review calls the update_review_text function unless
an inappropriate review index is input.
"""
def navigate_to_review():
    handle_submit()
    try:
        review_index = int(entry.get()) - 1
        update_review_text(review_index)
    except ValueError:
        print("Invalid input. Please enter a valid review number.")
    return


"""
def navigate_by_button calls the update_review_text function in
accordance with the controlled review_index determined by the
type of button pressed (previous, or next).
"""
def navigate_by_button(review_index):
    handle_submit()
    update_review_text(review_index)
    return


"""
def on_category_select is executed when the user selects a product
category from the dropdown, and in turn executes def handle_category
and def update_review_text.
"""
def on_category_select(selected_option):
    handle_submit()
    print(f"Selected option: {selected_option}")
    handle_category(selected_option)
    update_review_text(0)
    return


"""
def set_default populates the various options with their default values.
"""
def set_default(option):
    
    if option in cq1 + consumer + flagged:
        dropdown_value = 'n/a'
    elif option in cq3:
        dropdown_value = ''
    else:
        raise ValueError(f"Unexpected value variable option: {option}") 
    text_value = ''

    return dropdown_value, text_value


"""
def update_review_text is called when the user navigates to a valid
review index, either by pressing next, previous or manually inputting
a review number. It calls display_review_text and updates the review 
number, and clears the annotations submitted text. It also looks up
the annotations json file to indicate previous inputs where they exist.
"""
def update_review_text(index):
    if index >= 0 and index < len(data):
        # Get review data
        submit_label.config(text="")
        rating_label.config(text="")
        review_text = data[index]['reviewText']
        product_id = data[index]['asin']
        
        # Get meta data information
        meta_idx = find_asin(meta_data, product_id)
        if meta_idx == 'error':
            product_name = product_id
            product_desc = 'Product record missing'
        else:    
            product_name = meta_data[meta_idx]['title']
            temp_desc = meta_data[meta_idx]['description']
            if not temp_desc or temp_desc is None:
                product_desc = 'No description'
            else:
                product_desc = temp_desc[0]
        
        # Update text boxes
        display_review_text(text_box, review_text)
        display_review_text(product_box, product_desc)
        current_review_index.set(index)

        # Update the text above the text boxes
        text_above_product_box = f"Product: {product_name}"
        text_above_text_box = f"Review {index + 1}"
        product_label.configure(text=text_above_product_box)
        label.configure(text=text_above_text_box)
        
        # Check checkboxes based on existing annotations
        if os.path.isfile(savepath):
            print("savepath:", savepath)
            with open(savepath, 'r') as file:
                existing_annotations = json.load(file)
            if str(index) in existing_annotations:
                print("index valid", '\n')
                saved_options = existing_annotations[str(index)].get('selected_options', [])
                for option, var in checkboxes.items():
                    dropdown_value, text_value = set_default(option)
                    for saved_option in saved_options:
                        if saved_option['option'] == option:
                            dropdown_value = saved_option['dropdown']
                            text_value = saved_option['text']
                            break
                    var['dropdown'].set(dropdown_value)
                    var['text'].set(text_value)
            else:
                for option, var in checkboxes.items():
                    dropdown_value, text_value = set_default(option)
                    var['dropdown'].set(dropdown_value)
                    var['text'].set("")
        else:
            for option, var in checkboxes.items():
                dropdown_value, text_value = set_default(option)
                var['dropdown'].set(dropdown_value)
                var['text'].set("")        
        return


"""
def user_interface lays out the options for each CQ for the user to input,
repeatedly calling def CQ_options.
"""
def user_interface(options_list, opt_values):
    for option in options_list:
        # Create a frame to hold the option elements
        frame = ttk.Frame(second_frame)
        frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        # Option text label
        option_label = ttk.Label(frame, text=option, width=20)
        option_label.pack(side=tk.LEFT)

        # Dropdown selection
        dropdown_var = tk.StringVar()
        dropdown = ttk.Combobox(frame, textvariable=dropdown_var, values=opt_values, width=15)
        dropdown.current(len(opt_values)-1)  # Set the default value
        dropdown.pack(side=tk.LEFT)
        
        # Horizontal space
        hor_space_label = ttk.Label(frame, text='', width=5)
        hor_space_label.pack(side=tk.LEFT)
        
        # Relevant text label
        rel_text_label = ttk.Label(frame, text='Justification:', width=14)
        rel_text_label.pack(side=tk.LEFT)

        # Text box
        text_var = tk.StringVar()
        text_box = ttk.Entry(frame, textvariable=text_var, width=70)
        text_box.pack(side=tk.LEFT)

        # Store the variables in a dictionary
        checkboxes[option] = {'dropdown': dropdown_var, 'text': text_var}
    return checkboxes


# Create the GUI window
window = tk.Tk()
window.title("Review Text Display")
window.geometry("1200x600")

# Create a variable to keep track of the current review index
current_review_index = tk.IntVar()
current_review_index.set(0)

# Create a frame to hold the text boxes and label
text_frame = ttk.Frame(window)
text_frame.pack(side=tk.LEFT, anchor="nw")

# First category and create dropdown options
#category = 'All_Beauty'
category_list = get_categories()
category = tk.StringVar()
category.set(category_list[0]) # Set an initial value for the selected option
print("Category:", category.get())

# Create the dropdown menu
dropdown = tk.OptionMenu(text_frame, category, *category_list, command=on_category_select)
dropdown.pack(side=tk.TOP, anchor='nw')

# Obtain first data
savepath, text_above_product_box = handle_category(category.get())

# Create a label for the text above the product text box
product_label = tk.Label(text_frame, text=text_above_product_box, wraplength=500, justify='left')
product_label.pack(side=TOP, anchor='nw')

# Create a new text box
product_box = tk.Text(text_frame, height=15, width=70, wrap='word')
product_box.pack(side=tk.TOP, anchor='nw')

# Create a label for the text above the review text box
review_desc_frame = ttk.Frame(text_frame)
review_desc_frame.pack(side=tk.TOP, anchor='nw')
text_above_text_box = f"Review {current_review_index.get() + 1}"
label = tk.Label(review_desc_frame, text=text_above_text_box)
label.pack(side=LEFT)
rating_button = tk.Button(review_desc_frame, text="Reveal Rating", command=lambda: handle_rating(current_review_index.get()))
rating_button.pack(side=tk.LEFT)
rating_label = tk.Label(review_desc_frame, text="")
rating_label.pack(side=tk.LEFT)

# Create a text box to display the review text
text_box = tk.Text(text_frame, height=15, width=70, wrap='word')
text_box.pack(side=tk.TOP, anchor='nw')

# Configure the grid to expand properly
window.grid_rowconfigure(1, weight=1)
window.grid_columnconfigure(0, weight=1)
window.grid_columnconfigure(1, weight=1)

# Main
main_frame = ttk.Frame(window)
main_frame.pack(fill=BOTH, expand=1)

# Canvas
my_canvas = Canvas(main_frame)
my_canvas.pack(side=LEFT, fill=BOTH, expand=1)

# Scrollbar
my_scrollbar = tk.Scrollbar(main_frame, orient=HORIZONTAL, command=my_canvas.xview)
my_scrollbar.pack(side=BOTTOM, fill=X)

# Configure the canvas
my_canvas.configure(xscrollcommand=my_scrollbar.set)
my_canvas.bind('<Configure>', lambda e: my_canvas.configure(scrollregion=my_canvas.bbox("all")))

# Create target frame
second_frame = ttk.Frame(my_canvas, width = 1000, height = 500)
second_frame.pack(side=tk.TOP, anchor="nw")

# Create a list to store checkboxes for options
checkboxes = {}

# Display the options checkboxes
cq1_label = ttk.Label(second_frame, text='CQ1')
cq1_label.pack(side=tk.TOP)
cq1 = ['Feature Usage', 'Interaction Time', 'Context Experience']
cq1_range = [1, 2, 3, 4, 5, 'n/a']
user_interface(cq1, cq1_range)

consumer_label = ttk.Label(second_frame, text='Consumer Values')
consumer_label.pack(side=tk.TOP)
consumer = ['Efficiency', 'Excellence', 'Status', 'Esteem', 'Play', 'Aesthetics', 'Ethics', 'Spirituality', 'OVERALL']
consumer_range = [1, 2, 3, 4, 5, 'n/a']
user_interface(consumer, consumer_range)

cq3_label = ttk.Label(second_frame, text='CQ3')
cq3_label.pack(side=tk.TOP)
cq3 = ['Clarity of Sentiment']
cq3_range = [1, 2, 3, 4, 5]
user_interface(cq3, cq3_range)

flagged_label = ttk.Label(second_frame, text='Flagged')
flagged_label.pack(side=tk.TOP)
flagged = ['Review Flagged']
flagged_range = ['Adverse Emotion', 'Ambiguous Value', 'Bot', 'Desc. not Aligned', 'Disingenuous', 'Extraneous', 'Format Problem', 'Missing Value', 'Unclear Value', 'Other', 'n/a']
user_interface(flagged, flagged_range)

# Create navigation buttons
previous_button = tk.Button(window, text="Previous", command=lambda: navigate_by_button(current_review_index.get() - 1))
previous_button.pack(side=tk.LEFT)
next_button = tk.Button(window, text="Next", command=lambda: navigate_by_button(current_review_index.get() + 1))
next_button.pack(side=tk.LEFT)

# Create an input field for navigation
entry_label = tk.Label(window, text="Go to Review:")
entry_label.pack(side=tk.LEFT, anchor=tk.W)
entry = tk.Entry(window)
entry.pack(side=tk.LEFT)
go_button = tk.Button(window, text="Go", command=navigate_to_review)
go_button.pack(side=tk.LEFT)

# Create the submit button
submit_button = tk.Button(window, text="Submit", command=handle_submit)
submit_button.pack(side=tk.LEFT)

# Create a label for the submit message
submit_label = tk.Label(window, text="")
submit_label.pack(side=tk.LEFT)

# Configure scrollbar
my_canvas.create_window((0, 0), window=second_frame, anchor="nw")

# Display the initial review text and any pre-selections
update_review_text(0)

# Start the GUI event loop
window.mainloop()

