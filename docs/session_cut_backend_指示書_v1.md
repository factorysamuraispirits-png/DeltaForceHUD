# DeltaForceHUD: セッション区切り(/cut, /current_segment) backend実装 指示書 v1

## 背景・現状の問題

`sessions.html`（Git管理下版）には「ここで区切る」ボタンと区間損益表示UIが既に実装済みだが、
対応するbackend（`main.py`）に `POST /cut` と `GET /current_segment` が存在しない。
そのため本番相当のUIを開くと `current_segment` が404/500になり、区切り機能が動作しない。
Build Week提出前に、この壊れた見た目を解消し、実際に動く機能にする。

## 対象ファイル

- `main.py` のみ変更する。
- `sessions.html` / `obs.html` / `setup.html` は変更しない（既にfrontend実装済みのため）。
- 新規データファイル: `markers.jsonl`（`.gitignore` に既に登録済み、追加登録不要）。

## 呼び出し元・影響範囲（先に確認すること）

- `sessions.html` の `cutHere()` → `POST /cut` を呼ぶ（既存、変更不要）
- `sessions.html` の `loadCurrentSegment()` → `GET /current_segment` を5秒間隔で呼ぶ（既存、変更不要）
- `state` dict（グローバル、OCRループが更新）を読むだけで、OCRループ自体は変更しない
- `SESSION_LOG` / `session_log.jsonl` には触れない（`DELETE /sessions` が既存ログを空にする仕様と衝突させないこと。理由：マーカーはセッションログ削除後も残す設計のため、あえて別ファイルにする）

## 実装仕様

### 1. 定数追加（`SESSION_LOG` 定義の直後あたり）

```python
MARKERS_LOG = os.path.join(BASE_DIR, "markers.jsonl")
```

### 2. `POST /cut`

- `state["value"]` が `0` または未取得（falsy）の場合は何もマークせず、
  `{"ok": False, "message": "残高が未取得のため区切れません"}` を返す（HTTPステータスは200のままでよい。frontendは`res.ok`ではなく`d.message`を見てalertする実装のため、既存フロントの挙動に合わせる。ただし`res.ok`条件も壊さないよう通常の200で返すこと）
- 取得済みの場合、`markers.jsonl` に1行追記する（自己完結: そのマーカー自身の残高を持つ）

```python
{"t": "<datetime.now().strftime('%Y-%m-%dT%H:%M:%S')>", "balance": <state["value"]>}
```

- 追記は `SESSION_LOG` の既存書き込み処理と同じtry/exceptパターン（失敗しても例外を握りつぶしてよいが、`ok: False`を返すこと）
- 成功時は `{"ok": True, "balance": <値>, "t": <値>}` を返す

### 3. `GET /current_segment`

- `markers.jsonl` の**最後の1行**だけを読む（全件読み込みでよい、ファイルサイズは小さい想定。ただし存在しない場合は`FileNotFoundError`を握りつぶして「マーカーなし」扱い）
- `current_balance = state["value"] if state["value"] else None`
- 分岐:
  - マーカーが存在し、かつ `current_balance is not None` → `{"net": current_balance - marker["balance"], "current_balance": current_balance}`
  - マーカーが存在しないが `current_balance is not None` → `{"net": None, "current_balance": current_balance}`
  - `current_balance is None` → `{"net": None, "current_balance": None}`
- 例外発生時は握りつぶして `{"net": None, "current_balance": None}` を返す（frontendの`catch`分岐と重複してもよい。backend側でも500を返さないことが目的）

## 明確な停止条件（ここで必ず一度止めて報告する）

- 上記の仕様通りに実装できない技術的理由がある場合
- `state` の初期値や型が本指示書の前提（`value`のデフォルトは`0`）と食い違っていた場合
- `main.py` 内に同名の変数・関数・エンドポイントが既に存在した場合（衝突）
- 実装完了後、`git add` や `git commit` は絶対に行わない（人間の承認後に別途行う）

## 検証手順（実装後、必ず実施してdiffと結果を持ち帰ること）

1. `git diff --stat -- main.py` で変更行数を提示（他ファイルへの意図しない変更がないことも確認）
2. ローカルでサーバー起動: `start.bat`（またはvenv経由で `python main.py`）
3. 以下をcurlまたはブラウザで実行し、結果を貼り付ける:
   ```
   curl http://localhost:8765/current_segment
   # → {"net": null または数値, "current_balance": null または数値}
   curl -X POST http://localhost:8765/cut
   # → {"ok": true, "balance": ..., "t": "..."} または {"ok": false, "message": "..."}
   curl http://localhost:8765/current_segment
   # → cut後は net が 0 付近になっているはず（同じ残高からの差分なので）
   ```
4. `http://localhost:8765/log` をブラウザで開き、「ここで区切る」ボタンを押して画面上の区間損益表示が更新されることを目視確認したスクリーンショットまたは説明を持ち帰る
5. `markers.jsonl` の中身を1行貼り付け、想定した形式（`t`, `balance`のみのJSON1行）になっているか確認

## 出力形式

- 完全なbefore/after diff（`git diff -- main.py`、`...`のような省略は禁止）
- 上記検証手順1〜5の実行結果（テキストまたはスクリーンショット）
- 何も自動でcommitしないこと
