'''
This script sends a GET request to the Evaluation Endpoint of the Flask API to evaluate the model with different hyperparameters.
The hyperparameters are specified as a dictionary and converted to a string for the GET request.
The response from the API is parsed as JSON to extract the evaluation results.
The evaluation results include accuracy, precision, recall, and F1-score metrics.
'''
import requests
import pandas as pd

# URL of the Evaluation Endpoint
evaluation_url = 'http://127.0.0.1:5000/evaluate_model'

# Load the training data
train_data = pd.read_csv('annotated_empatheticdialogues.csv')

# Hyperparameters for the model
hyperparameters = {'alpha': [0.1, 0.5, 1.0, 1.5, 2.0]}

# Convert hyperparameters to a string for GET request
hyperparameters_str = str(hyperparameters)

# Make a GET request to the Evaluation Endpoint with hyperparameters
response = requests.get(evaluation_url, params={'hyperparameters': hyperparameters_str})

# Check if the request was successful (status code 200)
if response.status_code == 200:
    try:
        # Print the entire response content
        print("Response Content:", response.content)
        
        # Parse the JSON response
        evaluation_results = response.json()
        if 'error' in evaluation_results:
            print("Error:", evaluation_results['error'])
        else:
            # Print the evaluation results
            print("Evaluation Results:")
            print(evaluation_results)
    except ValueError:
        print("Error: Invalid JSON format in response.")
else:
    # Print the error message if request was not successful
    print("Error:", response.text)
