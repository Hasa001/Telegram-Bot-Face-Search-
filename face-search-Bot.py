import telegram
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

from dotenv import load_dotenv
import os
import time
import requests
# import urllib.request

load_dotenv()
Token = os.getenv("TOKEN")
ApiToken=os.getenv("APITOKEN")

TESTING_MODE = True
photo_expected = False
def search_by_face(image_file):
    if TESTING_MODE:
        print('****** TESTING MODE search, results are inacurate, and queue wait is long, but credits are NOT deducted ******')

    site='https://facecheck.id'
    headers = {'accept': 'application/json', 'Authorization': ApiToken}
    files = {'images': open(image_file, 'rb'), 'id_search': None}
    response = requests.post(site+'/api/upload_pic', headers=headers, files=files).json()

    if response['error']:
        return f"{response['error']} ({response['code']})", None

    id_search = response['id_search']
    print(response['message'] + ' id_search='+id_search)
    json_data = {'id_search': id_search, 'with_progress': True, 'status_only': False, 'demo': TESTING_MODE}

    while True:
        response = requests.post(site+'/api/search', headers=headers, json=json_data).json()
        if response['error']:
            return f"{response['error']} ({response['code']})", None
        if response['output']:
            return None, response['output']['items']
        print(f'{response["message"]} progress: {response["progress"]}%')
        time.sleep(1)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

  welcome_message = f"""
<b>Hi there!  I'm your friendly face search bot. ️✨

Use the `/photo` command to send me an image of the person you're looking for, and I'll search for similar faces online.

Here's a quick guide to using me:

`/start`: Get started or reset the conversation.
`/photo`: Send me an image to find similar faces.</b>
"""

  await context.bot.send_sticker(chat_id=update.effective_chat.id, sticker="hi.tgs")
  await context.bot.send_message(chat_id=update.effective_chat.id, text=welcome_message, parse_mode="HTML")
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global photo_expected

    if update.message.text == '/photo' or update.message.text == 'Find another photo':
        photo_expected = True

    if photo_expected:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="<b>Please send me an image!</b>",parse_mode="HTML")
        await context.bot.send_sticker(chat_id=update.effective_chat.id, sticker="detective.tgs")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="<b>Hi! I don't understand. Use /photo to send me an image!*</b>",parse_mode="HTML")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global photo_expected

    if not photo_expected:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="<b>Please use /photo first to send me an image!</b>",parse_mode="HTML")
        return

    # Send a loading message before starting the search
    await context.bot.send_sticker(chat_id=update.effective_chat.id, sticker="waiting.tgs")
    loading_message = await context.bot.send_message(chat_id=update.effective_chat.id, text="<b>Searching for similar images......\nPlease wait!</b>",parse_mode="HTML")
    
    file_id = update.message.photo[-1].file_id
    new_file = await application.bot.get_file(file_id)
    local_file_path = new_file.file_path.split('photos/')[1]
    await new_file.download_to_drive(local_file_path)

    error, urls_images = search_by_face(local_file_path)
    count=0
    if urls_images:
        for i in urls_images:
          if i['score']>60:
            count=count+1
            url = i['url']
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"<b>Links</b>\n {url}",parse_mode="HTML")
    else:
        await loading_message.edit_text(text=f"Error: {error}")

    if count>0:
            await loading_message.edit_text(text="*_Here are your links for similar images:_*",parse_mode="MarkdownV2")
            await context.bot.send_sticker(chat_id=update.effective_chat.id, sticker="done.tgs")
    else:
            await loading_message.edit_text(text="<b><i>Sorry! no image is found</i></b>",parse_mode="HTML")
            await context.bot.send_sticker(chat_id=update.effective_chat.id, sticker="sad.tgs")

    # Delete the saved image and reset flag after processing
    os.remove(local_file_path)
    photo_expected = False
    keyboard = [[telegram.KeyboardButton('Find another photo')]]
    reply_markup = telegram.ReplyKeyboardMarkup(keyboard,one_time_keyboard=True,resize_keyboard=True)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"<b>To Continue click the button</b>",parse_mode="HTML",reply_markup=reply_markup)

if __name__ == '__main__':
    application = ApplicationBuilder().token(Token).build()

    start_handler = CommandHandler('start', start)
    text_handler = MessageHandler(filters.TEXT, handle_text)
    photo_handler = MessageHandler(filters.PHOTO, handle_photo)


    application.add_handler(start_handler)
    application.add_handler(text_handler)
    application.add_handler(photo_handler)


    application.run_polling()

