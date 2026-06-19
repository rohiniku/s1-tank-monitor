import os
import json
import numpy as np
import pandas as pd
from google import genai
from google.genai import types
import time

# =======================================================================
# 🕵️ 昨晩定義した「4人の固定専門家プロンプト」の完全定義
# =======================================================================
PROMPTS = {
    "sar_expert": (
        "あなたは人工衛星（SARレーダー）の地球観測データ解析の専門家です。\n"
        "渡された石油タンクVV-VH偏波時系列データ（dB値）のみを客観的に評価してください。\n\n"
        "【課せられた任務】\n"
        "1. 直近データの数値が、過去の平均的なベースラインと比較して高い（満タン・蓋が上昇）か、低い（在庫減・蓋が下降）かを判定せよ。\n"
        "2. 突発的な1点のみの異常な跳ね上がり（スパイク）がある場合、原油の運用ではなく「撮影当日の現地の大雨による鏡面反射ノイズ」の可能性を考慮して評価せよ。\n"
        "3. 専門用語（dB、偏波、ベースライン等）を交え、データが示す物理的変化のみを2000～2450文字以内の日本語で冷徹に報告せよ。背景のニュース等は一切記述するな。"
    ),
    "weather_watcher": (
        "あなたは寒冷地（北海道・北陸・東北）の気象災害とインフラへの影響を専門とする環境アナリストです。\n"
        "渡された時系列データと、インターネット上のリアルタイム検索を組み合わせて分析してください。\n\n"
        "【課せられた任務】\n"
        "1. むつ、苫小牧、北海道、福井のデータに落ち込み（谷）が見られる場合、現在の現地の積雪量、凍結状況、または雪解け（融雪）の進捗状況をGoogleで検索し、気象事象との因果関係を特定せよ。\n"
        "2. 直近のデータ変化が、季節的な気象ノイズ（雪による電波吸収）なのか、それとも気象影響のない純粋なタンクの動きなのかを気象学の視点から評価せよ。\n"
        "3. 分析結果を2000～2450文字以内の日本語で簡潔に報告せよ。"
    ),
    "fact_checker": (
        "あなたは国際ニュースの報道内容と、現地の物理データを照らし合わせるファクトチェッカーです。\n"
        "渡された時系列データと、インターネット上のリアルタイム検索を組み合わせて分析してください。\n\n"
        "【課せられた任務】\n"
        "1. 「日本政府による国家備蓄原油の緊急放出、取り崩し、タンカーの入港状況」に関する最新のニュース（経済産業省の発表やマスコミ報道）をGoogleで検索し、直近の具体的な動きを把握せよ。\n"
        "2. 報道されている放出・輸入のタイミングと、目の前にある4大基地（志布志・福井・苫小牧・むつ）の実際のデータ変化（傾き）を比較し、タイムラグや矛盾、あるいは一致している点を冷徹に暴き出せ。\n"
        "3. 報道の裏に隠された地上のリアルな戦術を2000～2450文字以内の日本語で報告せよ。"
    ),
    "security_analyst": (
        "あなたは地政学リスク（中東情勢、ホルムズ海峡封鎖危機など）に伴う、日本のエネルギー安全保障の逼迫度を評価するシニアアナリストです。\n"
        "渡された時系列データと、インターネット上のリアルタイム検索を組み合わせて分析してください。\n\n"
        "【課せられた任務】\n"
        "1. 現在の「中東情勢、原油の供給途絶リスク、シーバースの緊迫度」に関する最新の世界情勢をGoogleで検索せよ。\n"
        "2. 4大基地全体の長期移動平均線が、過去の安全水域を維持しているか、あるいは危険水準（枯渇へのカウントダウン）に突入しているかを評価せよ。\n"
        "3. 日本のエネルギーの残り時間とリスクのフェーズを、緊張感を持って2000～2450文字以内の日本語で提言せよ。"
    )
}

# 💡 データのオウム返しを防ぎ、歴史を踏まえた有事解釈を強制する共通の最優先指令
PRIORITY_INSTRUCTION = (
    "\n\n【最優先の解析指令】\n"
    "あなたは過去数年分の膨大な時系列データ全体を読み込み、各基地固有の「長期的な季節変動の波（冬の積雪による定期的な減衰パターン）」や「平時の基準値（ベースライン）」を脳内で完全に把握・モデル化せよ。\n"
    "その巨大な歴史的背景を踏まえた上で、データの一番右端（直近数週間〜本日の最新データ）に起きている変化が、「例年通りの季節の波」なのか、それとも中東情勢や政府発表とリンクした「前例のない異常な有事トレンド（取り崩しや滑り込み荷揚げ）」なのかを冷徹にファクトチェックし、本日の結論を150文字以内の日本語で報告せよ。"
)

