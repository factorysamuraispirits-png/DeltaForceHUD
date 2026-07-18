# DeltaForceHUD: /cut 失敗時のHTTPステータス修正 指示書 v2（v1の追加修正）

## 背景

v1指示書で実装した `POST /cut` は、失敗時（残高未取得・保存失敗）も常にHTTP 200を返す仕様にしていた。
しかし `sessions.html` の `cutHere()` は `res.ok`（HTTPステータスが2xxかどうか）だけを見て
成功/失敗を分岐しており、`{"ok": false, ...}` のJSON本体は見ていない。
そのため実際にOCR未取得時に「ここで区切る」を押しても、画面には何のエラーも出ず無反応に見える。
これはv1指示書側の指定ミス（Codexの実装は指示通りで正しい）。今回はこの1点だけを直す。

## 対象ファイル

- `main.py` の `POST /cut` のみ変更する。
- `sessions.html` は変更不要（`res.json()`はステータスコードに関わらず本文をパースできるため、
  フロント側は無改修でそのまま動く）。

## 呼び出し元・影響範囲

- 呼び出し元は `sessions.html` の `cutHere()` のみ（v1指示書の調査時と同じ）。
- ステータスコードを見ている他のコード・スクリプトは現状存在しない（POST /cut を直接叩く外部連携なし）。
- 成功時のレスポンス（`{"ok": true, ...}`, 200）は変更しない。

## 実装仕様

`from fastapi.responses import HTMLResponse, Response` の行に `JSONResponse` を追加。

```python
from fastapi.responses import HTMLResponse, Response, JSONResponse
```

`POST /cut` の失敗系レスポンスを以下のように変更する（成功系はそのまま）。

- 残高未取得（`if not balance:`）→ `JSONResponse(status_code=400, content={"ok": False, "message": "残高が未取得のため区切れません"})`
- 保存失敗（`except Exception:`）→ `JSONResponse(status_code=500, content={"ok": False, "message": "区切りの保存に失敗しました"})`

参考実装イメージ（コピペ推奨ではなく仕様の説明。実際のコードスタイルは既存箇所に合わせること）：

```python
@app.post("/cut")
def cut():
    balance = state["value"]
    if not balance:
        return JSONResponse(status_code=400, content={"ok": False, "message": "残高が未取得のため区切れません"})

    t = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    try:
        with open(MARKERS_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({"t": t, "balance": balance}, ensure_ascii=False) + "\n")
    except Exception:
        return JSONResponse(status_code=500, content={"ok": False, "message": "区切りの保存に失敗しました"})
    return {"ok": True, "balance": balance, "t": t}
```

## 停止条件

- `JSONResponse` のimportが既存importと衝突する場合
- `Response` を別の用途で既に別名import・再定義している場合
- 上記以外で仕様通りに直せない技術的理由がある場合

## 検証手順（実施して結果を持ち帰ること）

1. `git diff --stat -- main.py`
2. サーバー起動後、OCR未取得状態を再現して:
   ```
   curl -i -X POST http://localhost:8765/cut
   ```
   → 1行目が `HTTP/1.1 400` になっていること、本文は `{"ok": false, ...}` のままであることを確認
3. 固定テスト残高がある状態で:
   ```
   curl -i -X POST http://localhost:8765/cut
   ```
   → `HTTP/1.1 200`、`{"ok": true, ...}` のままであることを確認（成功系は無変更のはず）
4. ブラウザで `/log` を開き、OCR未取得を意図的に再現できない場合は省略可。可能なら「ここで区切る」を
   OCR未取得状態で押し、alertが出ることを目視確認する
5. `git diff -- main.py` の完全diffを提示（`...`省略禁止）

## 出力形式

- 完全before/after diff
- 上記検証1〜5の結果
- stage/commit/pushは行わない
