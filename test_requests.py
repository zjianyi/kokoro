import requests

print("Requests module imported successfully!")
print(f"Requests version: {requests.__version__}")

# Make a simple request to verify functionality
response = requests.get("https://httpbin.org/get")
print(f"Status code: {response.status_code}")
print(f"Response: {response.json()}") 