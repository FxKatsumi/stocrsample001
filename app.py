import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import time
import streamlit as st
import sys

# フォント
# Windows
font_name_win = "./meiryo.ttc" # メイリョウ
# Mac
font_name_mac = "ヒラギノ丸ゴ ProN W4.ttc"
# Linux
# font_name_lnx = "DejaVuSerif.ttf"
# font_name_lnx = "DejaVuSerif-Bold.ttf"
# font_name_lnx = "DejaVuSansMono.ttf"
# font_name_lnx = "DejaVuSansMono-Bold.ttf"
# font_name_lnx = "DejaVuSans.ttf"
# font_name_lnx = "DejaVuSans-Bold.ttf"
font_name_lnx = "Noto Sans CJK JP"
# font_name_lnx = ""
# font_name_lnx = ""
# font_name_lnx = ""
# font_name_lnx = ""

# フォント
if sys.platform == "win32": # Windows
    font_name = font_name_win
if sys.platform == "darwin": # Mac
    font_name = font_name_mac
if sys.platform in ("linux", "linux2"): # Linux
    font_name = font_name_lnx

# ファイルをアップロードするためのStreamlitのウィジェットを表示
uploaded_file = st.file_uploader("名刺の画像ファイルをアップロードしてください", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # 画像ファイルを読み込む
    im = Image.open(uploaded_file)
    imFilePath = BytesIO(uploaded_file.getvalue())

    # Azure Computer Vision API の endpoint を指定する
    endpoint = "https://computervisiontestm01.cognitiveservices.azure.com/"
    text_recognition_url = endpoint + "vision/v3.2/read/analyze"

    # ヘッダー情報を指定する
    headers = {
        'Ocp-Apim-Subscription-Key': st.secrets.azure_settings.azure_subscription_key,
        'Content-Type': 'application/octet-stream'
    }
    params = {
        'language': 'ja',
        'model-version': 'latest'
    }

    # 指定した画像の read メソッドを呼び出します。これによって operation ID が返され、画像の内容を読み取る非同期プロセスが開始されます
    response = requests.post(text_recognition_url, headers=headers, params=params, json=None, data=imFilePath)
    response.raise_for_status()

    # レスポンスから operation location（末尾にIDが付いたURL）を取得する
    operation_url = response.headers["Operation-Location"]
    analysis = {}
    poll = True

    # read の呼び出しから返された operation location ID を取得し、操作の結果をサービスに照会します。
    # 次のコードは、結果が返されるまで 1 秒間隔で操作をチェックします
    while poll:
        response_final = requests.get(operation_url, headers=headers)
        analysis = response_final.json()

        if "analyzeResult" in analysis:
            poll = False
        if "status" in analysis and analysis['status'] == 'failed':
            poll = False

        if poll:
            time.sleep(1)

    # 画像イメージ読み込み
    draw = ImageDraw.Draw(im)
    fnt = ImageFont.truetype(font_name, 15)

    if "analyzeResult" in analysis:  # 成功した場合
        # 行ごとにデータを格納する
        lines = [(line["boundingBox"], line["text"], line["words"])
                 for line in analysis["analyzeResult"]["readResults"][0]["lines"]]

        # 行レベル
        for line in lines:
            boundingBox = line[0]
            text = line[1]
            words = line[2]

            # 文字レベル
            for word in words:
                try:
                    wp = word["boundingBox"]
                    wtext = word["text"]
                    wconfidence = word['confidence']

                    # 矩形を描画
                    draw.rectangle([wp[0], wp[1], wp[4], wp[5]], fill=None, outline=(0, 255, 0), width=1)
                    # テキストを描画
                    draw.text((wp[6] + 5, wp[7] - 5), wtext, font=fnt, fill=(0, 0, 255))
                except:
                    pass

    # 画像を表示
    st.image(im, caption='OCR 結果の画像', use_column_width=True)
