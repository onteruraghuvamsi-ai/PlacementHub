
import requests

BASE_URL = "http://127.0.0.1:5000/api/applications"


# 1. Search for Python jobs
print("\n--- SEARCH ---")

response = requests.get(
    BASE_URL,
    params={"search": "Python"}
)

print("Status:", response.status_code)
print(response.json())


# 2. Filter by status
print("\n--- FILTER BY STATUS ---")

response = requests.get(
    BASE_URL,
    params={"status": "Applied"}
)

print("Status:", response.status_code)
print(response.json())


# 3. Dashboard statistics
print("\n--- DASHBOARD ---")

response = requests.get(f"{BASE_URL}/stats")

print("Status:", response.status_code)
print(response.json())


# 4. External GitHub API
print("\n--- GITHUB ORGANIZATION ---")

response = requests.get(
    f"{BASE_URL}/github/microsoft",
    timeout=10
)

print("Status:", response.status_code)
print(response.json())