# Sentinel-1 Tank Monitor

Google Earth Engineを使用してSentinel-1 SARデータで石油タンクの時系列分析を行うPythonスクリプトです。

## 🚨 機能の責務分担 (重要) 🚨

このシステムは、処理を以下の2つのステップに分けて設計されています。

1. **データ取得レイヤー (`gee.py`)**: センサーから生データ (RAW SAR値) を取得し、時系列データCSVを生成します。**この段階では、比率計算や変化点検出は行いません。**
2. **データ加工・可視化レイヤー (`plot_tanks.py`)**: `gee.py` から取得したRAWデータCSVを読み込み、比率計算や日次平均化などの高度な加工を行い、最終的なプロット画像や集計結果を生成します。

## 特徴

- Sentinel-1 SARデータを使用した石油タンクの液面レベル監視
- 差分更新機能（6日周期での定期実行推奨）
- 拡張可能なタンクデータ構造（地名_番号形式のID）
- CSV出力（tank_id, date, datetime_utc, vv, vh, angle）

## インストール

1. Python 3.8 以上をインストール
2. 必要なパッケージをインストール:
   ```bash
   pip install earthengine-api pandas matplotlib
   ```

3. Google Earth Engine の認証:
   ```bash
   python -c 'import ee; ee.Authenticate()'
   ```
   > **認証の仕組み**: `ee.Authenticate()` はブラウザで OAuth 認証を行い、ローカルに認証情報を保存します。以降の実行では保存された認証情報が自動的に使用されます。プロジェクト ID さえ指定すればスクリプト単独で動作可能です。

## 使用方法

### 1. データ取得（`gee.py` の実行）
**【目的】** センサーから生データ (RAW SAR値) を取得し、時系列データCSVを生成する。
```bash
python gee.py --project YOUR_PROJECT_ID
```

### 2. データ加工・可視化（`plot_tanks.py` の実行）
**【目的】** 取得したCSVを読み込み、比率計算や平均化などの高度なデータ加工を経て、最終的な分析結果（PNG画像など）を生成する。
```bash
python plot_tanks.py --data-dir data --output-dir plots --plot-region-average
```

### オプション
- `--project`: Google CloudプロジェクトID（必須）
- `--output-csv`: 出力CSVファイル名またはパスのベース（デフォルト: tank_timeseries.csv）
- `--output-dir`: 地域別CSVを出力するディレクトリ（デフォルト: `.`）
- `--region`: 処理対象の地域を絞り込む（例: `shibushi`, `tomakomai`）
- `--max-tanks`: 処理対象とする最大タンク数（デフォルト: 全タンク）
- `--tanks`: 処理対象のタンクIDを具体的に指定する（例: `shibushi_01 shibushi_02`）
- `--update`: 更新モード（既存CSVに新規データを追加）
- `--verbose`: 詳細出力

### 例
```bash
# 全地域のタンクを地域別CSVに出力
python gee.py --project your-project-id --output-dir data --verbose

# --- 地域指定での実行例 ---
# shibushi地域のみ処理
python gee.py --project your-project-id --region shibushi --output-dir data --verbose

# 特定のタンクIDのみ処理
python gee.py --project your-project-id --tanks shibushi_01 shibushi_02 --output-dir data

# --- 更新モードでの実行例 ---
# shibushi地域に対して、前回データ以降の差分のみ更新
python gee.py --project your-project-id --region shibushi --output-dir data --update
```

## ファイル命名規則

地域別CSVファイルは以下の形式で出力されます：
- `{region}_tank_timeseries.csv`
  - 例: `shibushi_tank_timeseries.csv`

## データ可視化

CSVデータをグラフで可視化するツールが利用可能です。

### インストール（追加パッケージ）
```bash
pip install pandas matplotlib
```

### 全タンク時系列グラフ
```bash
python plot_tanks.py --csv tank_timeseries.csv --all-tanks-output all_tanks.png
```

### 地域別平均グラフ
```bash
python plot_tanks.py --csv tank_timeseries.csv --shibushi-output shibushi_avg.png
```

## 地域別CSV対応プロット

`data` ディレクトリに地域別CSVを格納している場合、次のように実行します。

### 各地域のプロットを一括生成
```bash
python src/plot_tanks.py --data-dir data --output-dir plots
```

### 特定地域のみを生成
```bash
python src/plot_tanks.py --data-dir data --region shibushi --output-dir plots
```

### 全地域の平均比較プロット
```bash
python src/plot_tanks.py --data-dir data --output-dir plots --plot-region-averages-comparison
```

### 全地域の全タンク平均プロット
```bash
python src/plot_tanks.py --data-dir data --output-dir plots --combined-average-output plots/all_regions_combined_average.png
```

### hokkaidoを除く全地域平均プロット
```bash
python src/plot_tanks.py --data-dir data --output-dir plots --non-hokkaido-average-output plots/all_regions_non_hokkaido_average.png
```

### 両方のプロットを生成
```bash
python plot_tanks.py --csv tank_timeseries.csv
```

### インタラクティブ表示
```bash
python plot_tanks.py --csv tank_timeseries.csv --show-plots
```

> `--shibushi-output` を指定した場合は、`shibushi` 地域平均プロットのみが出力されます。 `--all-tanks-output` も同時に指定すると、両方のプロットが生成されます。

