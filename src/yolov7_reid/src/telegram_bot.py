import os
import logging
import threading
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")

class TelegramBot(threading.Thread):
    def __init__(self) -> None:
        self.chat_id = self.load_id()
        self.chat_id_filepath = 'telegram_token.txt'
        self.token = os.getenv('TELEGRAM_TOKEN', None)
        self.application = None

        if self.token != None:
            self.application = ApplicationBuilder().token(self.token).build()

    def run(self) -> None:
        if self.application != None:
            self.application.run_polling()
    def send(self,message) -> None:
        if self.application != None and self.chat_id != None:
            print(f'sending message {message}')
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