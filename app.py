import streamlit as st
import time
from datetime import datetime, timedelta
from PIL import Image
from data_fetcher import get_base_map, get_realtime_jma_image, fetch_earthquake_data, fetch_tsunami_data, JST

# ページ設定
st.set_page_config(page_title="リアルタイム強震モニタ", layout="wide")
st.title("強震モニタ＆総合防災情報")

# 背景地図のキャッシュ読み込み
@st.cache_data
def load_base_map():
    return get_base_map()

base_map = load_base_map()
if not base_map:
    st.error("背景地図の取得に失敗しました。")
    st.stop()

# UIの構築
is_running = st.checkbox("リアルタイム更新を有効にする（※地図・地震情報を自動更新）", value=True)
tab1, tab2 = st.tabs(["強震モニタ", "津波情報"])

with tab1:
    st.markdown("### 地震モニタ")
    st.markdown("防災科学技術研究所（NIED）のデータを利用して、現在の震度分布をリアルタイムで表示します。")
    col_map, col_info = st.columns([7, 3])
    with col_map:
        image_placeholder = st.empty()
        status_placeholder = st.empty()
    with col_info:
        st.markdown("### 震度凡例")
        legend_html = """
        <div style="display: flex; flex-direction: column; width: 120px; border: 1px solid #ddd; padding: 8px; border-radius: 8px; background-color: #f9f9f9;">
    <div style="background-color: #b0000a; color: white; padding: 2px 0; text-align: center; font-weight: bold; margin-bottom: 3px; border-radius: 3px; font-size: 14px;">7</div>
    <div style="background-color: #e40001; color: white; padding: 2px 0; text-align: center; font-weight: bold; margin-bottom: 3px; border-radius: 3px; font-size: 14px;">6</div>
    <div style="background-color: #fd3304; color: white; padding: 2px 0; text-align: center; font-weight: bold; margin-bottom: 3px; border-radius: 3px; font-size: 14px;">5</div>
    <div style="background-color: #fd8906; color: white; padding: 2px 0; text-align: center; font-weight: bold; margin-bottom: 3px; border-radius: 3px; font-size: 14px;">4</div>
    <div style="background-color: #fdde05; color: black; padding: 2px 0; text-align: center; font-weight: bold; margin-bottom: 3px; border-radius: 3px; font-size: 14px;">3</div>
    <div style="background-color: #fdfd02; color: black; padding: 2px 0; text-align: center; font-weight: bold; margin-bottom: 3px; border-radius: 3px; font-size: 14px;">2</div>
    <div style="background-color: #d5ff14; color: black; padding: 2px 0; text-align: center; font-weight: bold; margin-bottom: 3px; border-radius: 3px; font-size: 14px;">1</div>
    <div style="background-color: #7fff00; color: black; padding: 2px 0; text-align: center; font-weight: bold; margin-bottom: 3px; border-radius: 3px; font-size: 14px;">0</div>
    <div style="background-color: #04c593; color: black; padding: 2px 0; text-align: center; font-weight: bold; margin-bottom: 3px; border-radius: 3px; font-size: 14px;">-1</div>
    <div style="background-color: #0447e9; color: black; padding: 2px 0; text-align: center; font-weight: bold; margin-bottom: 3px; border-radius: 3px; font-size: 14px;">-2</div>
    <div style="background-color: #0304ca; color: white; padding: 2px 0; text-align: center; font-weight: bold; border-radius: 3px; font-size: 14px;">-3</div>
</div>
        """
        st.markdown(legend_html, unsafe_allow_html=True)
        st.markdown("### 最新の地震履歴")
        history_placeholder = st.empty()

with tab2:
    st.markdown("### 津波警報・注意報")
    tsunami_time_placeholder = st.empty()
    tsunami_ui_placeholder = st.empty()

# 状態管理変数
last_jma_update = 0
last_tsunami_update = 0
earthquake_history_text = "データを読み込み中..."