### 特徴
- **全タンクプロット**: 各タンクの時系列をグリッド状に表示
- **地域平均プロット**: 上段に平均時系列、下段に個別タンクの推移
- **PNG出力**: 高解像度での保存が可能

## データ構造

### CSV出力形式
```csv
tank_id,date,datetime_utc,vv,vh,angle
shibushi_01,2023-01-01,1672579200000,-3.2,2.5,45.0
shibushi_01,2023-01-07,1672579200000,-3.2,2.5,45.0
shibushi_02,2023-01-01,1672579200000,0.92,2.5,45.0
```

### 地域別CSV出力
地域別出力では、`--output-dir` と `--region` を使います。たとえば `shibushi` 地域を処理すると、`data/shibushi_tank_timeseries.csv` を生成します。

- 全地域を処理すると、各地域ごとに `region_tank_timeseries.csv` が生成されます。
- `--region` を指定すると、その地域だけ処理します。
- 地域名はタンクIDの先頭（`shibushi_`, `tomakomai_`, `hokkaido_` など）で判定します。

### タンクデータ拡張

`gee.py` の`TANK_DATA`リストに新しいタンクを追加:

```python
TANK_DATA = [
    # 既存の志布志基地タンク
    {"id": "shibushi_01", "lon": 131.02403931993155, "lat": 31.37539899202453},
    # ... 他のshibushiタンク ...

    # 新しい基地のタンクを追加
    {"id": "tomakomai_01", "lon": 141.123456, "lat": 42.654321},
    {"id": "sendai_01", "lon": 140.987654, "lat": 38.123456},
    # 他の179個のタンクを同様に追加可能
]
```

## 定期実行設定

### Windowsタスクスケジューラ
1. タスクスケジューラを開く
2. 「タスクの作成」を選択
3. トリガーを「毎日」に設定（6日間隔）
4. アクションを「プログラムの開始」に設定:
   - プログラム: `python.exe`
   - 引数: `gee.py --project YOUR_PROJECT_ID --update --verbose`
   - 開始: `C:\path\to\your\script\directory`

### Linux/Mac cron
```bash
# crontab -e
# 毎週月曜日に実行（例）
0 9 * * 1 cd /path/to/script && python gee.py --project YOUR_PROJECT_ID --update
```

## 技術仕様

- **データソース**: Sentinel-1 GRD (IWモード, VV/VH偏波)
- **軌道**: 降下軌道のみ
- **集計**: サーバーサイド集計でパフォーマンス最適化
- **出力**: CSV形式（tank_id, date, datetime_utc, vv, vh, angle）

## 拡張方法

1. 新しい基地のタンク座標を`TANK_DATA`に追加
2. IDは`地名_番号`形式を使用
3. 座標はWGS84経緯度を使用
4. `--tanks`オプションで特定のタンクをテスト

## 注意事項

- Google Earth Engine のプロジェクト権限が必要です
- Sentinel-1 データの可用性により、データ取得に時間がかかる場合があります

## GitHub Actions での実行

GitHub Actions で自動実行する場合、サービスアカウントを使用した認証が必要です。

### 1. Google Cloud Service Account の作成
1. Google Cloud Console でサービスアカウントを作成
2. Earth Engine API を有効化
3. サービスアカウントに Earth Engine の権限を付与

### 2. サービスアカウントキーの作成
```bash
# サービスアカウントキーをJSON形式でダウンロード
```

### 3. GitHub Secrets への登録
GitHubリポジトリの Settings > Secrets and variables > Actions で以下を登録:
- `GEE_SERVICE_ACCOUNT_KEY`: サービスアカウントキーのJSON内容
- `GEE_PROJECT_ID`: Google Cloud プロジェクト ID

> **セキュリティについて**: GitHub Secrets は暗号化されて保存され、リポジトリのコードやログに表示されません。リポジトリを公開しても認証情報は安全に保護されます。

### 4. GitHub Actions ワークフロー例
```yaml
name: Tank Monitor Update
on:
  schedule:
    - cron: '0 9 * * 1'  # 毎週月曜日 9 時
  workflow_dispatch:

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install earthengine-api pandas matplotlib
      - name: Authenticate to Earth Engine
        run: |
          echo "${{ secrets.GEE_SERVICE_ACCOUNT_KEY }}" > service_account_key.json
          python -c "
          import ee
          import json
          with open('service_account_key.json') as f:
              key_data = json.load(f)
          credentials = ee.ServiceAccountCredentials(key_data['client_email'], 'service_account_key.json')
          ee.Initialize(credentials, project='${{ secrets.GEE_PROJECT_ID }}')
          print('Earth Engine authenticated successfully')
          "
      - name: Run tank monitor
        run: |
          python src/gee.py --project ${{ secrets.GEE_PROJECT_ID }} --update --verbose
      - name: Generate plots
        run: |
          python src/plot_tanks.py --csv tank_timeseries.csv --all-tanks-output all_tanks.png --shibushi-output shibushi_avg.png
      - name: Commit and push changes
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add tank_timeseries.csv *.png
          git commit -m "Update tank monitoring data [$(date +'%Y-%m-%d')]" || echo "No changes to commit"
          git push
```