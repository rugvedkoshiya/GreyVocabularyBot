import telegram
import json
import random
from config import Config as SETTING
from telegram import ParseMode
from apscheduler.schedulers.blocking import BlockingScheduler

def getRandomWord(jsonFile):
    randNumber = random.randrange(0, 817)
    selectedWord = jsonFile[randNumber]
    if selectedWord["send"] > 10:
        return getRandomWord(jsonFile)
    return selectedWord, randNumber


def increseCount(randNumber):
    with open("data.json", "r") as file:
        oldFile = json.load(file)
    with open("data.json", "w") as file:
        oldFile[randNumber]["send"] += 1
        file.write(json.dumps(oldFile))


def readPreviousData():
    with open("oldData.json", 'r') as file:
        return json.load(file)


def writePreviousData(number):
    previousData = readPreviousData()
    if len(previousData) > 6:
        previousData.pop(0)
    previousData.append(number)
    with open("oldData.json", 'w') as file:
        file.write(json.dumps(previousData))
    return previousData


def runBot(auth, jsonFile):
    selectedWord, randNumber = getRandomWord(jsonFile)
    print(selectedWord)
    print(randNumber)
    increseCount(randNumber)
    wordIndexList = writePreviousData(randNumber)

    response = ""
    for wordIndex in wordIndexList:
        response = "{}\n\n\n<b><i>{}</i></b>\n---------------\n{}".format(response,jsonFile[wordIndex]['word'],jsonFile[wordIndex]['meaning'])
    for chatId in SETTING.CHAT_IDS:
        try:
            telegram.Bot.sendMessage(auth, chatId, text=response, parse_mode=ParseMode.HTML)
        except telegram.error.BadRequest as e:
            telegram.Bot.sendMessage(auth, SETTING.ADMIN_ID, text=f"{chatId} I don't know him/her :)", parse_mode=ParseMode.HTML)
        except telegram.error.Unauthorized as e:
            telegram.Bot.sendMessage(auth, SETTING.ADMIN_ID, text=f"{chatId} has blocked me :(", parse_mode=ParseMode.HTML)
        except Exception as e:
            telegram.Bot.sendMessage(auth, SETTING.ADMIN_ID, text=f"got error with {chatId} :(\n\n{e}", parse_mode=ParseMode.HTML)



def main():
    try:
        auth = telegram.Bot(token=SETTING.TOKEN)
        with open("data.json", "r") as file:
            jsonFile = json.load(file)
        runBot(auth, jsonFile)
    except RecursionError as e:
        # print(e)
        auth = telegram.Bot(token=SETTING.TOKEN)
        runBot(auth, jsonFile)


scheduler = BlockingScheduler()
# scheduler.add_job(main, 'interval', hours=0.01)
scheduler.add_job(main, trigger='cron', hour='10', minute='0')
scheduler.add_job(main, trigger='cron', hour='17', minute='0')
scheduler.start()