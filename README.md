# DeltaForceHUD

> **OpenAI Build Week 2026 submission.** DeltaForceHUD is a local OCR overlay that reads *only your own screen* to show real-time asset gain/loss for extraction-shooter streamers — no game memory access, no network modification, nothing an anti-cheat would flag. Built with a Human + Claude + Codex loop: Claude writes the spec/instruction doc, Codex (GPT‑5.6) implements, Claude reviews the diff, the human approves and commits.

## Try it without the game (for judges)

You do **not** need Delta Force to verify the tool works:

1. Install deps and start the server (see セットアップ概要 / 起動 below).
2. Open `http://localhost:8765/health` → confirms the server and OCR loop are alive.
3. Open `http://localhost:8765/setup` → the setup wizard; pick a capture device and draw the OCR region in the browser, no code needed.
4. `GET http://localhost:8765/ocr_test` → runs OCR on the current frame and returns the parsed value, so you can confirm the read path end‑to‑end against any screen.
5. `http://localhost:8765/log` → session history + "cut here" segment tracking (the feature built during Build Week).

**How AI was used:** design/review by Claude, implementation by Codex on GPT‑5.6. During the "cut / segment" feature, Claude's diff review caught a real bug — the error‑path HTTP status did not match the front‑end's branching — and a follow‑up instruction doc had Codex fix it. Human role = final approval + commit only.

---

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

## 連絡先・不具合報告

- 不具合報告: [GitHub Issues](https://github.com/factorysamuraispirits-png/DeltaForceHUD/issues)
- お問い合わせ: X（Twitter） [@mochiya888](https://x.com/mochiya888) / Factory-mo 公式サイトのお問い合わせフォーム

## 利用上の注意・免責

本ツールは自己責任でご利用ください。使用により生じたいかなる損害についても製作者は責任を負いません。
本ツールは自身のPC画面のみをOCR対象とし、ゲームメモリへのアクセスや通信の改変は一切行いません。
アンチチート（ACE等）が画面キャプチャ系ツールを誤検知する可能性があります。利用は各自の判断でお願いします。

## ライセンス・再配布について

配布元は Factory-mo（本リポジトリ／公式サイト）のみとします。無断での二次配布・改変版の配布を禁止します。
個人的な改造・学習目的での改変は歓迎します（ただし改変版の再配布は不可）。
本ソースを参考に別作品を作る場合は、元ネタが Factory-mo（もちや。。）である旨の記載をお願いします。

© 2026 Factory-mo（もちや。。）
