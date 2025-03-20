import requests

JENKINS_URL = "http://localhost:8080"
JOB_NAME = "Test_AI_Agent"
API_TOKEN = "1179c4a777d7cebd76fe4ea4e576c73514"
USERNAME = "inviul"

# Step 1: Get the Crumb Token
crumb_response = requests.get(
    f"{JENKINS_URL}/crumbIssuer/api/json",
    auth=(USERNAME, API_TOKEN)
)
crumb_data = crumb_response.json()
crumb = crumb_data["crumb"]

# Step 2: Trigger the Job
headers = {"Jenkins-Crumb": crumb, "Content-Type": "application/x-www-form-urlencoded"}
params = {"MY_PARAM": "Avinash"}
trigger_url = f"{JENKINS_URL}/job/{JOB_NAME}/buildWithParameters?token=1179c4a777d7cebd76fe4ea4e576c73514"

response = requests.post(trigger_url, headers=headers, data=params, auth=(USERNAME, API_TOKEN))

print("Response: ", response.text)
print("Response: ", response.content)

if response.status_code == 201:
    print("Jenkins job triggered successfully!")
else:
    print(f"Failed to trigger job: {response.status_code}, {response.text}")
