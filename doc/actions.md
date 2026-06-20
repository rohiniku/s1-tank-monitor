# GitHub Actions 設定

このドキュメントでは、GitHub Actions での定期実行、Earth Engine 認証、gh-pages デプロイについてまとめます。

## 1. 目的

- `run.bash` を定期実行し、最新データとレポートを生成する
- 生成結果を `index.html` と `plots/` を含めて `gh-pages` ブランチにデプロイする

## 2. 現在のワークフロー

ワークフロー実行は以下の順序です。

1. リポジトリを checkout
2. Python 環境をセットアップ
3. 依存パッケージをインストール
4. Google Earth Engine 認証を実行
5. `run.bash` を実行してパイプラインを走らせる
6. 生成物を `gh-pages` ブランチに配置して push

## 3. 必要な GitHub Secrets

- `EARTH_ENGINE_CREDENTIALS`:
  - Google Cloud サービスアカウントの JSON 形式認証情報
  - ワークフロー内で `gcloud auth activate-service-account --key-file=gee_key.json` に渡される
- `GEMINI_API_KEY`:
  - Gemini API のキー

## 4. 動作内容

### 認証

- `gcloud auth activate-service-account --key-file=gee_key.json`
- `GOOGLE_APPLICATION_CREDENTIALS` を環境変数に設定

### 実行順序

1. `src/gee.py` で Earth Engine から CSV を更新
2. `src/plot_tanks.py` で `plots/` PNG を生成
3. `src/ai_reporter.py` で `reports/` JSON を生成
4. `src/build_page.py` で `index.html` を生成
5. `gh-pages` ブランチへ `data/`, `plots/`, `index.html` をデプロイ

## 5. ワークフローの改善点

- HTML 生成はワークフロー内ではなく `src/build_page.py` が担当するように整理済み
- `run.bash` は必要な全処理を順番に呼び出すエントリポイントとして機能する
- `data/`, `plots/`, `reports/` の明確な責務分離により、CI のトラブルシューティングが容易になる

## 6. 設定サンプル

```yaml
name: 🛰️ Sentinel-1 Tank Monitor Automatic Run

on:
  schedule:
    - cron: '0 2 * * *'
  workflow_dispatch:

jobs:
  run-monitor:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.10'
          cache: 'pip'
      - name: Install dependencies
        run: |
          python3 -m pip install --upgrade pip
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
      - name: Authenticate Google Earth Engine
        env:
          GEE_KEY: ${{ secrets.EARTH_ENGINE_CREDENTIALS }}
        run: |
          mkdir -p ~/.config/earthengine
          printf '%s' "$GEE_KEY" > gee_key.json
          gcloud auth activate-service-account --key-file=gee_key.json
          echo "GOOGLE_APPLICATION_CREDENTIALS=$(pwd)/gee_key.json" >> $GITHUB_ENV
      - name: Run Main Pipeline via run.bash
        env:
          GEE_PROJECT_ID: ${{ fromJson(secrets.EARTH_ENGINE_CREDENTIALS).project_id }}
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: |
          chmod +x ./run.bash
          ./run.bash
      - name: Deploy directly to GitHub Pages (gh-pages branch)
        run: |
          git config --global user.name "github-actions[bot]"
          git config --global user.email "github-actions[bot]@github.com"
          mkdir -p /tmp/artifacts
          cp -r data plots index.html /tmp/artifacts/
          rm -f gee_key.json
          git fetch origin
          git checkout --orphan gh-pages
          git rm -rf .
          cp -r /tmp/artifacts/* .
          git add .
          if ! git diff --cached --quiet; then
            git commit -m "🔄 [Automated Web Deploy] Update data and dashboard [$(date +'%Y-%m-%d')]"
            git push origin gh-pages --force
          else
            echo "No changes. Skipping."
          fi
```

## 7. 使い方のヒント

- まずはローカルで `./run.bash` を実行してパイプラインが完走することを確認してください。
- `run.bash` が動くようになったら、Actions でも同じ `run.bash` を使って動作を再現します。
- GitHub Actions の実行ログから失敗箇所を追跡する場合は、`run.bash` の各ステップ出力を参照してください。
