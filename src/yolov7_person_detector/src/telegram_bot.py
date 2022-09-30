import os
import logging
import threading
from telegram import Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext
)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


class TelegramBot(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.chat_id_filepath = '.config/telegram_chat_id.txt'
        self.token = os.getenv('TELEGRAM_TOKEN', None)
        self.application = None
        self.chat_id = self.load_id()
        self.bot = None
        self.updater = None

    def run(self):
        def recv_msg(update: Update, context: CallbackContext):
            try:
                update.message.reply_text("Hi, SharpAI is running...")
                print(update.message)
            except Exception as e:
                print('Exception when processing received message')
                print(e)

        def cmd_start(update: Update,  context: CallbackContext):
            try:
                self.chat_id = str(update.message['chat']['id'])
                self.save_id(self.chat_id)

                self.send("SharpAI started...")
                print(update.message)
            except Exception as e:
                print(e)
        # await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")

        if self.token != None:
            self.updater = Updater(self.token )
            self.bot = self.updater.bot
            dispatcher = self.updater.dispatcher
            dispatcher.add_handler(CommandHandler("start", cmd_start))
            dispatcher.add_handler(MessageHandler(
                Filters.text & ~Filters.command,
                recv_msg
            ))

            print('starting telegram bot')
            self.send('SharpAI detecter started')
            self.updater.start_polling()

    def send(self,message) -> None:
        try:
            self.chat_id = self.load_id()
            if self.bot != None and self.chat_id != None:
                print(f'sending message {message}')
                self.bot.send_message(chat_id=self.chat_id, text=message)
        except Exception as e:
            print('Exception when sending message')
            print(e)
    def send_image(self, photo_path) -> None:
        try:
            self.chat_id = self.load_id()
            if self.bot != None and self.chat_id != None:
                print(f'sending photo {photo_path}')
                self.bot.send_photo(chat_id=self.chat_id, photo=open(photo_path, 'rb'))
        except Exception as e:
            print('Exception when sending message')
            print(e)
        
    def save_id(self,chat_id):
        with open(self.chat_id_filepath, "w") as f:
            f.write(chat_id)
    def load_id(self):
        if os.path.exists(self.chat_id_filepath):
            with open(self.chat_id_filepath,'r') as f:
                chat_id = f.readline()
                if chat_id == '':
                    return None
                return chat_id
        return None