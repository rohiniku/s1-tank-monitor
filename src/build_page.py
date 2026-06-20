import os
import json
import argparse
from datetime import datetime
import zoneinfo

# =======================================================================
# 💡 あなたが徹底的に並び順を整えた「意味的な画像配列仕様（マクロ➔ミクロのストーリー）」
# =======================================================================
IMAGE_ORDER = [
    "region_averages_comparison.png",
    "all_regions_combined_average.png",
    "tomakomai_average.png",
    "tomakomai_all_tanks.png",
    "hokkaido_average.png",
    "hokkaido_all_tanks.png",
    "mutsu_average.png",
    "mutsu_all_tanks.png",
    "fukui_average.png",
    "fukui_all_tanks.png",
    "shibushi_average.png",
    "shibushi_all_tanks.png",
]

EXPERT_NAMES = {
    "sar_expert": "🛰️ 1. SARレーダー物理・波形解析室",
    "fact_checker": "📰 2. 国際情報ファクトチェッカー (報道 vs リアル計測値)",
    "security_analyst": "🛢️ 3. 国家安全保障・エネルギー有事アナリスト"
}


def generate_html(json_path, plots_dir='plots', target_dir=None):
    """画像とAIの構造化JSONをガッチャンコして、完全な静的index.htmlをビルドする"""
    
    # 1. 日本時間（JST）の動的タイムスタンプを生成（ローカルでもActionsでも完全に同期）
    jst = zoneinfo.ZoneInfo("Asia/Tokyo")
    updated_at = datetime.now(jst).strftime("%Y-%m-%d %H:%M (JST)")
    
    # 2. AIのJSONデータを読み込んで、無骨で美しいカード型HTMLに展開する
    ai_section_html = ""
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                ai_data = json.load(f)
                
            if ai_data:
                ai_section_html += '<div class="ai-container">\n'
                ai_section_html += '  <h2>📑 多角AIインテリジェンス報告 (3人の専門家)</h2>\n'
                ai_section_html += '  <p class="ai-disclaimer">※本レポートは、宇宙からのレーダー波形を自律的に読み解いたAIが、今朝のGoogle検索ニュースとリアルタイムに結合して自動生成した実験用ファクトチェック報告です。</p>\n'
                
                # 3人の専門家をループ
                for expert_key, expert_title in EXPERT_NAMES.items():
                    if expert_key not in ai_data: 
                        continue
                    ai_section_html += f'  <div class="expert-section">\n    <h3>{expert_title}</h3>\n'
                    
                    comment = ai_data[expert_key]
                    
                    ai_section_html += f'    <p style="white-space: pre-line;">{comment}</p>\n'
                    ai_section_html += '  </div>\n'
                ai_section_html += '</div>\n'
        except Exception as e:
            ai_section_html = f'<div class="ai-container"><p style="color:red;">AIレポート読み込みエラー: {e}</p></div>'

    # 3. 事前準備されたCSSとヘッダーをガッチャンコする（Aパート）
    # 💡 あなたの「ズームやスクロールの支配権」を絶対に邪魔しない、引き算の極限プレーンデザイン
    html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Sentinel-1 Tank Monitor Dashboard</title>
  <style>
    /* 1. 💡 画面全体の横揺れ（横スクロール）を物理的に完全シャットアウト */
    html, body {{
      margin: 0;
      padding: 0;
      max-width: 100vw;
      overflow-x: hidden; /* これで横方向へのハミ出しを強制カットします */
    }}
    body {{
      font-family: system-ui, -apple-system, sans-serif; 
      padding: 1.2rem; /* スマホの画面端にジャストフィットする絶妙な余白 */
      color: #2c3e50; 
      background: #fff; 
      line-height: 1.6;
    }}
    h1 {{
      font-size: 1.8rem; /* スマホでも見やすい大きさに少しコンパクト化 */
      margin-top: 0;
      margin-bottom: 0.2rem; 
      color: #1a252f;
    }}
    
    /* 2. 💡 【真犯人の撃破】長いファイル名を強制的に自動改行させる */
    h2 {{
      font-size: 1.05rem; 
      margin-top: 2rem; 
      margin-bottom: 0.8rem; 
      color: #34495e; 
      border-left: 4px solid #2c3e50; 
      padding-left: 0.5rem;
      /* 👇 この3つを揃えることで、どんなに長いファイル名でも自動で折れ曲がります */
      word-wrap: break-word;       
      overflow-wrap: break-word;   
      word-break: break-all;       
    }}
    
    .meta {{ color: #7f8c8d; font-size: 0.85rem; margin-bottom: 1.5rem; font-weight: 500; }}
    
    /* 3. 💡 画像（img）がスマホ幅に100%びっちり張り付くフルパディング設計 */
    img {{
      display: block;
      width: 100%;
      max-width: 100%; 
      height: auto; 
      border: 1px solid #e2e8f0; 
      border-radius: 4px; 
      margin-bottom: 0.5rem; 
      background: #f8fafc;
      box-sizing: border-box; /* 枠線がハミ出さないための魔法のプロパティ */
    }}
    hr {{ margin: 2rem 0; border: 0; border-top: 1px solid #edf2f7; }}
    
    /* AIコンテナも横幅ぴったりにフィット */
    .ai-container {{
      background: #f8fafc; 
      border: 1px solid #e2e8f0; 
      border-radius: 8px; 
      padding: 1.2rem; 
      margin-bottom: 2rem;
      box-sizing: border-box;
    }}
    .ai-disclaimer {{ color: #64748b; font-size: 0.8rem; margin-top: -0.5rem; margin-bottom: 1.2rem; }}
    .expert-section {{ margin-bottom: 1.5rem; padding-bottom: 1.2rem; border-bottom: 1px dashed #cbd5e1; }}
    .expert-section:last-child {{ border-bottom: none; margin-bottom: 0; padding-bottom: 0; }}
    .expert-section h3 {{ font-size: 1.05rem; margin-top: 0; margin-bottom: 0.6rem; color: #0f172a; }}
    
    .chart-instruction {{ font-weight: 600; color: #475569; margin-top: 1.5rem; font-size: 0.95rem; }}
    .chart-sub {{ font-size: 0.8rem; color: #94a3b8; margin-top: -0.6rem; margin-bottom: 1.5rem; }}
  </style>

</head>
<body>
  <h1>🛰️ Sentinel-1 Tank Monitor</h1>
  <div class="meta">最終更新日時: {updated_at}</div>
  <p>このダッシュボードは、Sentinel-1衛星のSARレーダー波形をリアルタイムに解析し、タンクの液面変化を監視する実験的なプロジェクトです。以下のチャートとAIレポートは、最新の観測データとGoogle検索からの情報を組み合わせて生成されたものです。</p>
  <p>OSSプロジェクトのGitHubリポジトリ: <a href="https://github.com/rohiniku/s1-tank-monitor" target="_blank">https://github.com/rohiniku/s1-tank-monitor</a></p>
  
  {ai_section_html}
  
  <p class="chart-instruction">📊 最新の幾何アライメント済・移動平均観測チャート</p>
  <p class="chart-sub">（※画像上でダブルタップまたはピンチアウトすることで、ブラウザ標準の滑らかなズーム操作が可能です）</p>
  <hr>
"""

    # 4. あなたが定義した画像順の通りに、<img>タグを数珠つなぎに直列結合（Bパート）
    for name in IMAGE_ORDER:
        # 画像の存在確認は実際のプロット出力ディレクトリで行う
        img_check_path = os.path.join(plots_dir, name) if plots_dir else f"plots/{name}"

        if os.path.exists(img_check_path) or plots_dir is None:
            html_content += f'  <h2>{name}</h2>\n'
            html_content += f'  <img src="plots/{name}" alt="{name}">\n'
            html_content += f'  <hr>\n'

    html_content += """</body>
</html>
"""

    # 5. 指定された出力先（またはカレントディレクトリ）へ index.html を一括出荷！
    out_target = os.path.join(target_dir, "index.html") if target_dir else "index.html"
    with open(out_target, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"SUCCESS: Generated 100% complete static web page at {out_target}")

def main():
    parser = argparse.ArgumentParser()
    # 入力レポート群のディレクトリ（デフォルトは "reports"）と、出力アーティファクト領域を指定
    parser.add_argument('--input-dir', '--reports-dir', default='reports', help='Directory containing report JSON files or path to a specific JSON file')
    parser.add_argument('--plots-dir', default='plots', help='Directory containing plot PNG files')
    parser.add_argument('--artifacts-dir', '--output-dir', default=None, help='Directory to output index.html')
    args = parser.parse_args()

    # input-dir がディレクトリなら最新の .json を自動選択、ファイルパスならそのまま使う
    if args.input_dir and os.path.isdir(args.input_dir):
        json_files = [os.path.join(args.input_dir, f) for f in os.listdir(args.input_dir) if f.lower().endswith('.json')]
        if json_files:
            json_path = max(json_files, key=os.path.getmtime)
        else:
            json_path = os.path.join(args.input_dir, "ai_report.json")
    else:
        json_path = args.input_dir if args.input_dir else "ai_report.json"

    plots_dir = args.plots_dir or 'plots'
    target_dir = args.artifacts_dir if args.artifacts_dir else None
    generate_html(json_path, plots_dir=plots_dir, target_dir=target_dir)

if __name__ == '__main__':
    main()
