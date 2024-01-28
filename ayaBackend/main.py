from fastapi import FastAPI, Request, Response
from pydantic import BaseModel
from openai import OpenAI
import time, json
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware



app = FastAPI()
openai_client = OpenAI(api_key='')
openai_assistant_id = ''

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Item(BaseModel):
    cookie: str
    message: str

class Cookies(BaseModel):
    cookie:str


current_threads = {}

 


@app.post("/api/v1/send_message")
async def send_message(obj: Item):
    if obj.cookie not in current_threads:
        thread = openai_client.beta.threads.create()
        thread_id =  thread.id
        current_threads[obj.cookie] = thread.id
    else:
        thread_id = current_threads[obj.cookie]
    

    openai_client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=obj.message,
    )

    run = openai_client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=openai_assistant_id,
    )

    while run.status == "queued" or run.status == "in_progress":
        run = openai_client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id,
        )
        time.sleep(0.5)
    

    messages = openai_client.beta.threads.messages.list(thread_id=thread_id)

    item = json.loads(messages.model_dump_json())['data'][0]['content'][0]['text']['value']


    return {'response': item}

@app.post("/api/v1/clean_cookie")
async def logout(cookies: Cookies):
    if cookies.cookie in current_threads:
        del current_threads[cookies.cookie]
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5500)
