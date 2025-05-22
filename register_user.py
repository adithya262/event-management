import requests
import json

# Define the API endpoint URL
url = "http://127.0.0.1:8000/api/auth/register"

# Define the data for the new user
# Replace with actual data you want to use for testing
user_data = {
    "email": "testuser@example.com",
    "username": "testuser123",
    "full_name": "Test User Programmatic",
    "password": "securepassword"
}

# Define the headers for the request
headers = {
    "Content-Type": "application/json"
}

# Send the POST request
try:
    response = requests.post(url, data=json.dumps(user_data), headers=headers)

    # Print the response details
    print(f"Status Code: {response.status_code}")
    print("Response Body:")
    try:
        print(json.dumps(response.json(), indent=4))
    except requests.exceptions.JSONDecodeError:
        print(response.text)

except requests.exceptions.ConnectionError as e:
    print(f"Error connecting to the server: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}") 