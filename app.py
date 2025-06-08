"""
UPDRS Part III 評価アプリケーション
UPDRS評価システム
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import os
from updrs_definitions import UPDRS_ITEMS, ITEM_ORDER, TREMOR_ITEMS, AKINETIC_RIGID_ITEMS

# ページ設定（最初に実行必須）
st.set_page_config(
    page_title="UPDRS Part III 評価システム",
    page_icon="🏥",
    layout="wide"
)


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
    
    # 従来のUPDRS基準も計算
    if tremor_score >= 2 * ar_score:
        classic_subtype = "振戦優位型（TD）"
    elif ar_score >= 2 * tremor_score:
        classic_subtype = "無動固縮型（AR）"
    else:
        classic_subtype = "混合型（MX）"
    
    return {
        'tremor_score': tremor_score,
        'ar_score': ar_score,
        'ratio': ratio,
        'subtype_mds': subtype,
        'subtype_classic': classic_subtype
    }

def save_to_csv():
    """評価結果をCSVに保存"""
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
    data['subtype_classic'] = subtypes['subtype_classic']
    
    # データフレームに変換
    df = pd.DataFrame([data])
    
    # ファイル名の生成
    filename = f"updrs_evaluations_{datetime.now().strftime('%Y%m%d')}.csv"
    
    # カレントディレクトリに保存
    filepath = filename
    
    # 既存ファイルがあれば追記、なければ新規作成
    if os.path.exists(filepath):
        existing_df = pd.read_csv(filepath)
        df = pd.concat([existing_df, df], ignore_index=True)
    
    df.to_csv(filepath, index=False, encoding='utf-8-sig')
    return filepath

# メインUI
st.title("🏥 MDS-UPDRS Part III 評価システム")
st.markdown("### 運動機能検査（Motor Examination）")
st.info("🔍 UPDRS評価アプリケーション")


# サイドバー
with st.sidebar:
    st.header("評価情報")
    
    # 患者ID入力
    patient_id = st.text_input("患者ID", value=st.session_state.patient_id)
    if patient_id != st.session_state.patient_id:
        st.session_state.patient_id = patient_id
    
    # 評価日
    st.session_state.evaluation_date = st.date_input(
        "評価日",
        value=st.session_state.evaluation_date
    )
    
    # 薬物治療状態
    st.session_state.medication_state = st.radio(
        "薬物治療状態",
        ["OFF", "ON"],
        index=0 if st.session_state.medication_state == "OFF" else 1
    )
    
    # レボドパ服用
    st.session_state.levodopa = st.checkbox(
        "レボドパ服用",
        value=st.session_state.levodopa
    )
    
    if st.session_state.levodopa:
        st.session_state.levodopa_time = st.number_input(
            "最終服用からの時間（分）",
            min_value=0,
            value=st.session_state.levodopa_time or 0
        )
    
    st.divider()
    
    # 進捗状況
    st.header("進捗状況")
    progress = len(st.session_state.scores) / len(ITEM_ORDER)
    st.progress(progress)
    st.write(f"完了: {len(st.session_state.scores)}/{len(ITEM_ORDER)} 項目")
    
    # 現在のスコア
    if st.session_state.scores:
        st.divider()
        st.header("現在のスコア")
        total_score = sum(st.session_state.scores.values())
        st.metric("合計スコア", total_score)
        
        # サブタイプ計算
        subtypes = calculate_subtypes()
        st.metric("振戦スコア", f"{subtypes['tremor_score']:.2f}")
        st.metric("無動固縮スコア", f"{subtypes['ar_score']:.2f}")
        st.metric("TD/AR比", f"{subtypes['ratio']:.2f}")
        st.info(f"サブタイプ（MDS）: {subtypes['subtype_mds']}")
        st.info(f"サブタイプ（従来）: {subtypes['subtype_classic']}")

# メインエリア
if not st.session_state.patient_id:
    st.warning("⚠️ 左のサイドバーで患者IDを入力してください")
else:
    # 全項目完了チェック
    all_completed = len(st.session_state.scores) == len(ITEM_ORDER)
    is_last_item = st.session_state.current_item_index >= len(ITEM_ORDER) - 1
    
    # ナビゲーションボタン - 最後の項目では完了ボタンを表示
    if is_last_item:
        col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
    else:
        col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
    
    with col1:
        if st.button("◀ 前へ", disabled=st.session_state.current_item_index == 0):
            st.session_state.current_item_index -= 1
    
    with col2:
        if is_last_item:
            # 最後の項目では完了ボタンを表示
            if st.button("✅ 完了", type="primary"):
                if all_completed:
                    filepath = save_to_csv()
                    st.success(f"🎉 評価完了！結果を保存しました: {os.path.basename(filepath)}")
                    st.balloons()
                else:
                    st.error("すべての項目を評価してください")
        else:
            if st.button("次へ ▶"):
                st.session_state.current_item_index += 1
    
    with col3:
        # 項目選択
        selected_item = st.selectbox(
            "評価項目を選択",
            options=ITEM_ORDER,
            format_func=lambda x: f"{x}: {UPDRS_ITEMS[x]['name']}",
            index=st.session_state.current_item_index,
            key="item_selector"
        )
        st.session_state.current_item_index = ITEM_ORDER.index(selected_item)
    
    with col4:
        if st.button("💾 保存", type="primary"):
            if len(st.session_state.scores) == 0:
                st.error("評価項目が入力されていません")
            else:
                filepath = save_to_csv()
                st.success(f"✅ 保存しました: {os.path.basename(filepath)}")
    
    with col5:
        if st.button("🔄 リセット"):
            st.session_state.scores = {}
            st.session_state.current_item_index = 0
            st.rerun()
    
    
    st.divider()
    
    # 全項目完了時の表示
    if all_completed:
        st.success("🎉 すべての項目の評価が完了しました！")
        st.info("「完了」ボタンを押して結果を保存してください。")
    
    # 現在の評価項目表示
    current_item_key = ITEM_ORDER[st.session_state.current_item_index]
    current_item = UPDRS_ITEMS[current_item_key]
    
    # 項目情報表示
    st.subheader(f"{current_item_key}: {current_item['name']}")
    st.info(f"💡 **評価方法**: {current_item['description']}")
    
    # スコア選択
    st.markdown("### スコアを選択してください")
    
    # 現在のスコア取得
    current_score = st.session_state.scores.get(current_item_key, None)
    
    # ラジオボタンでスコア選択
    score_options = []
    for score, description in current_item['scores'].items():
        score_options.append(f"**{score}点**: {description}")
    
    if current_score is not None:
        default_index = current_score
    else:
        default_index = None
    
    selected_score_text = st.radio(
        "スコア",
        options=score_options,
        index=default_index,
        key=f"score_{current_item_key}"
    )
    
    # スコアを抽出して保存
    if selected_score_text:
        selected_score = int(selected_score_text.split(":")[0].replace("**", "").replace("点", ""))
        st.session_state.scores[current_item_key] = selected_score
    
    # 評価済み項目の一覧
    st.divider()
    st.markdown("### 評価済み項目")
    
    if st.session_state.scores:
        # 評価済み項目をデータフレームで表示
        evaluated_items = []
        for item_key in ITEM_ORDER:
            if item_key in st.session_state.scores:
                evaluated_items.append({
                    '項目': item_key,
                    '項目名': UPDRS_ITEMS[item_key]['name'],
                    'スコア': st.session_state.scores[item_key]
                })
        
        df_evaluated = pd.DataFrame(evaluated_items)
        st.dataframe(df_evaluated, use_container_width=True)
    else:
        st.info("まだ評価された項目はありません")
    
    
    # 使用方法とキーボードショートカット情報
    with st.expander("💡 使用方法とキーボードショートカット"):
        st.markdown("""
        **使用方法:**
        1. サイドバーで患者情報を入力
        2. 各項目を順番に評価（「前へ」「次へ」ボタンまたは項目選択）
        3. 各項目でスコアを選択
        4. 全項目完了後、「完了」ボタンでCSVファイルに保存
        
        **機能:**
        - 自動サブタイプ判定（MDS-UPDRS基準と従来基準）
        - リアルタイム進捗表示
        - CSV形式での結果保存
        """)

# フッター
st.markdown("---")
st.markdown("© 2024 UPDRS Part III 評価システム")