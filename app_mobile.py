"""
UPDRS Part III 評価アプリケーション（モバイル対応版）
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import os
from updrs_definitions import UPDRS_ITEMS, ITEM_ORDER, TREMOR_ITEMS, AKINETIC_RIGID_ITEMS

# ページ設定（モバイル対応）
st.set_page_config(
    page_title="UPDRS Part III 評価システム",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed",  # モバイルではデフォルトで閉じる
    menu_items={
        'About': "UPDRS Part III 評価システム v1.0 - モバイル対応版"
    }
)

# モバイル対応のCSS
st.markdown("""
<style>
    /* モバイル対応のスタイル */
    @media (max-width: 768px) {
        .stButton > button {
            width: 100%;
            margin: 2px 0;
            padding: 10px;
            font-size: 16px;
        }
        .stRadio > div {
            flex-direction: column;
        }
        .stRadio > div > label {
            margin: 5px 0;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        .main > div {
            padding: 0 10px;
        }
        h1 {
            font-size: 24px;
        }
        h2 {
            font-size: 20px;
        }
        h3 {
            font-size: 18px;
        }
    }
    
    /* PWA対応 */
    .stApp {
        overflow-x: hidden;
    }
    
    /* ボタンを見やすく */
    .stButton > button {
        background-color: #4CAF50;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
        font-size: 16px;
        cursor: pointer;
    }
    
    .stButton > button:hover {
        background-color: #45a049;
    }
    
    /* スコア選択を見やすく */
    .stRadio > div > label {
        cursor: pointer;
        transition: background-color 0.3s;
    }
    
    .stRadio > div > label:hover {
        background-color: #f0f0f0;
    }
</style>

<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<meta name="theme-color" content="#4CAF50">
<link rel="apple-touch-icon" href="🏥">
""", unsafe_allow_html=True)

# セッション状態の初期化
if 'scores' not in st.session_state:
    st.session_state.scores = {}
if 'patient_id' not in st.session_state:
    st.session_state.patient_id = ""
if 'evaluation_date' not in st.session_state:
    st.session_state.evaluation_date = datetime.now()
if 'current_item_index' not in st.session_state:
    st.session_state.current_item_index = 0
if 'medication_state' not in st.session_state:
    st.session_state.medication_state = "OFF"
if 'levodopa' not in st.session_state:
    st.session_state.levodopa = False
if 'levodopa_time' not in st.session_state:
    st.session_state.levodopa_time = None
if 'show_settings' not in st.session_state:
    st.session_state.show_settings = False

def calculate_subtypes():
    """サブタイプを計算する"""
    # 振戦スコアの計算
    tremor_scores = [st.session_state.scores.get(item, 0) for item in TREMOR_ITEMS]
    tremor_score = sum(tremor_scores) / len(TREMOR_ITEMS) if TREMOR_ITEMS else 0
    
    # 無動固縮スコアの計算
    ar_scores = [st.session_state.scores.get(item, 0) for item in AKINETIC_RIGID_ITEMS]
    ar_score = sum(ar_scores) / len(AKINETIC_RIGID_ITEMS) if AKINETIC_RIGID_ITEMS else 0
    
    # 比率の計算（ゼロ除算を避ける）
    if ar_score > 0:
        ratio = tremor_score / ar_score
    else:
        ratio = float('inf') if tremor_score > 0 else 1.0
    
    # サブタイプの判定（MDS-UPDRS基準）
    if ratio >= 0.82:
        subtype = "振戦優位型（TD）"
    elif ratio <= 0.71:
        subtype = "無動固縮型（AR）"
    else:
        subtype = "混合型（MX）"
    
    return {
        'tremor_score': tremor_score,
        'ar_score': ar_score,
        'ratio': ratio,
        'subtype_mds': subtype
    }

def save_to_csv():
    """評価結果をCSVに保存（モバイル対応）"""
    # データフレームの作成
    data = {
        'patient_id': st.session_state.patient_id,
        'evaluation_date': st.session_state.evaluation_date.strftime('%Y-%m-%d'),
        'medication_state': st.session_state.medication_state,
        'levodopa': 'Yes' if st.session_state.levodopa else 'No',
        'levodopa_time_minutes': st.session_state.levodopa_time if st.session_state.levodopa else None
    }
    
    # 各項目のスコアを追加
    for item in ITEM_ORDER:
        data[f'score_{item}'] = st.session_state.scores.get(item, 0)
    
    # 合計スコアとサブタイプを追加
    total_score = sum(st.session_state.scores.values())
    subtypes = calculate_subtypes()
    
    data['total_score'] = total_score
    data['tremor_score'] = subtypes['tremor_score']
    data['ar_score'] = subtypes['ar_score']
    data['td_ar_ratio'] = subtypes['ratio']
    data['subtype_mds'] = subtypes['subtype_mds']
    
    # CSVデータを作成
    df = pd.DataFrame([data])
    
    # ダウンロード用のCSVを作成
    csv = df.to_csv(index=False, encoding='utf-8-sig')
    
    return csv, df

# メインUI
st.title("🏥 UPDRS Part III")
st.markdown("### 運動機能検査")

# モバイル用の設定ボタン
col1, col2 = st.columns([3, 1])
with col2:
    if st.button("⚙️ 設定", key="settings_toggle"):
        st.session_state.show_settings = not st.session_state.show_settings

# 設定パネル（モバイル用）
if st.session_state.show_settings:
    with st.container():
        st.markdown("#### 評価情報")
        
        # 患者ID入力
        patient_id = st.text_input("患者ID", value=st.session_state.patient_id, key="patient_id_input")
        if patient_id != st.session_state.patient_id:
            st.session_state.patient_id = patient_id
        
        # 評価日
        st.session_state.evaluation_date = st.date_input(
            "評価日",
            value=st.session_state.evaluation_date,
            key="date_input"
        )
        
        # 薬物治療状態
        col1, col2 = st.columns(2)
        with col1:
            if st.button("OFF", key="med_off", type="secondary" if st.session_state.medication_state == "ON" else "primary"):
                st.session_state.medication_state = "OFF"
        with col2:
            if st.button("ON", key="med_on", type="secondary" if st.session_state.medication_state == "OFF" else "primary"):
                st.session_state.medication_state = "ON"
        
        # レボドパ服用
        st.session_state.levodopa = st.checkbox(
            "レボドパ服用",
            value=st.session_state.levodopa,
            key="levodopa_check"
        )
        
        if st.session_state.levodopa:
            st.session_state.levodopa_time = st.number_input(
                "最終服用からの時間（分）",
                min_value=0,
                value=st.session_state.levodopa_time or 0,
                key="levodopa_time_input"
            )
        
        st.divider()

# 進捗状況（モバイル用コンパクト表示）
progress = len(st.session_state.scores) / len(ITEM_ORDER)
st.progress(progress)
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("完了", f"{len(st.session_state.scores)}/33")
with col2:
    st.metric("合計", sum(st.session_state.scores.values()))
with col3:
    if st.session_state.scores:
        subtypes = calculate_subtypes()
        st.metric("型", subtypes['subtype_mds'][:2])

st.divider()

# メインエリア
if not st.session_state.patient_id:
    st.warning("⚠️ 上の設定ボタンから患者IDを入力してください")
else:
    # 現在の評価項目表示
    current_item_key = ITEM_ORDER[st.session_state.current_item_index]
    current_item = UPDRS_ITEMS[current_item_key]
    
    # 項目情報表示（モバイル用コンパクト）
    st.subheader(f"{current_item_key}: {current_item['name']}")
    
    # 項目選択（モバイル用）
    selected_index = st.selectbox(
        "評価項目",
        range(len(ITEM_ORDER)),
        format_func=lambda x: f"{ITEM_ORDER[x]}: {UPDRS_ITEMS[ITEM_ORDER[x]]['name'][:20]}...",
        index=st.session_state.current_item_index,
        key="item_selector_mobile"
    )
    st.session_state.current_item_index = selected_index
    
    st.info(f"💡 {current_item['description']}")
    
    # スコア選択（モバイル用大きめボタン）
    st.markdown("### スコアを選択")
    
    # 現在のスコア取得
    current_score = st.session_state.scores.get(current_item_key, None)
    
    # スコアボタン（モバイル用）
    cols = st.columns(5)
    for i in range(5):
        with cols[i]:
            button_type = "primary" if current_score == i else "secondary"
            if st.button(str(i), key=f"score_btn_{i}", type=button_type, use_container_width=True):
                st.session_state.scores[current_item_key] = i
                st.rerun()
    
    # スコア説明（折りたたみ可能）
    with st.expander("スコアの詳細説明"):
        for score, description in current_item['scores'].items():
            st.markdown(f"**{score}点**: {description}")
    
    st.divider()
    
    # ナビゲーションボタン（モバイル用大きめ）
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("◀ 前へ", disabled=st.session_state.current_item_index == 0, use_container_width=True):
            st.session_state.current_item_index -= 1
            st.rerun()
    
    with col2:
        if st.button("💾 保存", type="primary", use_container_width=True):
            if len(st.session_state.scores) == 0:
                st.error("評価項目が入力されていません")
            else:
                csv_data, df = save_to_csv()
                st.success("✅ データを準備しました")
                
                # ダウンロードボタン
                st.download_button(
                    label="📥 CSVダウンロード",
                    data=csv_data,
                    file_name=f"updrs_{st.session_state.patient_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
    
    with col3:
        if st.button("次へ ▶", disabled=st.session_state.current_item_index >= len(ITEM_ORDER) - 1, use_container_width=True):
            st.session_state.current_item_index += 1
            st.rerun()
    
    # 評価済み項目の表示（モバイル用コンパクト）
    if st.session_state.scores:
        with st.expander(f"評価済み項目 ({len(st.session_state.scores)}件)"):
            for item_key in ITEM_ORDER:
                if item_key in st.session_state.scores:
                    st.write(f"• {item_key}: {UPDRS_ITEMS[item_key]['name'][:20]}... → **{st.session_state.scores[item_key]}点**")
    
    # リセットボタン（モバイル用）
    if st.button("🔄 すべてリセット", use_container_width=True):
        st.session_state.scores = {}
        st.session_state.current_item_index = 0
        st.rerun()

# フッター（モバイル用シンプル）
st.markdown("---")
st.markdown("UPDRS Part III 評価システム v1.0", help="© 2024")
