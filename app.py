from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
from rktellolib import Tello
import json

app = FastAPI()
app.mount('/static', StaticFiles(directory='static'), name='static')


@app.get("/")
async def get():
    with open('index.html', 'r') as file:
        return HTMLResponse(file.read())
    


if __name__ == '__main__':
    uvicorn.run(app)