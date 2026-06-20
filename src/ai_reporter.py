import os
import json
import time
import argparse
from datetime import datetime
import pandas as pd
from google import genai
from google.genai import types
from google.api_core.exceptions import ServiceUnavailable

# =======================================================================
# 🎭 「3人の精鋭ロール」の定義
# =======================================================================
PROMPTS = {
    "sar_expert": (
        "あなたは人工衛星（SARレーダー）の地球観測データ解析の専門家です。\n"
        "あなたは検索ツールを使用してはならない。\n"  
        "渡された石油タンクVV-VH偏波時系列データ（dB値）のみを客観的に評価してください。\n\n"
        "【課せられた任務】\n"
        "1. 直近データの数値が、過去の平均的なベースラインと比較して高い（満タン・蓋が上昇）か、低い（在庫減・蓋が下降）かを判定せよ。\n"
        "※過去ベースラインと同等で変化がない基地（例：冬季積雪から回復済みの苫小牧・むつ等）は、完全に記述を割愛するか、基地名のみに留めよ。異常値が出ている基地のみに記述を集中させよ。\n"
        "2. 突発的な1点のみの異常な跳ね上がり（スパイク）がある場合、原油の運用ではなく「撮影当日の現地の大雨による鏡面反射ノイズ」の可能性を考慮して評価せよ。\n"
        "3. 専門用語（dB、偏波、ベースライン等）を交え、データが示す物理的変化のみを報告せよ。背景のニュース等は一切記述するな。\n"
    ),
    "fact_checker": (
        "あなたは国際ニュースの報道内容と、現地の物理データを照らし合わせるファクトチェッカーです。\n"
        "渡された時系列データと、インターネット上のリアルタイム検索を組み合わせて分析してください。\n\n"
        "【課せられた任務】\n"
        "1. 「日本政府による国家備蓄原油の緊急放出、取り崩し、タンカーの入港状況」に関する最新のニュース（経済産業省の発表やマスコミ報道）をGoogleで検索し、直近の具体的な動きを把握せよ。\n"
        "2. 報道されている放出・輸入のタイミングと、目の前にある4大基地（志布志・福井・苫小牧・むつ）の実際のデータ変化（傾き）を比較し、タイムラグや矛盾、あるいは一致している点を冷徹に暴き出せ。\n"
        "※データが平年並みで報道との乖離がない基地（積雪回復後の苫小牧等）の定型的な説明は不要。矛盾や異常な兆候がある基地のみをフォーカスせよ。\n"
        "Google検索ツールに渡す検索クエリを生成する際は、以下の語句を参考にせよ：\n"
        "「日本 国家備蓄 原油 放出」\n"
        "「経産省 原油 備蓄」\n"
        "「日本 原油 輸入 タンカー」\n"
        "これらを組み合わせた検索クエリを生成し、最新の報道を取得せよ。\n"
    ),
    "security_analyst": (
        "あなたは地政学リスク（中東情勢、ホルムズ海峡封鎖危機など）に伴う、日本のエネルギー安全保障の逼迫度を評価するシニアアナリストです。\n"
        "渡された時系列データと、インターネット上のリアルタイム検索を組み合わせて分析してください。\n\n"
        "【課せられた任務】\n"
        "1. 現在の「中東情勢、原油の供給途絶リスク、シーバースの緊迫度」に関する最新の世界情勢をGoogleで検索せよ。\n"
        "2. 4大基地全体の長期移動平均線が、過去の安全水域を維持しているか、あるいは危険水準（枯渇へのカウントダウン）に突入しているかを評価せよ。\n"
        "※全体が安全水域にある場合や、例年通りの季節回復（苫小牧等）をしている箇所は、単に『全体として安全』等と一括し、個別の基地ごとの無駄な生存報告は記述するな。\n"
        "【検索クエリ指示】\n"
        "Google検索ツールに渡す検索クエリを生成する際は、以下の語句を参考にせよ：\n"
        "「中東 原油 供給リスク」\n"
        "「ホルムズ海峡 緊迫」\n"
        "「原油 価格 供給不安」\n"
        "これらを組み合わせた検索クエリを生成し、最新の世界情勢を取得せよ。\n"
        "ニュース検索では日本国内の報道機関の記事よりも、国際的な報道や専門家の分析が優先されるべきであることに留意せよ。\n"
    )
}

