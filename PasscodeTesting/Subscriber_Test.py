import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe("esp32/state")
    
def on_message(client, userdata, msg):
    print("Message Received: " + msg.topic + " " + str(msg.payload))

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect('130.215.172.60')
client.subscribe("esp32/state", 0)

while(True):
    client.loop()
#     print("waiting...")