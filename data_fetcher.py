import requests
from PIL import Image
from io import BytesIO
from datetime import timedelta, timezone

# URL定義
BASE_MAP_URL = "http://www.kmoni.bosai.go.jp/data/map_img/CommonImg/base_map_w.gif"
JMA_EARTHQUAKE_URL = "https://www.jma.go.jp/bosai/quake/data/list.json"
P2P_TSUNAMI_URL = "https://api.p2pquake.net/v2/history?codes=552&limit=1"

# 日本時間のタイムゾーン
JST = timezone(timedelta(hours=+9), 'JST')

def get_base_map():
    """背景地図を取得する"""
    try:
        response = requests.get(BASE_MAP_URL, timeout=5)
        response.raise_for_status()
        return Image.open(BytesIO(response.content)).convert("RGBA")
    except Exception as e:
        print(f"背景地図取得エラー: {e}")
        return None

def get_realtime_jma_image(date_str, time_str):
    """指定時刻のリアルタイム震度画像を取得する"""
    img_url = f"http://www.kmoni.bosai.go.jp/data/map_img/RealTimeImg/jma_s/{date_str}/{time_str}.jma_s.gif"
    try:
        res = requests.get(img_url, timeout=5)
        if res.status_code == 200:
            return Image.open(BytesIO(res.content)).convert("RGBA"), 200
        return None, res.status_code
    except requests.exceptions.RequestException:
        return None, None

def fetch_earthquake_data():
    """最新の地震情報を取得する"""
    try:
        res = requests.get(JMA_EARTHQUAKE_URL, timeout=5)
        if res.status_code == 200:
            return res.json()
    except requests.exceptions.RequestException:
        pass
    return None

def fetch_tsunami_data():
    """最新の津波情報を取得する"""
    try:
        res = requests.get(P2P_TSUNAMI_URL, timeout=5)
        if res.status_code == 200:
            return res.json()
    except requests.exceptions.RequestException:
        pass
    return None