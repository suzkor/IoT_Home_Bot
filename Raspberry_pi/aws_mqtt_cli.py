from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import time
import json
import dht11
import RPi.GPIO as GPIO

# Custom MQTT message callback
def customCallback(client, userdata, message):
    print("Received a new message: ")
    print(message.payload)
    print("from topic: ")
    print(message.topic)
    print("--------------\n\n")

host = "XXX.amazonaws.com"
rootCAPath = "root-CA.crt"
certificatePath = "XXX.cert.pem"
privateKeyPath = "XXX.private.key"
port = 8883
clientId = "client_name"
pub_topic = "publish_topic_name"
sub_topic = "subscribe_topic_name"

# Init AWSIoTMQTTClient
myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId)
myAWSIoTMQTTClient.configureEndpoint(host, port)
myAWSIoTMQTTClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

# AWSIoTMQTTClient connection configuration
myAWSIoTMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
myAWSIoTMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
myAWSIoTMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
myAWSIoTMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
myAWSIoTMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec

# Connect and subscribe to AWS IoT
myAWSIoTMQTTClient.connect()
myAWSIoTMQTTClient.subscribe(sub_topic, 1, customCallback)
time.sleep(2)

# DHT setup
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
instance = dht11.DHT11(pin = 14)

# Publish to the same topic in a loop forever
while True:
	cnt = 0
	temp = []
	humi = []
	while(cnt<30):
		result = instance.read()
		if(result.temperature != 0):
			temp.append(result.temperature)
		if(result.humidity != 0):
			humi.append(result.humidity)
		time.sleep(10)
		cnt += 1
	message = {}
	message["name"] = "raspi"
	message['time'] = int(time.mktime(time.gmtime()))
	
	#mean
	if(len(temp) != 0):
		temp_ave=sum(temp)/len(temp)
		message["type"] = "temp"
		message["value"] = temp_ave
		messageJson = json.dumps(message)
		myAWSIoTMQTTClient.publish(pub_topic, messageJson, 1)
		
		humi_ave=sum(humi)/len(humi)
		message["type"] = "humi"
		message["value"] = humi_ave
		messageJson = json.dumps(message)
		myAWSIoTMQTTClient.publish(pub_topic, messageJson, 1)
