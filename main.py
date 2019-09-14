from bs4 import BeautifulSoup
from urllib.request import urlopen, Request
from boto3.dynamodb.conditions import Key, Attr
import os, sys, requests, boto3

chatId = os.environ['TELEGRAM_CHAT_ID']
token = os.environ['TELEGRAM_TOKEN']

def getChapterLists(url):
    req = Request(url)
    req.add_header("User-Agent", "Magic Browser")
    htmlContent = urlopen(req).read()
    soup = BeautifulSoup(htmlContent, "html.parser")
    allLi = soup.select("li")

    chapters = set()

    for eachLi in allLi:
        if (eachLi.a is not None):
            chapters.add(eachLi.a['href'])
    return chapters

def sendTelegramMessage(text):
    requestBody = {
        "chat_id": chatId,
        "text": text
    }
    print("Send message: ", text)
    url = "https://api.telegram.org/bot{}/sendMessage".format(token)
    r = requests.post(url, json=requestBody)
    print(r.status_code)

def startWork(event, context):
    sys.setrecursionlimit(100000)

    dynamodb = boto3.resource("dynamodb")

    table = dynamodb.Table("Things")

    response = table.query(
        KeyConditionExpression=Key('Type').eq('Novel')
    )
    for item in response['Items']:
        name = item['Key']
        url = item['Url']
        firstTime = item['FirstTime']

        currentChapters = set()
        if 'Chapters' in item:
            currentChapters = item['Chapters']
        newChapters = getChapterLists(url)

        differences = newChapters - currentChapters

        if firstTime or (len(differences) != 0) :
            table.update_item(
                Key={
                    'Type': 'Novel',
                    'Key':  name,
                },
                UpdateExpression='SET Chapters = :val1, FirstTime = :val2',
                ExpressionAttributeValues={
                    ':val1': newChapters,
                    ':val2': False
                }
            )
            if not firstTime: 
                for difference in differences:
                    chapterUrl = url + difference
                    sendTelegramMessage("#小说 {}".format(chapterUrl))
        else:
            print("No new chapters")
