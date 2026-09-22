import requests

application_id = 1
interview_id = 2

url = (
    f"http://127.0.0.1:5000/api/applications/"
    f"{application_id}/interviews/{interview_id}"
)

response = requests.delete(url)

print("Status:", response.status_code)
print("Response:", response.text)