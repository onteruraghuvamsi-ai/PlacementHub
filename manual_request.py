
import requests

BASE_URL = "http://127.0.0.1:5000/api/applications"

# 1. CREATE
print("\n--- CREATE ---")

data = {
    "company": "Prodesk",
    "role": "Python Developer",
    "location": "Noida",
    "status": "Applied"
}

response = requests.post(BASE_URL, json=data)

print("Status:", response.status_code)
print("Response:", response.json())

# Get the actual ID created by the database
application_id = response.json()["id"]


# 2. READ ALL
print("\n--- READ ALL ---")

response = requests.get(BASE_URL)

print("Status:", response.status_code)
print("Response:", response.json())


# 3. READ ONE
print("\n--- READ ONE ---")

response = requests.get(f"{BASE_URL}/{application_id}")

print("Status:", response.status_code)
print("Response:", response.json())


# 4. UPDATE
print("\n--- UPDATE ---")

update_data = {
    "status": "Interview"
}

response = requests.put(
    f"{BASE_URL}/{application_id}",
    json=update_data
)

print("Status:", response.status_code)
print("Response:", response.json())


# 5. DELETE
print("\n--- DELETE ---")

response = requests.delete(
    f"{BASE_URL}/{application_id}"
)

print("Status:", response.status_code)
print("Response:", response.json())