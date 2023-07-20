import json
import sys
import telebot  # pip install pyTelegramBotAPI
import os
from . import db
from .models import URLs
from .config import *
from datetime import datetime
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

tb = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML')  # HTML or MARKDOWN
print(__location__)


def tg_bot(text, channel, arg='send'):
    if arg == 'send':
        message = tb.send_message(channel, text)
        _ = URLs.query.filter_by(tg_channel=channel).update({'last_message_id': message.message_id})
        db.session.commit()

    if arg == 'edit':
        message = URLs.query.filter_by(tg_channel=channel).first().last_message_id
        try:
            tb.edit_message_text(chat_id=channel, message_id=message, text=text)
        except Exception as e:
            print('Error: ' + str(e))
