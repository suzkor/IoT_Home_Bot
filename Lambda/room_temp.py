import json
import boto3
from boto3.dynamodb.conditions import Key,Attr

db = boto3.resource("dynamodb")

def lambda_handler(event, context):
    table = db.Table("sensor_data")
    response = table.query(KeyConditionExpression=Key("sensor_type").eq(
        "temp") & Key("sensor_name").eq("raspi"), ScanIndexForward=False, Limit=1)
    temp = str(response["Items"][0]["payload"]["value"]-3)
    response = table.query(KeyConditionExpression=Key("sensor_type").eq(
        "humi") & Key("sensor_name").eq("raspi"), ScanIndexForward=False, Limit=1)
    humi = str(response["Items"][0]["payload"]["value"])
    return {
        'statusCode': 200,
        'body': json.dumps({"temp":temp, "humi":humi})
    }
