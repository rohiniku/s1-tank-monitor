# 1. 仮想環境のアクティベート（初期設定）
Write-Host "--- 1. 仮想環境をアクティベートします ---" -ForegroundColor Yellow
& .\venv\Scripts\activate

# 2. 最初のPythonスクリプト実行とエラーチェック（最も重要）
Write-Host "--- 2. gee.py の実行を開始します ---" -ForegroundColor Yellow
try {
    # 実行コマンドを括弧 [] で囲み、失敗した場合に例外を発生させる
    & python src/gee.py --project <YOUR_PROJECT_ID> --output-dir data --verbose --update
    
    # ★★★ 成功した場合のみここが実行される ★★★
    Write-Host "SUCCESS: gee.py の実行が正常に完了しました。" -ForegroundColor Green
}
catch {
    # エラー発生時（429エラーやコードエラーなど）
    Write-Host "ERROR: gee.py の実行中にエラーが発生しました。処理を中断します。" -ForegroundColor Red
    Write-Host "詳細なエラーメッセージ: $($_.Exception.Message)" -ForegroundColor Red
    
    # 続行を意図的にスキップするために、処理を終了する
    Write-Host "!!! 後続のplot_tanks.pyの実行はスキップします !!!" -ForegroundColor Red
    exit 1 # 終了コード1を返して、パイプラインを強制終了させる
}

# 3. 後続のPythonスクリプト実行（前ステップが成功した場合のみ実行される場所）
# PowerShellのtry/catchの外側にあるため、前のステップでexit 1が呼ばれていなければ到達する。
Write-Host "--- 3. plot_tanks.py の実行を開始します ---" -ForegroundColor Yellow
try {
    & python src/plot_tanks.py --data-dir data --output-dir plots
    Write-Host "SUCCESS: plot_tanks.py の実行が正常に完了しました。" -ForegroundColor Green
}
catch {
    Write-Host "WARNING: plot_tanks.py の実行中にエラーが発生しました。" -ForegroundColor Yellow
    Write-Host "詳細なエラーメッセージ: $($_.Exception.Message)" -ForegroundColor Yellow
}

# 終了処理（任意）
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "全処理が完了しました。" -ForegroundColor Cyan