intensity_map = {
    "1": "震度1", "2": "震度2", "3": "震度3", "4": "震度4",
    "5-": "震度5弱", "5+": "震度5強", "6-": "震度6弱", "6+": "震度6強", "7": "震度7"
}
tsunami_grade_map = {
    "MajorWarning": {"name": "大津波警報", "bg": "#800080", "txt": "white"},
    "Warning": {"name": "津波警報", "bg": "#ff0000", "txt": "white"},
    "Watch": {"name": "津波注意報", "bg": "#ffcc00", "txt": "black"},
    "Unknown": {"name": "津波予報等", "bg": "#00ccff", "txt": "black"}
}

# リアルタイム更新ループ
while is_running:
    current_loop_time = time.time()
    now = datetime.now(JST) - timedelta(seconds=5)
    date_str = now.strftime("%Y%m%d")
    time_str = now.strftime("%Y%m%d%H%M%S")
    
    # 1. 地図画像の更新
    jma_img, status = get_realtime_jma_image(date_str, time_str)
    if status == 200 and jma_img:
        combined_img = Image.alpha_composite(base_map, jma_img)
        image_placeholder.image(combined_img, caption=f"表示時刻: {now.strftime('%Y/%m/%d %H:%M:%S')}", use_container_width=True)
        status_placeholder.success("リアルタイムモニタリング中...")
    elif status == 404:
        status_placeholder.warning("最新データを待機中...")

    # 2. 地震履歴の更新 (15秒に1回)
    if current_loop_time - last_jma_update > 15:
        eq_data = fetch_earthquake_data()
        if eq_data:
            lines = []
            for eq in eq_data[:5]:
                at_str = eq.get("at")
                try:
                    dt = datetime.fromisoformat(at_str).astimezone(JST)
                    formatted_time = dt.strftime("%m/%d %H:%M")
                except:
                    formatted_time = at_str
                anm = eq.get("anm", "不明")
                max_int_code = str(eq.get("maxi", "-"))  
                max_int = intensity_map.get(max_int_code, f"震度{max_int_code}" if max_int_code != "-" else "不明")
                mag = str(eq.get("mag", "不明"))
                if max_int_code in ["5-", "5+", "6-", "6+", "7"]:
                    lines.append(f"🔴 **{formatted_time}** \n┗ **{anm} ({max_int} / M{mag})**")
                else:
                    lines.append(f"🔵 {formatted_time}  \n┗ {anm} ({max_int} / M{mag})")
            
            earthquake_history_text = "  \n  \n".join(lines)
            last_jma_update = current_loop_time
            
        history_placeholder.markdown(
            earthquake_history_text +
            "\n\n---\n🔴 **最大震度5弱以上の地震**\n\n🔵 **最大震度4以下の地震**"
        )

    # 3. 津波情報の更新 (15秒に1回)
    if current_loop_time - last_tsunami_update > 15:
        ts_data = fetch_tsunami_data()
        tsunami_html = ""
        if ts_data and len(ts_data) > 0 and not ts_data[0].get("cancelled", False) and len(ts_data[0].get("areas", [])) > 0:
            cards_html = "<div style='display: flex; flex-wrap: wrap; gap: 15px;'>"
            for area in ts_data[0].get("areas", []):
                style = tsunami_grade_map.get(area.get("grade", "Unknown"), tsunami_grade_map["Unknown"])
                cards_html += f"<div style='background-color: {style['bg']}; color: {style['txt']}; padding: 15px; border-radius: 10px; width: 230px;'><b>{style['name']}</b><br><span style='font-size:18px;'>{area.get('name', '不明')}</span></div>"
            cards_html += "</div>"
            tsunami_html = cards_html
        else:
            tsunami_html = "<div style='padding: 15px; background-color: #e6fced; color: #008000; border-radius: 8px; font-weight: bold;'>現在、津波警報・注意報は発表されていません。</div>"
        
        tsunami_time_placeholder.markdown(f"**情報更新時刻:** {datetime.now(JST).strftime('%Y/%m/%d %H:%M:%S')}")
        tsunami_ui_placeholder.markdown(tsunami_html, unsafe_allow_html=True)
        last_tsunami_update = current_loop_time
        
    time.sleep(1)