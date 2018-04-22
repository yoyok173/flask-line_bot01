# -*- coding: utf-8 -*-

#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

import os
import sys
from argparse import ArgumentParser

from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy

# linebot
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
db = SQLAlchemy(app)

# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)


# モデル
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.String(200), unique=True)

    def __init__(self, source_id):
        self.source_id = source_id

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    user_id =db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, name, user_id):
        self.name = name
        self.user_id = user_id

    # アイテムを購入したかどうかを判定する真偽値が必要
    # 同時に修正できるように設定しておく必要がある
    # リストから削除する。を伝えるとDBからデータが削除される


# webhook
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def message_text(event):
    if event.message.text == "買う！":
        text = "何を買うんですか？"
    elif event.message.text == "私のID":
        text = str(event.source.user_id)
    elif event.message.text == "買う!":
        text = "何を買うんですか？"
    elif event.message.text == "買った！" or event.message.text = "買った!":
        text = "何を買ったんですか？"
        '''
    elif event.message.text == "買った!":
        text = "何を買ったんですか？"
        '''
    elif "ヘルプ" in event.message.text:
        text = "操作コマンド\n\n買う！\n＝＞何を買うんですか？\n買った！\n＝＞何を買ったんですか？\nおはよう　が含まれる\n＝＞おはようございます！\nそれ以外\n＝＞おうむ返し的なやつ"
    elif "買う！" in event.message.text:
        user_text = event.message.text
        source_id = str(event.source.user_id)
        item = user_text.replace('買う！','')
        text = item + " をお買い物リストに入れたよ！"
        # ここで、DBにデータをいれる
        #
        if not User.query.filter_by(source_id=source_id).first():
            user = User(source_id=source_id)
            db.session.add(user)
            db.session.commit()

        user_id= User.query.filter_by(source_id=source_id).first().id
        item = Item(name=item, user_id=user_id)
        db.session.add(item)
        db.session.commit()

    elif "買う!" in event.message.text:
        user_text = event.message.text
        source_id = str(event.source.user_id)
        item = user_text.replace('買う!','')
        text = item + " をお買い物リストに入れたよ！"
        # ここで、DBにデータを入れる
        #
        # データ型
        # 
        if not User.query.filter_by(source_id=source_id).first():
            user = User(source_id=source_id)
            db.session.add(user)
            db.session.commit()

        user_id= User.query.filter_by(source_id=source_id).first().id
        item = Item(name=item, user_id=user_id)
        db.session.add(item)
        db.session.commit()

    elif "買った！" in event.message.text:
        user_text = event.message.text
        item = user_text.replace('買った！', '')
        text = item + " をお買い物リストから除いたよ！"
    elif "買った!" in event.message.text:
        user_text = event.message.text
        item = user_text.replace('買った!', '')
        text = item + " をお買い物リストから除いたよ！"
    elif "おはよう" in event.message.text:
        text = "おはようございます！"

    elif event.message.text == "リスト":
        text = "現在のお買い物リストです。"
        source_id = str(event.source.user_id)
        user_id = User.query.filter_by(source_id=source_id).first().id
        items = Item.query.filter_by(user_id=user_id).all()
        a = ""
        for item in items:
            a = a + item.name + '\n'

        text = text + '\n\n' + a


    else:
        text = "あなたがおっしゃったことは" + event.message.text + "ですね。"

    # lineBOT 登録

    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text)
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)