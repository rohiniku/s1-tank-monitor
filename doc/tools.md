# ツール設計と使い方

このドキュメントでは、ローカル実行用の主要スクリプトとその設計意図、CLIオプション、実行例をまとめています。

## 1. 全体フロー

`run.bash` を使うと以下をまとめて実行します。

1. `src/gee.py`: Google Earth Engine から Sentinel-1 SAR データを取得し、地域別 CSV を更新する
2. `src/plot_tanks.py`: CSV を読み込み、プロット画像を生成する
3. `src/ai_reporter.py`: AI レポートを生成し、`reports/` に JSON を出力する
4. `src/build_page.py`: 最新の JSON と画像を組み合わせて `index.html` を生成する

## 2. スクリプト一覧

### `run.bash`

- ローカルまたは CI でのパイプライン実行エントリポイント
- `src/gee.py` → `src/plot_tanks.py` → `src/ai_reporter.py` → `src/build_page.py` の順で実行
- 出力例:
  - `data/` (CSV)
  - `plots/` (PNG)
  - `reports/` (JSON)
  - `index.html`

### `src/gee.py`

- Google Earth Engine から Sentinel-1 データを取得する
- 出力先: `data/`
- 主要オプション:
  - `--project`: GEE プロジェクト ID
  - `--output-dir`: CSV 出力ディレクトリ
  - `--region`: 処理する地域名
  - `--update`: 既存 CSV へ差分更新

### `src/plot_tanks.py`

- `data/` 配下の CSV を読み込み、PNG を生成する
- 主要オプション:
  - `--data-dir`: CSV 入力ディレクトリ
  - `--output-dir`: PNG 出力ディレクトリ
  - `--region`: 地域を指定して出力対象を絞る

### `src/ai_reporter.py`

- 最新の CSV データを読み込み、Gemini API を呼び出して AI レポートを生成する
- 既定出力: `reports/ai_report_<timestamp>.json`
- 主要オプション:
  - `--data-dir`: CSV 入力ディレクトリ
  - `--output-dir`: JSON 出力ディレクトリ
  - `--no-timestamp`: 上書き用に `ai_report.json` を生成

### `src/build_page.py`

- 最新レポート JSON と PNG を組み合わせ、静的 HTML を生成する
- 主要オプション:
  - `--input-dir` / `--reports-dir`: レポート JSON のあるディレクトリ
  - `--plots-dir`: PNG ディレクトリ
  - `--artifacts-dir` / `--output-dir`: HTML 出力先

## 3. 実行例

### 1) ローカル実行フルパイプライン

```bash
./run.bash
```

### 2) CSV 取得のみ

```bash
python src/gee.py --project YOUR_PROJECT_ID --output-dir data --verbose --update
```

### 3) プロット生成のみ

```bash
python src/plot_tanks.py --data-dir data --output-dir plots
```

### 4) AI レポート生成のみ

```bash
python src/ai_reporter.py --data-dir data --output-dir reports
```

### 5) HTML 生成のみ

```bash
python src/build_page.py --input-dir reports --plots-dir plots --artifacts-dir .
```

## 4. ファイル構成

- `data/`: 地域別 CSV
- `plots/`: 生成された PNG
- `reports/`: 生成された JSON
- `index.html`: GitHub Pages で公開するダッシュボード

## 5. 追加ノート

- `ai_reporter.py` の `--no-timestamp` を使うと、毎回同じファイル名 (`ai_report.json`) で上書きできます。
- GitHub Pages へ公開する場合は、`index.html` と `plots/` を `gh-pages` ブランチに含めれば OK です。
