# main.py
import datetime

import requests
from flask import Blueprint, render_template, redirect, request, flash, url_for
from flask_login import login_required, current_user
from .parser import get_info, send, send_first
import os
from . import db
import json
from .models import User, URLs
from werkzeug.security import generate_password_hash
from .bybit import short, close, pnl, send_open, send_close, HTTP_Request

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

main = Blueprint('main', __name__)


@main.route('/', methods=["POST", "GET"])
@login_required
def index():
    pools = URLs.query.filter_by().all()
    pnls = dict()
    for i in pools:
        if i.amount_1 and i.amount_2:
            res1 = pnl(i.tickers.split("/")[0].strip(), i.amount_1)
            res2 = pnl(i.tickers.split("/")[1].strip(), i.amount_2)
            pnls.update({
                i.id: f'{i.tickers.split("/")[0].strip()}: {res1}<br>{i.tickers.split("/")[1].strip()}: {res2}'})
        elif i.amount_1:
            res1 = pnl(i.tickers.split("/")[0].strip(), i.amount_1)
            pnls.update(
                {i.id: f'{i.tickers.split("/")[0].strip()}: {res1}<br>{i.tickers.split("/")[1].strip()}: {i.result_2}'})
        elif i.amount_2:
            res2 = pnl(i.tickers.split("/")[1].strip(), i.amount_1)
            pnls.update({
                i.id: f'{i.tickers.split("/")[0].strip()}: {i.result_1}<br>{i.tickers.split("/")[1].strip()}: {res2}'})
        else:
            if i.amount_1 == 0:
                pnls.update({
                    i.id: f'{i.tickers.split("/")[0].strip()}: {i.result_1}<br>{i.tickers.split("/")[1].strip()}: {i.result_2}'})
    return render_template('index.html', pools=pools, pnls=pnls)


@main.route('/profile/<action>', methods=["GET", "POST"])
@login_required
def profile(action):
    if action == "view":
        return render_template('profile.html', name=current_user.name)
    elif action == "edit" and request.method != 'POST':
        return render_template('edit.html', name=current_user.name)
    else:
        name = request.form.get('name')
        login = request.form.get('login')
        password = request.form.get('password')
        _ = User.query.filter_by(id=current_user.id).update(
            {'name': name, 'email': login, 'password': generate_password_hash(password, method='sha256')})
        db.session.commit()
        return redirect(url_for('main.profile', action="view"))


@main.route('/add_pool', methods=["POST", "GET"])
@login_required
def add_pool():
    url = request.form.get('url')
    channel = request.form.get('channel')
    admins = request.form.get('admins')
    if URLs.query.filter_by(tg_channel=channel).first():
        flash(f'Для канала уже есть ссылка')
        return redirect('/')
    try:
        try:
            result = get_info(url)
            if result == 'closed':
                flash(result)
                redirect('/')
        except Exception as e:
            flash(f'Ошибка! Ссылка не корректна')
            return redirect('/')
        new_pool = URLs(url=url, tg_channel=channel, admins=admins)
        db.session.add(new_pool)
        db.session.commit()
        send_first(channel, url)
        flash('Успех! Ссылка успешно добавлена')
        return redirect('/')
    except Exception as e:
        print(e)
        flash(f'Ошибка! Не верный ID канала, попробуйте добавить бота в канал')
        return redirect('/')


@main.route('/stop_pool/<id>', methods=["POST", "GET"])
@login_required
def stop_pool(id):
    _ = URLs.query.filter_by(id=id).update({'stopped': 1})
    db.session.commit()
    try:
        if URLs.query.filter_by(id=id).first().amount_1 or URLs.query.filter_by(id=id).first().amount_2:
            symbols = URLs.query.filter_by(id=id).first().tickers.split('/')
            amount_1 = URLs.query.filter_by(id=id).first().amount_1
            amount_2 = URLs.query.filter_by(id=id).first().amount_2
            result_1 = pnl(symbols[0], amount_1)
            result_2 = pnl(symbols[1], amount_2)
            close1 = close(symbols[0], amount_1)
            close2 = close(symbols[1], amount_2)
            send_close(URLs.query.filter_by(id=id).first().admins, symbols[0], symbols[1], result_1, result_2)
            _ = URLs.query.filter_by(id=id).update(
                {'amount_1': None, 'amount_2': None, 'result_1': result_1, 'result_2': result_2, 'tickers': None})
            db.session.commit()
    except:
        pass
    return redirect('/')


@main.route('/start_pool/<id>', methods=["POST", "GET"])
@login_required
def start_pool(id):
    try:
        _ = URLs.query.filter_by(id=id).update({'stopped': 0})
        pool = URLs.query.filter_by(id=id).first()
        send_first(pool.tg_channel, pool.url)
        db.session.commit()
        return redirect('/')
    except Exception as e:
        flash(f'Ошибка! {str(e)}')
        return redirect('/')