def get_clean_timeseries_data():
    """4大基地のCSVから、プロットと100%同じ幾何フィルター、黄金の2年分スライス、60D/120Dローリング平均と傾きを算出する"""
    regions = ['shibushi', 'fukui', 'tomakomai', 'mutsu']
    processed_data = {}
    
    for r in regions:
        csv_path = f"data/{r}_tank_timeseries.csv"
        if not os.path.exists(csv_path):
            continue
            
        df = pd.read_csv(csv_path)
        
        # 💡 【幾何同期】プロット用コードと100%同じ厳密なフィルタリングを適用
        if 'orbitProperties_pass' in df.columns:
            df = df[df['orbitProperties_pass'] == 'DESCENDING']
        if 'localIncidenceAngle' in df.columns:
            df = df[(df['localIncidenceAngle'] >= 35.5) & (df['localIncidenceAngle'] <= 36.5)]
            
        df['date_parsed'] = pd.to_datetime(df['date'])
        
        # 💡 【ミリ秒ソート】あなたが見抜いた一本の数珠つなぎにするための厳密ソート
        if 'system:time_start' in df.columns:
            df['datetime_utc'] = pd.to_datetime(df['system:time_start'], unit='ms')
            df = df.sort_values('datetime_utc')
        else:
            df = df.sort_values('date_parsed')
            
        # 地域・日付ごとに平均して個別タンクのガタつきノイズを消し去る
        daily_df = df.groupby('date_parsed').agg({'vv': 'mean', 'vh': 'mean'}).reset_index()
        daily_df['vv_minus_vh'] = daily_df['vv'] - daily_df['vh']
        
        # あなたが選んだ大正解の時間枠ベース（Time-based window）に変換
        daily_df = daily_df.set_index('date_parsed').sort_index()
        
        # 💡 【黄金の2年分スライス】季節の証拠を2回踏ませ、かつ古い歴史に迷わせない
        latest_time = daily_df.index.max()
        start_time = latest_time - pd.Timedelta(days=730)
        daily_df = daily_df[daily_df.index >= start_time]
        
        # 60日線（短期）と 120日線（長期ベースライン）を正確に計算してAIにプレゼント
        daily_df['rolling_60D'] = daily_df['vv_minus_vh'].rolling(window='60D', min_periods=1).mean()
        daily_df['rolling_120D'] = daily_df['vv_minus_vh'].rolling(window='120D', min_periods=1).mean()
        
        # 💡 【数理アシスト】直近60日移動平均線の本当の「傾き（モメンタム）」を算出
        daily_df['slope_60D'] = daily_df['rolling_60D'] - daily_df['rolling_60D'].shift(60, freq='D').reindex(daily_df.index, method='ffill')
        daily_df['slope_60D'] = daily_df['slope_60D'].fillna(0)
        
        processed_data[r] = daily_df.reset_index()
        
    return processed_data

