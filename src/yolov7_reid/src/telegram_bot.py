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
        self.chat_id_filepath = 'telegram_token.txt'
        self.token = os.getenv('TELEGRAM_TOKEN', None)
        self.application = None
        self.chat_id = self.load_id()

    def run(self):
        def recv_msg(update: Update, context: CallbackContext):
            update.message.reply_text("Oooopa")
            print(update.message)

            # context.bot.send_message(chat_id=update.effective_chat.id, text=f"Your chat_id is {update.effective_chat.id}")
        def cmd_start(update: Update,  context: CallbackContext):
            print(update.message)
            try:
                chat_id = update.message['chat']['id']
                self.save_id(chat_id)
            except Exception as e:
                print(e)
        # await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")

        if self.token != None:
            updater = Updater(self.token )
            dispatcher = updater.dispatcher

            dispatcher.add_handler(CommandHandler("start", cmd_start))

            dispatcher.add_handler(MessageHandler(
                Filters.text & ~Filters.command,
                recv_msg
            ))

            print('starting telegram bot')
            updater.start_polling()

    def send(self,message) -> None:
        if self.application != None and self.chat_id != None:
            print(f'sending message {message}')
            self.application.bot.send_message(chat_id=self.chat_id, text=message)
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