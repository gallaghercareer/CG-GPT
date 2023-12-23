
import json
import openai
import os
from datetime import datetime
import asyncio

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



def create_thread():    
    try:     
        # Create a thread
        thread = client.beta.threads.create()
        thread_id = thread.id  
        write_log("create_thread() openai response object:" + str(thread))     
        return thread_id
    except Exception as e:
        write_log("Error in create_thread():" + str(e))
        return f"An error occurred with create_thread() function: {e}"

def send_message(thread_id, user_message):
    try:
        # Send a message to the thread
        message_response = client.beta.threads.messages.create(
            thread_id=thread_id,
            content = user_message,
            role="user"
        )
        write_log("send_message() openai response object:" + str(message_response))   
        return message_response
    except Exception as e:
        write_log("Error in create_thread():" +str(e))
        return f"An error occurred while sending a message: {e}"
    

def run_assistant(thread_id, assistant_id):
    try:
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id
        )
        write_log("run_assisstant() openai response object:" + str(run))  

        messages = client.beta.threads.messages.list(
            thread_id = thread_id
        )

        response = messages
        write_log("run_assitsant() response object is as follows" + str(response))
        return response
    except Exception as e:
        write_log("Error in create_thread():" + str(e))
        return f"An error occurred while running assistant over thread session: {e}"

async def handler(event, context):

    try:
       
        #the Assistant ID
        assitant_id = "asst_dRsEPaYci0NTsLzk5ot52hpf"

        body = json.loads(event['body'])

        thread_id = body['thread_id']
        user_message = body['user_message']
        
        if not thread_id:
            # If thread_id is not provided, create a new thread
            thread_id= create_thread()
           
        #add user's message to thread
        send_message(thread_id, user_message)

        #assitant's response to the thread session
        assistant_response = run_assistant(thread_id, assitant_id)  # Replace with your assistant ID
        
        # Read the log file and include its contents in the response
        log_contents = ""
        if os.path.exists(log_file_path):
            with open(log_file_path, 'r') as log_file:
                log_contents = log_file.read()

        response_body = {
            "assistant_response": assistant_response,
            "thread_id" : thread_id,
            "log_contents": log_contents           
        }
        
        # Return the line count as the response
        return {
            "isBase64Encoded": False,
            "statusCode": 200,
            "headers": { "Content-Type": "application/json" },
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