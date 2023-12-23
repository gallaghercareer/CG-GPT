from fastapi import FastAPI,HTTPException
from pydantic import BaseModel
from mangum import Mangum
import openai

app = FastAPI()

class InputData(BaseModel):
    text: str
    thread_id: str | None  # User may or may not send a thread_id

class AssistantResponse(BaseModel):
    response: str
    thread_id: str

#Open AI Client Object
#we actually need this from the STORE system parameter
openai_api_key = "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"
client = openai.OpenAI(api_key=openai_api_key)

#the Assistant ID
assitant_id = "asst_dRsEPaYci0NTsLzk5ot52hpf"

async def create_thread():
    response = await client.Thread.create()
     # Extract the thread ID from the response
    thread_id = response['id']  # Extract the 'id' field
    return thread_id  # Update the key path as per the actual response
  
async def send_message(thread_id, message_content):
    await client.ThreadMessage.create(
        thread_id=thread_id,
        role="user",
        content=message_content
    )

async def run_assistant(thread_id, assistant_id):
    response = await client.ThreadRun.create(
        thread_id=thread_id,
        assistant_id=assistant_id
    )
    
    # Assuming 'response' is the response dictionary from the API
    most_recent_message = None

    # Iterate over the messages in reverse order
    for message in reversed(response.get("messages", [])):
        if message.get("role") == "assistant":
            most_recent_message = message.get("content", {}).get("text", "")
            break  # Found the most recent assistant message

    return most_recent_message

@app.get("/")
async def hello():
    return {"message": "hello world"}

@app.post("/generate_openai_response/", response_model=str)
async def handler(data: InputData):
    try:
        #thread id from POST request
        thread_id = data.thread_id
        if not thread_id:
            # If thread_id is not provided, create a new thread
            thread_id= await create_thread()
           
        #add user's message to thread
        await send_message(thread_id, data.text)

        #assitant's response to the thread session
        assistant_response = await run_assistant(thread_id, 'your_assistant_id')  # Replace with your assistant ID
        return AssistantResponse(response=assistant_response, thread_id=thread_id)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
handler = Mangum(app)