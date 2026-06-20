# Sentinel-1 Tank Monitor

Sentinel-1 Tank Monitor は、Google Earth Engine と Sentinel-1 SAR データを使って日本国内の石油タンク液面変化を監視し、自動生成ダッシュボードを GitHub Pages に公開する OSS パイプラインです。

- Live dashboard: https://rohiniku.github.io/s1-tank-monitor/
- ドキュメント:
  - [ツール設計と実行方法](doc/tools.md)
  - [GitHub Actions 設定](doc/actions.md)

## 何をするものか

このリポジトリは次の処理を自動化します。

1. Sentinel-1 SAR データを Earth Engine から取得して CSV を生成
2. CSV を加工して可視化用 PNG を出力
3. AI レポートを生成して JSON に保存
4. 生成結果を HTML に組み込み、Pages 用のダッシュボードを作成

## 使い方の概略

ローカルでは `run.bash` を使うと一連の処理をまとめて実行できます。

```bash
./run.bash
```

詳細なツール設計と CLI オプションは `doc/tools.md` を参照してください。

## GitHub Actions

このリポジトリは GitHub Actions で定期実行と gh-pages デプロイを行います。ワークフローの説明は `doc/actions.md` をご覧ください。

## ライセンス

このプロジェクトは [MIT License](LICENSE) です。
