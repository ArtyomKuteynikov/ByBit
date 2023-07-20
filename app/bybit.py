import requests
import time
import hashlib
import hmac
import uuid
import telebot
import requests
from .config import *

bot = telebot.TeleBot(BOT_TOKEN)

api_key = api_key
secret_key = api_secret
httpClient = requests.Session()
recv_window = str(60000)
url = "https://api.bybit.com"  # Testnet endpoint


def HTTP_Request(endPoint, method, payload, Info):
    global time_stamp
    time_stamp = str(int(time.time() * 10 ** 3))
    signature = genSignature(payload)
    headers = {
        'X-BAPI-API-KEY': api_key,
        'X-BAPI-SIGN': signature,
        'X-BAPI-SIGN-TYPE': '2',
        'X-BAPI-TIMESTAMP': time_stamp,
        'X-BAPI-RECV-WINDOW': recv_window,
        'Content-Type': 'application/json'
    }
    if (method == "POST"):
        response = httpClient.request(method, url + endPoint, headers=headers, data=payload)
    else:
        response = httpClient.request(method, url + endPoint + "?" + payload, headers=headers)
    print(response.text)
    print(Info + " Elapsed Time : " + str(response.elapsed))
    return response.json()


def genSignature(payload):
    param_str = str(time_stamp) + api_key + recv_window + payload
    hash = hmac.new(bytes(secret_key, "utf-8"), param_str.encode("utf-8"), hashlib.sha256)
    signature = hash.hexdigest()
    return signature


def short(symbol, qty):
    endpoint = "/v5/position/set-leverage"
    method = "POST"
    params = '''{"category": "linear","symbol": "''' + str(
        symbol) + '''USDT","buyLeverage": "''' + LEVERAGE + '''","sellLeverage": "''' + LEVERAGE + '''"}'''
    HTTP_Request(endpoint, method, params, "SetL")
    endpoint = "/v5/order/create"
    method = "POST"
    params = '{"category": "linear","symbol": "' + str(
        symbol) + 'USDT","side": "Sell","orderType": "Market","qty": "' + str(
        qty) + '","timeInForce": "GTC","isLeverage": 1}'
    res1 = HTTP_Request(endpoint, method, params, "Short")
    if res1['retMsg'] == 'position idx not match position mode':
        params = '{"category": "linear","positionIdx":2,"symbol": "' + str(
            symbol) + 'USDT","side": "Sell","orderType": "Market","qty": "' + str(
            qty) + '","timeInForce": "GTC","isLeverage": 1}'
        res1 = HTTP_Request(endpoint, method, params, "Close")
    if res1['retMsg'] == "OK":
        # Price
        endpoint = "/spot/v3/public/quote/ticker/price"
        method = "GET"
        params = 'symbol=' + symbol + 'USDT'
        res = HTTP_Request(endpoint, method, params, "Price")
        price = float(res['result']['price'])
        return 'success', qty * price
    return 'error', res1['retMsg']


def close(symbol, qty):
    try:
        endpoint = "/v5/order/create"
        method = "POST"
        params = '{"category": "linear","symbol": "' + str(
            symbol.strip()) + 'USDT","side": "Buy","orderType": "Market","qty": "' + str(
            qty) + '","timeInForce": "GTC","isLeverage": 1}'
        res = HTTP_Request(endpoint, method, params, "Close")
        if res['retMsg'] == 'position idx not match position mode':
            params = '{"category": "linear","positionIdx":2,"symbol": "' + str(
                symbol.strip()) + 'USDT","side": "Buy","orderType": "Market","qty": "' + str(
                qty) + '","timeInForce": "GTC","isLeverage": 1}'
            res = HTTP_Request(endpoint, method, params, "Close")
        if res['retMsg'] == "OK":
            endpoint = "/spot/v3/public/quote/ticker/price"
            method = "GET"
            params = 'symbol=' + symbol.strip() + 'USDT'
            res = HTTP_Request(endpoint, method, params, "Price")
            price = float(res['result']['price'])
            return 'success', qty * price
        return 'error', res['retMsg']
    except Exception as e:
        return 'error', f'error: {e}'


def pnl(symbol, qty):
    endpoint = "/v5/position/list"
    method = "GET"
    params = '''category=linear&symbol=''' + symbol.strip() + '''USDT'''
    res1 = HTTP_Request(endpoint, method, params, "Buy")
    price1, price2 = float(res1["result"]["list"][0]["avgPrice"]), float(res1["result"]["list"][0]["markPrice"])
    if price1 == 0:
        price1 = float(res1["result"]["list"][-1]["avgPrice"])
    if price1 > 0:
        result = f'{round(float(qty) * (price1 - price2), 8)}$({round((price1 - price2) / price1, 8)}%)'
    else:
        result = f'{round(0.0, 8)}$({0.0}%)'
    return result


def send_open(admins, symbol2, qty2):
    for i in admins.split(';'):
        print(i)
        try:
            bot.send_message(i, f'Открыта позиция {symbol2}\nна  объем: {qty2}{symbol2}')
            print('sent', i)
        except Exception as e:
            print(e)


def send_close(admins, symbol1, symbol2, result_1, result_2):
    for i in admins.split(';'):
        print(i)
        try:
            bot.send_message(i,
                             f'Позиции закрыты:\n {symbol1}\nрезультат: {result_1}\n\n{symbol2}\nрезультат: {result_2}')
            print('sent', i)
        except Exception as e:
            print(e)
