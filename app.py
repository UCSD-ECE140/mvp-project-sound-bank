from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
from rktellolib import Tello
import json
import paho.mqtt.client as paho
from paho import mqtt
from dotenv import load_dotenv
import os


app = FastAPI()
app.mount('/static', StaticFiles(directory='static'), name='static')
client1 = paho.Client(callback_api_version=paho.CallbackAPIVersion.VERSION1, client_id="", userdata=None, protocol=paho.MQTTv5)

load_dotenv()  # Load environment variables from .env file



def on_connect(client, userdata, flags, rc, properties=None):
    """
        Prints the result of the connection with a reasoncode to stdout ( used as callback for connect )
        :param client: the client itself
        :param userdata: userdata is set when initiating the client, here it is userdata=None
        :param flags: these are response flags sent by the broker
        :param rc: stands for reasonCode, which is a code for the connection result
        :param properties: can be used in MQTTv5, but is optional
    """
    print("CONNACK received with code %s." % rc)

def on_message(client, userdata, msg):
    print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))



client1.on_connect = on_connect
# enable TLS for secure connection
client1.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
# set username and password
client1.username_pw_set(os.getenv("HIVEMQ_USERNAME"), os.getenv("HIVEMQ_PASSWORD"))
# connect to HiveMQ Cloud on port 8883 (default for MQTT)
client1.connect("6e55730bd5364136b3eea32f4fcb7183.s1.eu.hivemq.cloud", 8883)





@app.get("/")
async def get():
    with open('index.html', 'r') as file:
        return HTMLResponse(file.read())
    
@app.post("/queue_add")
async def queue_add(request: Request):
    data = await request.json()
    song = data.get("song")
    if song:
        client1.publish("queue/add", payload=song, qos=1)
        return {"message": "Song added to the queue"}
    else:
        return {"message": "No song provided"}


if __name__ == '__main__':
    uvicorn.run(app)