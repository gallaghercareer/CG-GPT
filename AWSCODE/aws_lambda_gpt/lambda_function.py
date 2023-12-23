
import json
import openai
import os
from datetime import datetime
import asyncio
import aiohttp

# Configure logging to use /tmp directory in AWS Lambda
log_file_path = '/tmp/openai_interaction_log.txt'

# Custom log writing function
def write_log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"{timestamp} - {message}\n"
    with open('/tmp/openai_interaction_log.txt', 'a') as log_file:
        log_file.write(log_message)

#Open AI Client Object
#we actually need this from the STORE system parameter
openai_api_key = "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"
client = openai.OpenAI(api_key = openai_api_key)


# Async function to create a thread
async def create_thread():
    url = "https://api.openai.com/v1/beta/threads"
    headers = {"Authorization": f"Bearer {openai_api_key}"}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                thread_id = data['id']
                write_log("create_thread() openai response object:" + str(data))
                return thread_id
            else:
                error_message = await response.text()
                write_log("Error in create_thread():" + error_message)
                return None  # Handle error appropriately

# Async function to send a message
async def send_message(thread_id, user_message):
    url = f"https://api.openai.com/v1/beta/threads/{thread_id}/messages"
    headers = {"Authorization": f"Bearer {openai_api_key}"}
    payload = {
        "role": "user",
        "content": user_message
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                write_log("send_message() openai response object:" + str(data))
                return data
            else:
                error_message = await response.text()
                write_log("Error in send_message():" + error_message)
                return None  # Handle error appropriately

# Async function to run assistant
async def run_assistant(thread_id, assistant_id):
    url = f"https://api.openai.com/v1/beta/threads/{thread_id}/runs"
    headers = {"Authorization": f"Bearer {openai_api_key}"}
    payload = {"assistant_id": assistant_id}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                write_log("run_assistant() openai response object:" + str(data))
                return data
            else:
                error_message = await response.text()
                write_log("Error in run_assistant():" + error_message)
                return None  # Handle error appropriately
async def handler(event, context):
    try:
        body = json.loads(event['body'])
        assistant_id = "asst_dRsEPaYci0NTsLzk5ot52hpf"  # Define outside for reuse
        thread_id = body.get('thread_id')
        user_message = body.get('user_message')
        
        if not thread_id:
            thread_id = await create_thread()
            if not thread_id:
                raise Exception("Failed to create thread")

        message_response = await send_message(thread_id, user_message)
        if message_response is None:
            raise Exception("Failed to send message")

        assistant_response = await run_assistant(thread_id, assistant_id)
        if assistant_response is None:
            raise Exception("Failed to run assistant")

        # Read the log file and include its contents in the response
        log_contents = ""
        if os.path.exists(log_file_path):
            with open(log_file_path, 'r') as log_file:
                log_contents = log_file.read()

        response_body = {
            "assistant_response": assistant_response,
            "thread_id": thread_id,
            "log_contents": log_contents
        }

        return {
            "isBase64Encoded": False,
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(response_body)
        }

    except Exception as e:
        write_log("Main Handler Exception:" + str(e))
        log_contents = ""
        if os.path.exists(log_file_path):
            with open(log_file_path, 'r') as log_file:
                log_contents = log_file.read()

        # Correctly format the error response according to Lambda proxy integration requirements
        error_response = {
            "errorMessage": str(e),
            "log_contents": log_contents
        }
        
        return {
            'statusCode': 500,
            'body': json.dumps(error_response),
            "isBase64Encoded": False,
            "headers": { "Content-Type": "application/json" }
        }