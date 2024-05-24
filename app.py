from fastapi import FastAPI, WebSocket, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
import json
import paho.mqtt.client as paho
from paho import mqtt
from dotenv import load_dotenv
import os


app = FastAPI()
app.mount('/static', StaticFiles(directory='static'), name='static')



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


# with this callback you can see if your publish was successful
def on_publish(client, userdata, mid, properties=None):
    """
        Prints mid to stdout to reassure a successful publish ( used as callback for publish )
        :param client: the client itself
        :param userdata: userdata is set when initiating the client, here it is userdata=None
        :param mid: variable returned from the corresponding publish() call, to allow outgoing messages to be tracked
        :param properties: can be used in MQTTv5, but is optional
    """
    print("mid: " + str(mid))

def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    """
        Prints a reassurance for successfully subscribing
        :param client: the client itself
        :param userdata: userdata is set when initiating the client, here it is userdata=None
        :param mid: variable returned from the corresponding publish() call, to allow outgoing messages to be tracked
        :param granted_qos: this is the qos that you declare when subscribing, use the same one for publishing
        :param properties: can be used in MQTTv5, but is optional
    """
    print("Subscribed: " + str(mid) + " " + str(granted_qos))

def on_message(client, userdata, msg):
    """
        Prints a mqtt message to stdout ( used as callback for subscribe )
        :param client: the client itself
        :param userdata: userdata is set when initiating the client, here it is userdata=None
        :param msg: the message with topic and payload
    """
    print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))




@app.get("/")
async def get():
    with open('index.html', 'r') as file:
        return HTMLResponse(file.read())
    
@app.post("/queue_add")
async def queue_add(request: Request):
    data = await request.json()
    song = data.get("song")
    print(song)
    
    if song:
        client.publish("songs/add", payload=song, qos=1)
        return {"message": "Song added to the queue"}
    else:
        return {"message": "No song provided"}




if __name__ == '__main__':
    load_dotenv()

    client = paho.Client(callback_api_version=paho.CallbackAPIVersion.VERSION1, client_id="", userdata=None, protocol=paho.MQTTv5)

    broker_address = os.environ.get('BROKER_ADDRESS')
    broker_port = int(os.environ.get('BROKER_PORT'))
    username = os.environ.get('USER_NAME')
    password = os.environ.get('PASSWORD')

    


    # enable TLS for secure connection
    client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
    # set username and password
    client.username_pw_set(username, password)
    # connect to HiveMQ Cloud on port 8883 (default for MQTT)
    client.connect(broker_address, broker_port)

    client_sub = paho.Client(callback_api_version=paho.CallbackAPIVersion.VERSION1, client_id="", userdata=None, protocol=paho.MQTTv5)
    client_sub.on_connect = on_connect

     # enable TLS for secure connection
    client_sub.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
    # set username and password
    client_sub.username_pw_set(username, password)
    # connect to HiveMQ Cloud on port 8883 (default for MQTT)
    client_sub.connect(broker_address, broker_port)

    client_sub.on_message = on_message
    client_sub.on_publish = on_publish

    # subscribe to all topics of numbers by using the wildcard "#"
    client_sub.subscribe("songs/#", qos=1)


    client_sub.loop_start()

    uvicorn.run(app)