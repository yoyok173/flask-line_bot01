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

from flask import Flask, request, abort
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
    elif event.message.text == "買う!":
        text = "何を買うんですか？"
    elif event.message.text == "買った！":
        text = "何を買ったんですか？"
    elif event.message.text == "買った!":
        text = "何を買ったんですか？"
    elif "ヘルプ" in event.message.text:
        text = "操作コマンド\n\n買う！\n＝＞何を買うんですか？\n買った！\n＝＞何を買ったんですか？\nおはよう　が含まれる\n＝＞おはようございます！\nそれ以外\n＝＞おうむ返し的なやつ"
    elif "買う！" in event.message.text:
        user_text = event.message.text
        item = user_text.replace('買う！','')
        text = item + " をお買い物リストに入れたよ！"
    elif "買う!" in event.message.text:
        user_text = event.message.text
        item = user_text.replace('買う!','')
        text = item + " をお買い物リストに入れたよ！"
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
        # 今日買うリストはこんな感じですね！元気にいきましょう♪（一覧表示）
    else:
        text = "あなたがおっしゃったことは" + event.message.text + "ですね。"
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text)
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)