from flask import Blueprint, render_template, redirect, request, flash, url_for
from flask_login import login_required, current_user
from .parser import get_info, send, send_first, get_data
import os
from . import db
import json
from .tele_post import tg_bot
from .models import User, URLs
from werkzeug.security import generate_password_hash
from .bybit import close, short, pnl, send_close, send_open

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

api = Blueprint('api', __name__)


@api.route('/send', methods=["POST", "GET"])
def send():
    pools = URLs.query.filter_by(stopped=0).all()
    for i in pools:
        channel = i.tg_channel
        url = i.url
        try:
            result = get_info(url)
            print(result)
            if result == 'closed':
                _ = URLs.query.filter_by(tg_channel=channel).update({'stopped': 1})
                db.session.commit()
                return
            tg_bot(result, channel, arg='send')
            _ = URLs.query.filter_by(tg_channel=channel).update({'working': 1})
            db.session.commit()
        except Exception as e:
            _ = URLs.query.filter_by(tg_channel=channel).update({'working': 0})
            return {'ok': str(e), 'result': result}
        db.session.commit()
    return {'ok': 'True'}


@api.route('/update', methods=["POST", "GET"])
def update():
    pools = URLs.query.filter_by(stopped=0).all()
    print(pools)
    for i in pools:
        try:
            channel = i.tg_channel
            url = i.url
            result1 = get_info(url)
            print(result1)
            try:
                tg_bot(result1, channel, arg='edit')
            except:
                pass
            result = get_data(url)['data']
            if result1 == 'closed':
                _ = URLs.query.filter_by(tg_channel=channel).update({'stopped': 1})
                db.session.commit()
                symbols = URLs.query.filter_by(id=i.id).first().tickers.split('/')
                amount_1 = URLs.query.filter_by(id=i.id).first().amount_1
                amount_2 = URLs.query.filter_by(id=i.id).first().amount_2
                result_1 = pnl(symbols[0], amount_1)
                result_2 = pnl(symbols[1], amount_2)
                close1 = close(symbols[0], amount_1)
                close2 = close(symbols[1], amount_2)
                send_close(URLs.query.filter_by(id=i.id).first().admins, symbols[0], symbols[1], result_1, result_2)
                _ = URLs.query.filter_by(id=i.id).update({'amount_1': 0, 'amount_2': 0, 'result_1': result_1, 'result_2': result_2})
                return
            print(result)
            symbol1, symbol2, qty1, qty2 = result[0].split('/')[0].strip(), result[0].split('/')[1].strip(), float(result[1]), float(result[2])
            print(symbol1, symbol2, qty1, qty2)
            amount_1 = URLs.query.filter_by(id=i.id).first().amount_1
            amount_2 = URLs.query.filter_by(id=i.id).first().amount_2
            if (qty1 == 0 or qty2 == 0) and (amount_1 != 0 and amount_2 != 0):
                result_1 = pnl(symbol1, amount_1)
                result_2 = pnl(symbol2, amount_2)
                close1 = close(symbol1, amount_1)
                close2 = close(symbol2, amount_2)
                send_close(URLs.query.filter_by(id=i.id).first().admins, symbol1, symbol2, result_1, result_2)
                if qty1 == 0:
                    print(1)
                    short2 = short(symbol2, qty2)
                    send_open(URLs.query.filter_by(id=i.id).first().admins, symbol2, qty2)
                    _ = URLs.query.filter_by(id=i.id).update({'amount_1': 0, 'amount_2': qty2, 'result_1': result_1})
                    db.session.commit()
                elif qty2 == 0:
                    print(2)
                    short1 = short(symbol1, qty1)
                    send_open(URLs.query.filter_by(id=i.id).first().admins, symbol1, qty1)
                    _ = URLs.query.filter_by(id=i.id).update({'amount_2': 0, 'amount_1': qty2, 'result_2': result_2})
                    db.session.commit()
            _ = URLs.query.filter_by(tg_channel=channel).update({'working': 1})
            db.session.commit()
        except Exception as e:
            print(e)
            _ = URLs.query.filter_by(tg_channel=channel).update({'working': 0})
        db.session.commit()
    return {'ok': True}
