import requests

url = "http://127.0.0.1:8080/register"
payload = {"userId": "451211", "nickname": "johnrao",  "gender":"male"}
headers = {"Content-Type": "application/json"}

response = requests.post(url, json=payload, headers=headers)
print(response.json())