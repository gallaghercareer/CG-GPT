import openai
import os
from dotenv import load_dotenv
import requests
import json

def create_assistant(api_key, model, name, instructions, tools):
 
    
    url = "https://api.openai.com/v1/assistants"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "OpenAI-Beta": "assistants=v1"
    }
    payload = {
        "model": model,
        "name": name,
        "instructions": instructions,
        "tools": tools
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    if response.status_code == 200 or response.status_code == 201:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

load_dotenv() 
openai_api_key = os.getenv('OPENAI_API_KEY')
# Example usage
api_key = openai_api_key # Replace with your actual API key
model = "gpt-3.5-turbo"
name = "Award Writer"
instructions = "You are helping write awards."
tools = [{}]

assistant_response = create_assistant(api_key, model, name, instructions, tools)
if assistant_response:
    assistant_id = assistant_response.get('id', 'No ID found')
    print(f"Assistant created successfully. ID: {assistant_id}")
