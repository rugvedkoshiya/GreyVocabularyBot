import telegram
import json
import random
from config import Config as SETTING
from telegram import ParseMode
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
from datetime import tzinfo
from gtts import gTTS
import ffmpeg
import logging
from datetime import date

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


def convertToOGG():
    output = "myWord." + 'ogg'
    try:
        stream = ffmpeg.input("myWord.mp3").output(output, ar='48000', ac=2, acodec='libopus', ab='32k', threads=2).overwrite_output()
        ffmpeg.run(stream, quiet=True)
        return output
    except RuntimeError as e:
        logging.error('An error occured whilst converting the file.', exc_info=e)


def runBot(auth, jsonFile, sendTime):
    selectedWord, randNumber = getRandomWord(jsonFile)
    increseCount(randNumber)
    wordIndexList = writePreviousData(randNumber)

    # Send to channel
    myWord = gTTS(text=jsonFile[wordIndexList[-1]]['word'], lang='en', slow=True, lang_check=True)
    myWord.save("myWord.mp3")
    myWord = open(convertToOGG(), "rb")
    try:
        telegram.Bot.sendAudio(auth, SETTING.CHANNEL_ID, audio=myWord, caption=f"<b><i>{jsonFile[len(wordIndexList)]['word']}</i></b>\n--------------\n{jsonFile[len(wordIndexList)]['meaning']}", parse_mode=ParseMode.HTML)
    except telegram.error.BadRequest as e:
        telegram.Bot.sendMessage(auth, SETTING.ADMIN_ID, text=f"Bad Request in Channel :)", parse_mode=ParseMode.HTML)
    except telegram.error.Unauthorized as e:
        telegram.Bot.sendMessage(auth, SETTING.ADMIN_ID, text=f"I am Unauthorized in Channel :)", parse_mode=ParseMode.HTML)
    except Exception as e:
        telegram.Bot.sendMessage(auth, SETTING.ADMIN_ID, text=f"Got Error in Channel :(\n\n{e}", parse_mode=ParseMode.HTML)
    myWord.close()


    # Send message to user about today
    stopDate = date.today()
    for chatId in SETTING.CHAT_IDS:
        try:
            if(sendTime == 0):
                telegram.Bot.sendMessage(auth, chatId, text=f"<b>#Day{(stopDate - startDate).days + 1} &lt;10 AM&gt;\n{date.today().strftime('%d %b %Y')}</b>", parse_mode=ParseMode.HTML)
            elif(sendTime == 1):
                telegram.Bot.sendMessage(auth, chatId, text=f"<b>#Day{(stopDate - startDate).days + 1} &lt;5 PM&gt;\n{date.today().strftime('%d %b %Y')}</b>", parse_mode=ParseMode.HTML)
        except telegram.error.BadRequest as e:
            telegram.Bot.sendMessage(auth, SETTING.ADMIN_ID, text=f"{chatId} I don't know him/her :)", parse_mode=ParseMode.HTML)
        except telegram.error.Unauthorized as e:
            telegram.Bot.sendMessage(auth, SETTING.ADMIN_ID, text=f"{chatId} has blocked me :(", parse_mode=ParseMode.HTML)
        except Exception as e:
            telegram.Bot.sendMessage(auth, SETTING.ADMIN_ID, text=f"got error with {chatId} :(\n\n{e}", parse_mode=ParseMode.HTML)



    # Individual send
    for wordIndex in wordIndexList:
        myWord = gTTS(text=jsonFile[wordIndex]['word'], lang='en', slow=True, lang_check=True)
        myWord.save("myWord.mp3")
        myWord = open(convertToOGG(), "rb")

        for chatId in SETTING.CHAT_IDS:
            try:
                telegram.Bot.sendAudio(auth, chatId, audio=myWord, caption=f"<b><i>{jsonFile[wordIndex]['word']}</i></b>\n--------------\n{jsonFile[wordIndex]['meaning']}", parse_mode=ParseMode.HTML)
            except telegram.error.BadRequest as e:
                telegram.Bot.sendMessage(auth, SETTING.ADMIN_ID, text=f"{chatId} I don't know him/her :)", parse_mode=ParseMode.HTML)
            except telegram.error.Unauthorized as e:
                telegram.Bot.sendMessage(auth, SETTING.ADMIN_ID, text=f"{chatId} has blocked me :(", parse_mode=ParseMode.HTML)
            except Exception as e:
                telegram.Bot.sendMessage(auth, SETTING.ADMIN_ID, text=f"got error with {chatId} :(\n\n{e}", parse_mode=ParseMode.HTML)
        myWord.close()



def main(sendTime):
    try:
        auth = telegram.Bot(token=SETTING.TOKEN)
        with open("data.json", "r") as file:
            jsonFile = json.load(file)
        runBot(auth, jsonFile, sendTime)
    except RecursionError as e:
        # print(e)
        auth = telegram.Bot(token=SETTING.TOKEN)
        runBot(auth, jsonFile)

startDate = date.today()
scheduler = BlockingScheduler()
scheduler.add_job(lambda : main(0), trigger='cron', hour='4', minute='30')
scheduler.add_job(lambda : main(1), trigger='cron', hour='11', minute='30')
scheduler.start()