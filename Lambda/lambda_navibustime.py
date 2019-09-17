import json
import requests as rq
import datetime
from bs4 import BeautifulSoup

def lambda_handler(event, context):
    url="https://www.navitime.co.jp/bus/diagram/timelist?departure="+event["dep"]+"&arrival="+event["arrival"]+"&line="+event["line"]
    html=rq.get(url)
    read_count=event["count"]
    
    try:
        soup = BeautifulSoup(html.text,"html.parser")
        timelist=soup.find("dl",attrs={"class","time-list-frame"})
        deplist=timelist.find_all("span",attrs={"class","time dep"})
        
        deptime_list=[]
        now=(datetime.datetime.now() + datetime.timedelta(hours=9)).strftime("%Y/%m/%d ")
        for l in deplist:
           deptime_list.append([datetime.datetime.strptime(now + l.text,"%Y/%m/%d %H:%M"),l.text])
           
        nextbus=[]
        for deptime in deptime_list:
            if deptime[0]>(datetime.datetime.now() + datetime.timedelta(hours=9)):
                nextbus.append(deptime[1])
                
        result="次は"
        try:
            for i in range(read_count):
                result+=", "+nextbus[i]
            result+="があるよ"
        except:
            if len(nextbus)!=0:
                result+="があるけど、これで終わりだね"
            else:
                result="今日はもうないよ"
    except Exception as e:
        result=e
    print(result)    
    return {'body': result}