# =======================================================================
# ❄️ 【雪のドメイン知識を完全統合】＆【3行・150文字の出力形式絶対命令】
# =======================================================================
PRIORITY_INSTRUCTION = (
    "\n\n【SAR物理前提（全ロール共通）】\n"
    "・VV/VH偏波が上昇する＝タンク屋根が上昇＝在庫増加（満タン方向）。\n"
    "・VV/VH偏波が下降する＝タンク屋根が下降＝在庫減少（払い出し）。\n"
    "・この物理法則は全ロールが絶対に遵守すること。\n\n"
    "【最優先の解析および出力指令（※全アナリスト共通の大前提知識）】\n"
    "1. 石油タンクのSAR観測において、冬季（12月〜3月）に北海道（苫小牧）や東北（むつ）のデータが突発的または持続的に著しく下落する現象は、「現地の積雪・凍結によるレーダー波の吸収減衰（気象ノイズ）」である可能性が極めて高い。この過去2年間の季節性ノイズの波を脳内で完全にモデル化し、有事の原油の減少（払い出し）と絶対に混同するな。\n"
    "2. 直近データが過去平均（ベースライン）に戻って安定している基地（例：積雪から回復した苫小牧・むつ等）は、重要度が極めて低いためレポート内での言及（生存報告）を一切禁止する。過去平均から著しく乖離している『前例のない異常な有事トレンド（志布志の偏波上昇など）』のファクトチェックにのみ、150文字の全リソースを集中せよ。\n"
    "3. 思考プロセスや検索結果の要約、英語の解説文（『The search results confirm...』等）は一切出力してはならない。思考と言語は脳内（内部処理）で完結させ、出力バッファには以下の【型】の日本語の箇条書きのみをダイレクトに書き込め。\n\n"
    "【出力フォーマット制限】\n"
    "Webサイトを訪れたユーザーが1秒で大局を理解できるように、最終出力は以下の【型】に厳密に従い、各項目5080〜120文字、全体で300〜400文字の美しい日本語でのみ箇条書きで出力せよ。\n"
    "【型】の2番目にある「ネット検索から紐解いた因果関係や報道との矛盾」の項目は、SARエキスパート以外の2人のロール（ファクトチェッカーと安全保障アナリスト）にのみ適用される項目であることに留意せよ。SARエキスパートはこの項目を完全にスキップし、出力からも完全に割愛せよ。\n"
    "max_output_tokensによる物理的な檻は撤廃したため、途中でブツ切りになる心配をせず、あなたのディープな考察エッセンスを凝縮せよ。\n"
    "挨拶文、導入文、章分け（1.序論など）、前置き（『承知いたしました』や英語の解説等）や、Markdownの太字（**）などの余計な装飾は一切出力するな。他のすべての思考を排除し、いきなり最初の『・』から始めよ。\n\n"
    "・[データが示す物理ファクト（※過去平均並みで安定している基地の記述は禁止）]\n"
    "・[ネット検索から紐解いた因果関係や報道との矛盾]\n"
    "・[明日以降の最大の警戒シグナル]"
)

def get_clean_timeseries_data(data_dir='data'):
    """4大基地のCSVから、プロットと100%同じ幾何フィルター、黄金の2年分スライスを適用した生データを抽出する"""
    regions = ['shibushi', 'fukui', 'tomakomai', 'mutsu']
    processed_data = {}
    
    for r in regions:
        csv_path = os.path.join(data_dir, f"{r}_tank_timeseries.csv")
        if not os.path.exists(csv_path):
            continue
            
        df = pd.read_csv(csv_path)
        
        # 💡 【幾何同期】プロットコードと100%同じ厳密なフィルター
        if 'orbitProperties_pass' in df.columns:
            df = df[df['orbitProperties_pass'] == 'DESCENDING']
        if 'localIncidenceAngle' in df.columns:
            df = df[(df['localIncidenceAngle'] >= 35.5) & (df['localIncidenceAngle'] <= 36.5)]
            
        df['date_parsed'] = pd.to_datetime(df['date'])
        
        # 💡 【ミリ秒ソート】一本の数珠つなぎにする厳密時系列ソート
        if 'system:time_start' in df.columns:
            df['datetime_utc'] = pd.to_datetime(df['system:time_start'], unit='ms')
            df = df.sort_values('datetime_utc')
        else:
            df = df.sort_values('date_parsed')
            
        # 地域・日付ごとに平均して個別タンクのガタつきを消去
        daily_df = df.groupby('date_parsed').agg({'vv': 'mean', 'vh': 'mean'}).reset_index()
        daily_df = daily_df.set_index('date_parsed').sort_index()
        
        # 💡 【黄金の2年分スライス】季節の証拠を2回踏ませ、かつ古い歴史に迷わせない
        latest_time = daily_df.index.max()
        start_time = latest_time - pd.Timedelta(days=730)
        daily_df = daily_df[daily_df.index >= start_time]
        
        processed_data[r] = daily_df.reset_index()
        
    return processed_data

