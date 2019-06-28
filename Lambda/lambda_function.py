import os,sys,json,requests,datetime
import boto3
from boto3.dynamodb.conditions import Key,Attr
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, TemplateSendMessage, ConfirmTemplate, MessageAction
)
from linebot.exceptions import (
    LineBotApiError, InvalidSignatureError
)

channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

db = boto3.resource("dynamodb")

def lambda_handler(event, context):
    print(event)
    signature = event["headers"]["X-Line-Signature"]
    body = event["body"]
    ok_json = {"isBase64Encoded": False,
               "statusCode": 200,
               "headers": {},
               "body": ""}
    error_json = {"isBase64Encoded": False,
                  "statusCode": 403,
                  "headers": {},
                  "body": "Error"}

    @handler.add(MessageEvent, message=TextMessage)
    def message(line_event):
        if(line_event.message.text =="部屋の温度と湿度は？"):
            table = db.Table("sensor_data")
            response = table.query(KeyConditionExpression=Key("sensor_type").eq("temp") & Key("sensor_name").eq("raspi"),ScanIndexForward = False,Limit=1)
            temp=str(response["Items"][0]["payload"]["value"]-3)
            response = table.query(KeyConditionExpression=Key("sensor_type").eq("humi") & Key("sensor_name").eq("raspi"),ScanIndexForward = False,Limit=1)
            humi=str(response["Items"][0]["payload"]["value"])
            message = TextSendMessage(text="温度は"+temp+"℃で、湿度は"+humi+"%だよ")
        elif(line_event.message.text == "次のバスの時刻は？"):
            message = TemplateSendMessage(
                alt_text='Confirm template',
                template=ConfirmTemplate(
                    text='今から出かける？それとも帰る？',
                    actions=[
                        MessageAction(
                            label='出かける',
                            text='出発のバス時刻'
                        ),
                        MessageAction(
                            label='帰る',
                            text='帰宅のバス時刻'
                        )
                    ]
                )
            )
        elif(line_event.message.text == "帰宅のバス時刻" or line_event.message.text == "出発のバス時刻"):
            utc = datetime.datetime.now()
            now=utc+datetime.timedelta(hours=9)
            minutes=now.hour * 60 + now.minute
            if(line_event.message.text == "出発のバス時刻"):
                table = db.Table("bus_time_GH")
            else:
                table = db.Table("bus_time_St")
            if(now.weekday()<5):
                response = table.query(KeyConditionExpression=Key("day").eq("weekday") & Key("min").gt(minutes),ScanIndexForward = True,Limit=3)
            else:
                response = table.query(KeyConditionExpression=Key("day").eq("Holiday") & Key("min").gt(minutes),ScanIndexForward = True,Limit=3)
            item=response["Items"]
            if(item==[]):
                text = "今日はもうないね"
            else:
                text="次は、"
                for i in item:
                    text += i["time"]+"、"
                text=text[:-1]
                text+="があるよ"
            message = TextSendMessage(text=text)
        elif(line_event.message.text == "エアコン操作して"):
            message = TemplateSendMessage(
                alt_text='Confirm template',
                template=ConfirmTemplate(
                    text='つける？それとも消す？',
                    actions=[
                        MessageAction(
                            label='つける',
                            text='エアコンをつけて'
                        ),
                        MessageAction(
                            label='消す',
                            text='エアコンを消して'
                        )
                    ]
                )
            )
        elif(line_event.message.text == "エアコンをつけて"):
            requests.post(os.getenv('WEB_HOOK_URL1', None), data = json.dumps({
                "value1":"test"
            }))
            message = TextSendMessage(text="エアコンつけたよ")
        elif(line_event.message.text == "エアコンを消して"):
            requests.post(os.getenv('WEB_HOOK_URL2', None), data = json.dumps({
                "value1":"test"
            }))
            message = TextSendMessage(text="エアコン消したよ")
        elif(line_event.message.text == "天気を教えて"):
            weather_json = requests.get(os.getenv('WEATHER_URL', None))
            weather_dict=json.loads(weather_json.text)
            weather=weather_dict["forecasts"]
            text = "千葉の天気をお知らせします!"
            for w in weather:
                text += "\n\n"+w["dateLabel"]+"の天気は"+w["telop"]
                if(w["temperature"]["min"]!=None and w["temperature"]["max"]!=None):
                    text += "\n最低気温は"+w["temperature"]["min"]["celsius"]+"℃"
                    text += "\n最高気温は"+w["temperature"]["max"]["celsius"]+"℃"
                text+="だよ"
            message = TextSendMessage(text=text)
        else:
            message = TextSendMessage(text="定型文以外は非対応")
        
        line_bot_api.reply_message(line_event.reply_token, message)

    try:
        handler.handle(body, signature)
    except LineBotApiError as e:
        print("Got exception from LINE Messaging API: %s\n" % e.message)
        for m in e.error.details:
            print("  %s: %s" % (m.property, m.message))
        return error_json
    except InvalidSignatureError:
        return error_json

    return ok_json