@main.route('/edit_pool/<id>', methods=["POST", "GET"])
@login_required
def edit_pool(id):
    url = request.form.get('url')
    channel = request.form.get('channel')
    admins = request.form.get('admins')
    try:
        if url != URLs.query.filter_by(id=id).first().url:
            try:
                result = get_info(url)
                if result == 'closed':
                    flash(result)
                    redirect('/')
                send_first(channel, url)
            except Exception as e:
                print(e)
                flash(f'Ошибка! Ссылка или id канала не корректны')
                return redirect('/')
        if url != URLs.query.filter_by(id=id).first().url and URLs.query.filter_by(
                id=id).first().amount_1 and URLs.query.filter_by(id=id).first().amount_2:
            symbols = URLs.query.filter_by(id=id).first().tickers.split('/')
            amount_1 = URLs.query.filter_by(id=id).first().amount_1
            amount_2 = URLs.query.filter_by(id=id).first().amount_2
            result_1 = pnl(symbols[0], amount_1)
            print(1)
            result_2 = pnl(symbols[1], amount_2)
            print(2)
            close1 = close(symbols[0], amount_1)
            print(3)
            close2 = close(symbols[1], amount_2)
            print(4)
            send_close(URLs.query.filter_by(id=id).first().admins, symbols[0], symbols[1], result_1, result_2)
            _ = URLs.query.filter_by(id=id).update(
                {'url': url, 'tg_channel': channel, 'working': 1, 'stopped': 0, 'tickers': None, 'result_1': None,
                 'result_2': None, 'amount_1': None, 'amount_2': None, 'admins': admins})
        elif url != URLs.query.filter_by(id=id).first().url:
            _ = URLs.query.filter_by(id=id).update(
                {'url': url, 'tg_channel': channel, 'working': 1, 'stopped': 0, 'tickers': None, 'result_1': None,
                 'result_2': None, 'amount_1': None, 'amount_2': None, 'admins': admins})
        else:
            _ = URLs.query.filter_by(id=id).update(
                {'tg_channel': channel, 'working': 1, 'stopped': 0, 'admins': admins})
        db.session.commit()
        flash('Успех! Ссылка успешно добавлена')
        return redirect('/')
    except Exception as e:
        flash(f'Ошибка! Не верный ID канала, попробуйте добавить бота в канал{e}')
        return redirect('/')


@main.route('/delete_pool/<id>', methods=["POST", "GET"])
@login_required
def delete_pool(id):
    _ = URLs.query.filter_by(id=id).delete()
    db.session.commit()
    return redirect('/')


@main.route('/first_short/<id>', methods=["POST", "GET"])
@login_required
def first_short(id):
    try:
        result = requests.get('http://46.229.215.118:5001/',
                              params={'url': URLs.query.filter_by(id=id).first().url}).json()
        if result == 'closed':
            flash(result)
            redirect('/')
        res1 = short(result['data'][0].split('/')[0].strip(), float(result['data'][1]))
        send_open(URLs.query.filter_by(id=id).first().admins, result['data'][0].split('/')[0].strip(),
                  float(result['data'][1]))
        print(res1)
        if res1[0] != 'error':
            res2 = short(result['data'][0].split('/')[1].strip(), float(result['data'][2]))
            send_open(URLs.query.filter_by(id=id).first().admins, result['data'][0].split('/')[1].strip(),
                      float(result['data'][2]))
            print(res2)
            if res2[0] != 'error':
                print('updatind')
                _ = URLs.query.filter_by(id=id).update(
                    {'tickers': result['data'][0], 'amount_1': result['data'][1], 'amount_2': result['data'][2]})
                db.session.commit()
            else:
                close(result['data'][0].split('/')[0].strip(), float(result['data'][1]))
                send_close(URLs.query.filter_by(id=id).first().admins, result['data'][0].split('/')[0].strip(),
                           result['data'][0].split('/')[1].strip(), float(result['data'][1]), float(result['data'][2]))
                flash(res2[1])
        else:
            flash(res1[1])
        return redirect('/')
    except Exception as e:
        flash(str(e))
        redirect('/')


@main.route('/balance', methods=["POST", "GET"])
@login_required
def balance():
    endpoint = "/v5/account/wallet-balance"
    method = "GET"
    params = '''accountType=CONTRACT'''
    try:
        coins = HTTP_Request(endpoint, method, params, "Buy")['result']['list'][0]['coin']
        return render_template('balance.html', coins=coins)
    except:
        flash('API ERROR')
        return render_template('balance.html')


@main.route('/positions', methods=["POST", "GET"])
@login_required
def positions():
    endpoint = "/v5/position/list"
    method = "GET"
    try:
        positions = []
        for i in URLs.query.filter_by().all():
            if i.tickers:
                for j in i.tickers.split('/'):
                    params = '''category=linear&symbol=''' + j.strip() + '''USDT'''
                    res1 = HTTP_Request(endpoint, method, params, "Buy")
                    temp = dict()
                    temp.update({'symbol': res1['result']['list'][0]['symbol']})
                    if len(res1['result']['list']) > 1:
                        temp.update({'side_buy': str('+' if res1['result']['list'][0]['side'] == 'Buy' else '-') + str(
                            res1['result']['list'][0]['size'] + f"({res1['result']['list'][0]['unrealisedPnl']}$)"),
                                     'side_both': str(
                                         res1['result']['list'][1][
                                             'size']),
                                     'date': datetime.datetime.fromtimestamp(int(res1['result']['list'][1]['updatedTime'])//1000+3600*3).strftime('%d-%m-%Y %H:%M'),
                                     'pnl': f"{res1['result']['list'][1]['unrealisedPnl']}$",
                                     'side': str('Buy' if res1['result']['list'][1]['side'] == 'Buy' else 'Sell')})
                    else:
                        print(res1['result']['list'][0]['size'])
                        temp.update({'side_both': str(
                            res1['result']['list'][0]['size']),
                                     'date': datetime.datetime.fromtimestamp(int(res1['result']['list'][0]['updatedTime'])//1000+3600*3).strftime('%d-%m-%Y %H:%M'),
                                     'pnl': f"{res1['result']['list'][0]['unrealisedPnl']}$",
                            'side': str('Buy' if res1['result']['list'][0]['side'] == 'Buy' else 'Sell')})
                    positions.append(temp)
        return render_template('positions.html', positions=positions)
    except Exception as e:
        print(e)
        flash('API ERROR')
        return render_template('positions.html')