def ask_gemini(client, full_prompt, max_retries=3, initial_delay=2):
    """503エラー時に自動でリトライするラッパー関数"""
    delay = initial_delay
    for attempt in range(max_retries):
        try:
            # 💡 max_output_tokens の制限を完全撤廃！AI本来の知能と安心感をフルに解放します
            config = types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=0.1  # 完全に冷徹にファクトを追わせ、ハルシネーションを防ぐ設定
            )
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=full_prompt,
                config=config
            )
            
            # 💡 応答が空の場合、エラーを発生させてexceptブロック（リトライ）へ流す
            if response is None or response.text is None:
                raise ValueError("AIからの応答が空（None）でした（検索クエリ拒絶等の可能性）")
                
            return response.text.strip()
        except Exception as e:
            # エラーメッセージ文字列に "503" または "UNAVAILABLE" が含まれているかチェック
            err_msg = str(e)
            is_transient = "503" in err_msg or "UNAVAILABLE" in err_msg or "応答が空" in err_msg
            
            if is_transient and attempt < max_retries - 1:
                # 指数バックオフで待機時間を延ばしながらリトライ
                time.sleep(delay)
                delay *= 2
                continue
                
            # 最終リトライでも失敗、または503以外の致命的エラーの場合
            return f"AIレポート生成エラー: {err_msg}"

def main():
    # GitHubのSecrets、またはローカルの環境変数からAPIキーを読み込む
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', default='reports', help='Directory to write AI report JSON')
    parser.add_argument('--data-dir', default='data', help='Directory to read CSV timeseries from')
    parser.add_argument('--no-timestamp', action='store_true', help='Do not append timestamp to filename')
    args = parser.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY")

    output_dir = args.output_dir or 'reports'
    data_dir = args.data_dir or 'data'
    os.makedirs(output_dir, exist_ok=True)

    if args.no_timestamp:
        filename = "ai_report.json"
    else:
        filename = f"ai_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    output_json_path = os.path.join(output_dir, filename)
    
    if not api_key:
        print("WARNING: GEMINI_API_KEY not found. Outputting dummy JSON to avoid pipeline crash.")
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump({}, f)
        print(f"Wrote dummy report to {output_json_path}")
        return

    client = genai.Client(api_key=api_key)
    data_dict = get_clean_timeseries_data(data_dir=data_dir)
    
    analysis_target_desc = "【分析対象：過去2年間 全基地一斉観測生デシベル（VV/VH）時系列データ】\n"
    for r, df in data_dict.items():
        if df.empty: continue
        analysis_target_desc += f"\n■ 基地名: {r}\n" + df[['date_parsed', 'vv', 'vh']].to_csv(index=False)
    
    results = {}
    
    print("Step 3: Triggering Gemini 2.5 Flash (Slim 3-request mode with Per-Day protection)...")
    # 3人の専門家ループ
    for expert_key, base_prompt in PROMPTS.items():
        full_prompt = f"{base_prompt}{PRIORITY_INSTRUCTION}\n\n{analysis_target_desc}"
        
        print(f" -> Requesting {expert_key}...")
        comment = ask_gemini(client, full_prompt)
        
        # build_page.py側のHTML表示互換性を保つため、JSON構造を維持してpattern_bへ格納
        results[expert_key] = comment
        
        # 分速5回制限を100%安全に回避するウエイト（3回しか叩かないのでこれでも超安全です）
        print("    Waiting 15 seconds to respect Gemini API rate limits...")
        time.sleep(15)

    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n🎉 SUCCESS: Saved 3-expert AI intelligence to {output_json_path}")

if __name__ == '__main__':
    main()
