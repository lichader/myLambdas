from bs4 import BeautifulSoup
from urllib.request import urlopen, Request
import boto3
import uuid
import sys
sys.setrecursionlimit(100000)

req = Request("https://www.ptwxz.com/html/9/9102/")
req.add_header("User-Agent", "Magic Browser")

htmlContent = urlopen(req).read()

soup = BeautifulSoup(htmlContent, "html.parser")

print(soup.title)

allLi = soup.select("li")

chapters = set()

for eachLi in allLi:
    if (eachLi.a is not None):
        chapters.add(eachLi.a['href'])

print(chapters)

dynamodb = boto3.resource("dynamodb")

table = dynamodb.Table("Novels")

# print(table.creation_date_time)
# print(table.item_count)

with table.batch_writer() as batch:
    for c in chapters:
        batch.put_item(
            Item={
                'Id': str(uuid.uuid4()),
                'chapters': c,
                'Name': '凡人修仙记之仙界篇'
            }
        )

# lookup all novels that requires check


# compare each one by one
