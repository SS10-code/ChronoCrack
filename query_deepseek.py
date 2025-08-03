import requests

def query_deepseek(prompt, api_key):
    url = "https://openrouter.ai/api/v1/chat/completions"
    get_header = {"Authorization": f"Bearer {api_key}","Content-Type": "application/json"}

    #context for the ai
    request_payloads =  {"model":"deepseek/deepseek-r1-0528:free",  "messages":[{"role": "system","content":"You are an AI that is helping a student understand topics keep you explanations breif and simple" },  {"role": "user", "content": prompt } ]}

    response = requests.post(url, headers = get_header, json = request_payloads)#reply

    result =  response.json()
    
    return result["choices"][0]["message"]["content"]