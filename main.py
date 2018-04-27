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

## ### 一旦データベースを作り直す
##   from main import db
##   db.drop_all()
##   db.create_all()

# モデル
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.String(200), unique=True)

    def __init__(self, source_id):
        self.source_id = source_id

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    bought = db.Column(db.Boolean, default=False)

    def __init__(self, name, user_id, bought):
        self.name = name
        self.user_id = user_id
        self.bought = bought

    def __repr__(self):
        return '<Item %r>' % self.bought

## ### DB直接入力
##   url = ItemUrl('hoge','https://hoeghoge')
##   db.session.add(url)
##   db.session.commit()

class ItemUrl(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    url = db.Column(db.String(200))

    def __init__(self, name, url):
        self.name = name
        self.url = url


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
    if event.message.text == "買う！" or event.message.text == "買う!":
        text = "何を買うんですか？"
    elif event.message.text == "買った！" or event.message.text == "買った!":
        text = "何を買ったんですか？"
    elif event.message.text == "私のID":
        text = str(event.source.user_id)
    elif "ヘルプ" in event.message.text:
        text = "操作コマンド\n\n〇〇買う！\n＝＞〇〇をリストにいれるよ♪\n〇〇買った！\n＝＞〇〇をリストから外すよ♪\nリスト！\n＝＞リストを表示するよ\nおすすめ！\n＝＞只今、準備中・・・。\nhttps://amzn.to/2F74c9L"
    elif "買う！" in event.message.text:
        user_text = event.message.text
        source_id = str(event.source.user_id)
        item = user_text.replace('買う！','')
        text = item + " をお買い物リストに入れたよ！"
        # ここで、DBにデータをいれる

        if not User.query.filter_by(source_id=source_id).first():
            user = User(source_id=source_id)
            db.session.add(user)
            db.session.commit()

        user_id= User.query.filter_by(source_id=source_id).first().id
        item = Item(name=item, user_id=user_id, bought=False)
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
        item = Item(name=item, user_id=user_id, bought=False)
        db.session.add(item)
        db.session.commit()

    elif "買った！" in event.message.text:
        user_text = event.message.text
        source_id = str(event.source.user_id)
        item = user_text.replace('買った！', '')
        text = item + " をお買い物リストから除いたよ！"

        if not User.query.filter_by(source_id=source_id).first():
            user = User(source_id=source_id)
            db.session.add(user)
            db.session.commit()
            # ユーザーが存在していない場合はユーザー登録をお知らせする
            text = "ユーザー登録をしたよ！"

        if User.query.filter_by(source_id=source_id).first():
            user_id= User.query.filter_by(source_id=source_id).first().id
            # itemと一致するこの人が持っているitemのboughtカラムをTrueに変更
            # update
            item = Item.query.filter(Item.user_id == user_id ).filter(Item.bought == False).filter(Item.name == item).first()
            item.bought = True
            db.session.add(item)
            db.session.commit()

    elif "買った!" in event.message.text:
        user_text = event.message.text
        source_id = str(event.source.user_id)
        item = user_text.replace('買った!', '')
        text = item + " をお買い物リストから除いたよ！"

        if not User.query.filter_by(source_id=source_id).first():
            user = User(source_id=source_id)
            db.session.add(user)
            db.session.commit()
            # ユーザーが存在していない場合はユーザー登録をお知らせする
            text = "ユーザー登録をしたよ！"

        if User.query.filter_by(source_id=source_id).first():
            user_id= User.query.filter_by(source_id=source_id).first().id
            # itemと一致するこの人が持っているitemのboughtカラムをTrueに変更
            # update
            item = Item.query.filter(Item.user_id == user_id).filter(Item.bought == False).filter(Item.name == item).first()
            item.bought = True
            db.session.add(item)
            db.session.commit()

    elif "おはよ" in event.message.text:
        text = "おはようございます！"

    elif event.message.text == "リスト" or event.message.text == "りすと":
        text = "現在のお買い物リストです。"
        source_id = str(event.source.user_id)
        user_id = User.query.filter_by(source_id=source_id).first().id
        items = Item.query.filter_by(user_id=user_id).filter(Item.bought == False).all()
        a = ""
        for item in items:
            a = a + item.name + '\n'

        text = text + '\n\n' + a


    else:
        text = "あなたがおっしゃったことは" + event.message.text + "ですね。"
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text)
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)