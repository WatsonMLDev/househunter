import requests
import json

try:
    response = requests.get("http://localhost:8000/properties")
    data = response.json()
    if data:
        first_item = data[0]
        print("First item keys:", first_item.keys())
        print("Created At field:", first_item.get('created_at'))
    else:
        print("No data returned")
except Exception as e:
    print(e)
