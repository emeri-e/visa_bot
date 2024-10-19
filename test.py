import requests
  
url = "https://scraper-api.smartproxy.com/v2/scrape"
  
payload = {
      "target": "universal",
      "url": "https://ipinfo.io/",
      "headless": "html",
      "geo": "Pakistan"
}
  
headers = {
    "accept": "application/json",
    "content-type": "application/json",
    "authorization": ""
}
  
response = requests.post(url, json=payload, headers=headers)
  
print(response.text)