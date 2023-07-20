import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from . import db
from .config import *
from .models import URLs
from .tele_post import tg_bot
import os
import requests
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


def get_info(url):
    try:
        result = requests.get('http://46.229.215.118:5001', params={'url': url}).json()['result']
        return result
    except Exception as e:
        print(e)
        return f'error {e}'


def get_data(url):
    try:
        result = requests.get('http://46.229.215.118:5001', params={'url': url}).json()
        return result
    except Exception as e:
        print(e)
        return f'error {e}'


def send_first(channel, url):
    result = get_info(url)
    if result == 'closed':
        _ = URLs.query.filter_by(tg_channel=channel).update({'stopped': 1})
        db.session.commit()
        return
    tg_bot(result, channel, arg='send')


def send():
    res = requests.get('http://159.89.229.47:5000/send')
    print(res.text)


def update():
    res = requests.get('http://159.89.229.47:5000/update')
    print(res.text)
