from bs4 import BeautifulSoup
from boto3.dynamodb.conditions import Key
import os
import sys
import requests
import boto3

chatId = os.getenv("TELEGRAM_CHAT_ID", "")
token = os.getenv("TELEGRAM_TOKEN", "")
isDebug = os.getenv("DEBUG", "false").lower() == "true"

headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "}


def getChapterLists(url):
    mainPage = requests.get(url=url, headers=headers, verify=False)

    if isDebug:
        print(f"URL: {url}")
        print(f"Main page status code: {mainPage.status_code}")
        print(f"Main page encoding: {mainPage.encoding}")

    soup = BeautifulSoup(mainPage.content, "html.parser")

    if isDebug:
        soup.prettify()

    allLi = soup.select("li")

    if isDebug:
        print(f"Total li: {len(allLi)}")

    chapters = set()
    for eachLi in allLi:
        if isDebug:
            print(f"Li: {eachLi}")

        if (eachLi.a is not None) and (eachLi.a["href"] != ""):
            if isDebug:
                print(f"Li a: {eachLi.a}")
                print(f"Li a href: {eachLi.a['href']}")

            chapters.add(eachLi.a["href"])
    return chapters


def sendTelegramMessage(text):
    requestBody = {"chat_id": chatId, "text": text}
    print("Send message: ", text)
    url = "https://api.telegram.org/bot{}/sendMessage".format(token)
    r = requests.post(url, json=requestBody)
    print(f"Message status code: {r.status_code}")


def startWork(event, context):
    sys.setrecursionlimit(100000)

    dynamodb = boto3.resource("dynamodb")

    table = dynamodb.Table("Things")

    response = table.query(KeyConditionExpression=Key("Type").eq("Novel"))
    for item in response["Items"]:
        name = item["Key"]
        url = item["Url"]
        firstTime = item["FirstTime"]

        currentChapters = set()
        if "Chapters" in item:
            currentChapters = item["Chapters"]
        newChapters = getChapterLists(url)

        if isDebug:
            print(f"Current chapters: {currentChapters}")
            print(f"New chapters: {newChapters}")

        differences = newChapters - currentChapters

        print(f"{name} has new chapters: {len(differences)}")

        if firstTime or (len(differences) != 0):
            table.update_item(
                Key={
                    "Type": "Novel",
                    "Key": name,
                },
                UpdateExpression="SET Chapters = :val1, FirstTime = :val2",
                ExpressionAttributeValues={":val1": newChapters, ":val2": False},
            )

            if not firstTime:
                for difference in differences:
                    chapterUrl = url + difference

                    chapterPage = requests.get(
                        url=chapterUrl, headers=headers, verify=False
                    )
                    chapterPage.encoding = "gb18030"

                    soup = BeautifulSoup(chapterPage.text, "html.parser")

                    sendTelegramMessage(f"#小说 {soup.title.string} {chapterUrl}")
        else:
            print(f"{name} has no new chapters")


if __name__ == "__main__":
    startWork(None, None)
