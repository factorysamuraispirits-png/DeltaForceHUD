@echo off
chcp 65001 > nul
cd /d "%~dp0"

rem ── Python 確認 ──────────────────────────────────
python --version > nul 2>&1
if errorlevel 1 (
  echo [エラー] Python が見つかりません
  echo https://www.python.org/downloads/ からインストールしてください
  pause & exit /b 1
)

rem ── Tesseract 確認 ───────────────────────────────
if not exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
  echo [警告] Tesseract が見つかりません
  echo https://github.com/UB-Mannheim/tesseract/wiki からインストールしてください
  pause
)

rem ── venv 作成（初回のみ）────────────────────────
if not exist venv\Scripts\activate.bat (
  echo 初回セットアップ中... 仮想環境を作成しています
  python -m venv venv
  if errorlevel 1 (
    echo [エラー] venv の作成に失敗しました
    pause & exit /b 1
  )
)

call venv\Scripts\activate

rem ── 依存パッケージのインストール ────────────────
echo 依存パッケージを確認中...
pip install -q -r requirements.txt
if errorlevel 1 (
  echo [エラー] パッケージのインストールに失敗しました
  echo ネット接続を確認してから再試行してください
  pause & exit /b 1
)

echo.
echo  Delta Force HUD v2.0
echo  設定画面      : http://localhost:8765/setup
echo  セッション履歴 : http://localhost:8765/log
echo  OBS 用 URL   : http://localhost:8765/
echo  終了          : Ctrl+C
echo.
python main.py

rem ここに来たら main.py が終了している
echo.
echo サーバーが終了しました。
pause