def build_patterns(processed_data):
    """人間とシステムがAIの性質を見極めるため、A/Bテスト実験用の3つの表現パターンを構築する"""
    # 【パターンA: 生数値バルク型】
    pattern_a_str = "【パターンA：過去2年分全基地一斉観測生デシベル（VV/VH）時系列データ】\n"
    # 【パターンB: 数理アシスト型】
    pattern_b_str = "【パターンB：過去2年分長期ベースライン（120日平均）および直近60日線の傾きデータ】\n"
    # 【パターンC: 意味抽出ラベル型】
    pattern_c_str = "【パターンC：Python側で1次解釈を終えた意味抽出ラベル】\n"
    
    for r, df in processed_data.items():
        if df.empty: continue
        latest = df.iloc[-1]
        
        # パターンAの構築（2年分の全履歴をそのままCSVテキスト化）
        pattern_a_str += f"\n■ 基地: {r}\n" + df[['date_parsed', 'vv', 'vh']].to_csv(index=False)
        
        # パターンBの構築（計算済みの数学的な武器をプレゼント）
        pattern_b_str += f"\n■ 基地: {r}\n" + df[['date_parsed', 'rolling_120D', 'slope_60D']].to_csv(index=False)
        
        # パターンCの構築（ルールベースで完全に安全な言葉に一度落とし込む）
        status_120 = "例年並みの安定水準"
        if latest['rolling_120D'] < df['rolling_120D'].mean() - 1.0: 
            status_120 = "過去数年で最低水準まで低下中（貯蔵の糊代枯渇の危機）"
        elif latest['rolling_120D'] > df['rolling_120D'].mean() + 1.0: 
            status_120 = "過去最高水準の歴史的満タン状態（最高警戒ホールド）"
            
        status_60 = "横ばいで安定維持"
        if latest['slope_60D'] < -0.2: 
            status_60 = "前例のない速度で急激に払い出し（在庫激減・緊急放出）が進行中"
        elif latest['slope_60D'] > 0.2: 
            status_60 = "最後の荷揚げ原油による集中蓄積・蓋の急上昇トレンドを検知"
            
        pattern_c_str += f"・基地: {r} / 長期状態: {status_120} / 直近60日モメンタム: {status_60}\n"
        
    return pattern_a_str, pattern_b_str, pattern_c_str

def ask_gemini(client, full_prompt):
    """Google Search Grounding（リアルタイムネット検索機能）を完全内蔵してGemini 1.5 Flashをキックする"""
    try:
        # 💡 toolsにGoogleSearchを指定するだけで、AIが自らリアルタイムの気象・地政学ニュースを検索します
        config = types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
            temperature=0.1,  # 完全に冷徹にファクトを追わせ、ハルシネーションを防ぐ設定
            # max_output_tokens=2500
        )
        response = client.models.generate_content(
            model='gemini-2.5-flash',  # 💡 これが最新の無料枠対応の正しいモデル名指定です！
            contents=full_prompt,
            config=config
        )
        return response.text.strip()
    except Exception as e:
        return f"AIレポート生成エラー: {e}"

def main():
    # GitHubのSecrets、またはローカルの環境変数からAPIキーを読み込む
    api_key = os.environ.get("GEMINI_API_KEY")
    output_json_path = "ai_report.json"
    
    if not api_key:
        print("WARNING: GEMINI_API_KEY not found. Outputting dummy JSON to avoid pipeline crash.")
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump({}, f)
        return

    # 最新の公式 google-genai クライアントの初期化
    client = genai.Client(api_key=api_key)
    
    print("Step 1: Fetching and filtering timeseries data from local CSVs...")
    data_dict = get_clean_timeseries_data()
    
    print("Step 2: Constructing 3 evaluation pattern strings (A, B, C)...")
    pat_a, pat_b, pat_c = build_patterns(data_dict)
    patterns = {"pattern_a": pat_a, "pattern_b": pat_b, "pattern_c": pat_c}
    
    results = {}
    
    print("Step 3: Triggering Gemini 2.5 Flash with Search Grounding (Total 12 requests with rate-limit protection)...")
    # 4人の専門家×3つのパターンのマトリクスループ（12回）
    for expert_key, base_prompt in PROMPTS.items():
        results[expert_key] = {}
        full_role_prompt = base_prompt + PRIORITY_INSTRUCTION
        
        for pat_key, pat_text in patterns.items():
            print(f" -> Processing [{expert_key}] x [{pat_key}]...")
            full_prompt = f"{full_role_prompt}\n\n{pat_text}"
            
            # APIを叩いてレポート文を取得
            print("    Sending request to Gemini API...")
            print("    Full prompt length (characters):", len(full_prompt))
            print("    Full prompt preview (first 500 chars):", full_prompt)

            comment = ask_gemini(client, full_prompt)
            results[expert_key][pat_key] = comment
            print("    Received comment:", comment)
            break

            # ========================================================
            # 💡 【重要：429エラー完全根絶のホットフィックス】
            #     1回リクエストを投げるたびに「13秒」あえて待機（スリープ）します。
            #     これにより分速4.5回ペースとなり、無料枠の制限（分速5回）を完全に回避します。
            # ========================================================
            print("    Waiting 13 seconds to respect Gemini API rate limits...")
            time.sleep(13)
            # ========================================================
        break

    # 構造化したピュアなJSONファイルとして保存
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    print(f"\n🎉 SUCCESS: Saved multi-expert AI intelligence to {output_json_path}")

if __name__ == '__main__':
    main()
