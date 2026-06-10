# DeltaForceHUD

DeltaForceHUD は、ローカルPC上で動作するOBS向けHUD補助ツールです。FastAPIでローカルサーバーを起動し、OBSには `http://localhost:8765/` を表示元として登録します。

## Git管理するもの

- `main.py`
- `obs.html`
- `sessions.html`
- `setup.html`
- `requirements.txt`
- `start.bat`
- `assets/logo.png`
- ドキュメント類

## Git管理しないもの

- Python仮想環境: `venv/`
- 個人設定: `settings.json`
- 実行ログ: `session_log.jsonl`
- OCR調査ログ: `lobby_debug.csv`
- Tesseract学習データ: `tessdata/*.traineddata`
- 録画、キャプチャ、zipなどの生成物

## セットアップ概要

```powershell
python -m venv venv
.\venv\Scripts\pip install -r requirements.txt
```

Tesseract本体は別途インストールが必要です。日本語OCR用の `.traineddata` は `tessdata/` に配置しますが、ファイルサイズが大きいためGitには入れません。

## 起動

```powershell
.\start.bat
```

起動後、ブラウザまたはOBSから以下を開きます。

- 設定画面: `http://localhost:8765/setup`
- セッション履歴: `http://localhost:8765/log`
- OBS用URL: `http://localhost:8765/`

## 注意

このリポジトリには実ログ、個人設定、秘密情報を入れないでください。初回コミット前に `git status --short` で追跡対象を確認し、gitleaks / Semgrep などのローカル無料スキャンを通してください。
