
import json
import openai
import os
from datetime import datetime
import aiofiles
import asyncio
import time
import boto3

# Instantiate a Boto3 client for SSM
ssm = boto3.client('ssm')

def get_parameter(param_name):
    """Retrieve a parameter from AWS SSM Parameter Store."""
    response = ssm.get_parameter(Name=param_name, WithDecryption=True)
    return response['Parameter']['Value']

# Get OpenAI API key  and Assistant ID from Parameter Store
openai_api_key = get_parameter("openai_api_key")
assistant_id = get_parameter("assistant_id_achievementaward")

#Open AI Client Object
client = openai.OpenAI(api_key = openai_api_key)

# Configure logging to use /tmp directory in AWS Lambda
log_file_path = '/tmp/openai_interaction_log.txt'

# Custom log writing function
async def write_log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"{timestamp} - {message}\n"
    async with aiofiles.open('/tmp/openai_interaction_log.txt', 'a') as log_file:
        await log_file.write(log_message)

async def readlog():

    if os.path.exists(log_file_path):
        async with aiofiles.open(log_file_path, 'r') as log_file:
            log_contents = await log_file.read()
        return log_contents
    else:
        return "Log file does not exist"

def create_thread():   
    try:     
        # Create a thread
        thread = client.beta.threads.create()
        thread_id = thread.id  
        return thread_id
    except Exception as e:      
        return f"An error occurred with create_thread() function: {e}"

def send_message(thread_id, user_message):

    try:
        # Send a message to the thread
        message_response = client.beta.threads.messages.create(
            thread_id=thread_id,
            content = user_message,
            role="user"
        )
        return message_response      
    except Exception as e:
        return f"An error occurred while sending a message: {e}"

async def run_assistant(thread_id, assistant_id):
    try:
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id
        )
        run_id = run.id  

        while run.status != 'completed':
            if run.status == 'required_action':
                raise Exception("Run failed: " + str(run.last_error) + "\n " + str(run.required_action))
            if run.status =='failed':
                raise Exception("Run failed: " + str(run.last_error) + "\n " + str(run.required_action))                    
            print(run.status)
            run = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run_id
            )    
            time.sleep(5)

        await write_log("run_assisstant() openai completed")  

        messages = client.beta.threads.messages.list(
            thread_id = thread_id,
        )
       
        
        await write_log("run_assitsant() run completed" )
        return messages.data
    except Exception as e:
        return f"An error occurred while calling async_handler: {e}"    

async def async_handler(event, context, thread_id):    
    try:       
        headers = {
            "Access-Control-Allow-Headers" : "Content-Type, Authorization" ,
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "OPTIONS, POST"
            

        }    
        #assitant's response to the thread session
        message = await run_assistant(thread_id, assistant_id)

        print(message)
        first_ai_message = message[0].content[0].text.value
        print(message[0].thread_id)
        if (len(thread_id) < 0):
            thread_id  = message[0].thread_id
        
        response_body = {
            "assistant_response": first_ai_message,
            "thread_id" : thread_id,
            #"log_contents": log_contents           
        }
        
     
        # Return the line count as the response
        return {
            
            "isBase64Encoded": False,
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps(response_body)           
        }
        
    except Exception as e:
        await write_log("Main Handler Exception:" + str(e))
        # Correctly format the error response according to Lambda proxy integration requirements
        error_response = {
            "errorMessage": str(e),
        }
        
        return {
            'statusCode': 500,
            'body': json.dumps(error_response),
            "isBase64Encoded": False,
            "headers": headers
        }

def handler(event, context):
    body = json.loads(event['body'])
    thread_message = body['user_message']
    thread_id = body['thread_id']  
    if not thread_id:
        # If thread_id is not provided, create a new thread
            thread_id = create_thread()
    send_message(thread_id, thread_message)
    result = asyncio.run(async_handler(event, context,thread_id))
    return result