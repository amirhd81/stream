import requests

url = "https://tapi.bale.ai/751585554:XalUAe8C-fm5rgcUfvzPoezfILcSC7s5vSA/setWebhook"
data = {
    "url": "https://www.avalin48.ir/webhook/streamable",
}

response = requests.post(url, json=data)

print("Status code:", response.status_code)
print("Response body:", response.text)
