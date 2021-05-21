from flask import Flask, jsonify, request, redirect
import sqlite3 as sqlitedb
import os
import logging
import random
from hashlib import sha256
from datetime import datetime

logging.basicConfig(format='[%(asctime)s] %(levelname)s: %(message)s',
                    level=logging.DEBUG)


class DB:
    def __init__(self):
        self.dbfile = os.path.join(os.path.dirname(
            os.path.abspath(__name__)), 'url_shortner.db')

        # Create table if it does not exist
        sql = """CREATE TABLE IF NOT EXISTS URLS (
              URLID VARCHAR(7) NOT NULL PRIMARY KEY
            , FULL_URL VARCHAR(500) NOT NULL
        )"""
        self.run_sql(sql)

    def run_sql(self, sql):
        try:
            logging.debug(sql)
            conn = sqlitedb.connect(self.dbfile)
            cur = conn.cursor()
            cur.execute(sql)
            rows = cur.fetchall()
        except Exception as e:
            logging.error('Error occured :' + str(e))
            rows = []
        finally:
            conn.commit()
            cur.close()
            conn.close()

        return rows

    def check_urlid_exist(self, urlid):
        sql = "SELECT 1 FROM URLS WHERE URLID = '{}'".format(urlid)
        check = self.run_sql(sql)

        return bool(check)

    def save_url(self, urlid, full_url):
        sql = "INSERT INTO URLS VALUES ('{}','{}')".format(urlid, full_url)
        self.run_sql(sql)

        return self.check_urlid_exist(urlid)

    def get_urlid_by_url(self, full_url):
        sql = "SELECT URLID FROM URLS WHERE FULL_URL = '{}'".format(full_url)
        urlid = self.run_sql(sql)

        return urlid[0][0] if urlid else None

    def get_url_by_id(self, urlid):
        sql = "SELECT FULL_URL FROM URLS WHERE URLID = '{}'".format(urlid)
        url = self.run_sql(sql)

        return url[0][0] if url else None


# Flask App
app = Flask(__name__)
HOST = '0.0.0.0'
PORT = '8089'

# Create Database Instance
db = DB()


def generate_uid():
    chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'
    timenow_str = datetime.now().strftime("%Y%m%d%H%M%S%Z").encode()
    timenow_sha = sha256(timenow_str).hexdigest()

    first4 = random.sample(chars, 4)
    last3 = random.sample(timenow_sha, 3)

    return "".join(first4 + last3)


@app.route('/')
def index():
    return jsonify("{'message': 'This is URL Shortening App. Go to /short?url=<full_url>'}"), 200


@app.route('/short', methods=['GET'])
def short():
    full_url = request.args.get('url')

    if full_url is not None and full_url.strip() != '':

        # Check if Full URL already exist in Database
        urlid = db.get_urlid_by_url(full_url)
        if urlid:
            return jsonify('{{ urlid: {}, link: {}:{}/{} }}'.format(urlid, HOST, PORT, urlid))
        else:
            new_urlid = generate_uid()
            while db.check_urlid_exist(new_urlid):
                new_urlid = generate_uid()
            else:
                if db.save_url(new_urlid, full_url):
                    return jsonify('{{ urlid: {}, link: {}:{}/{} }}'.format(new_urlid, HOST, PORT, new_urlid))
                else:
                    return jsonify('{message: Unable to save URL}')

    else:
        return jsonify('{message: Invalid Input URL}')


@app.route('/<urlid>', methods=['GET'])
def redirect_link(urlid):
    url = db.get_url_by_id(urlid)
    if url:
        if not url.startswith('http'):
            url = 'http://' + url
        return redirect(url)

    else:
        return jsonify('{message: Invalid Short URL}'), 404


if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=True)
