import cv2, numpy as np, pytesseract, time, re, json, threading, os, base64, csv
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response
import uvicorn

BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
SESSION_LOG   = os.path.join(BASE_DIR, "session_log.jsonl")
MARKERS_LOG   = os.path.join(BASE_DIR, "markers.jsonl")
LOBBY_DEBUG_LOG = os.path.join(BASE_DIR, "lobby_debug.csv")
SETTINGS_PATH = os.path.join(BASE_DIR, "settings.json")

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

DEFAULT_SETTINGS = {
    "profile": "delta_force",
    "first_run_done": False,
    "camera_index": 1,
    "ocr_region": {"x": 0.760, "y": 0.020, "w": 0.140, "h": 0.035},
    "lobby_anchor": {"x": 0.050, "y": 0.015, "w": 0.450, "h": 0.038},
    "elements": {
        "gain":   {"enabled": True, "fx": False},
        "logo":   {"enabled": True},
        "banner": {"enabled": False, "mode": "sponsor"},
        "lobby_gate": {"enabled": False, "min_chars": 6, "debug": False}
    },
    "session": {"log": True}
}

_frame_lock    = threading.Lock()
_settings_lock = threading.Lock()
_s_mtime: float = 0.0
_s_cache        = None


def round_region(r):
    try:
        return {k: round(float(r[k]), 3) for k in ("x", "y", "w", "h")}
    except Exception:
        return DEFAULT_SETTINGS["ocr_region"].copy()


def deep_merge(base, override):
    out = json.loads(json.dumps(base))
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_settings():
    global _s_mtime, _s_cache
    with _settings_lock:
        try:
            mtime = os.path.getmtime(SETTINGS_PATH)
            if _s_cache is not None and mtime == _s_mtime:
                return json.loads(json.dumps(_s_cache))
            with open(SETTINGS_PATH, encoding="utf-8") as f:
                raw = json.load(f)
            s = deep_merge(DEFAULT_SETTINGS, raw)
            s["ocr_region"] = round_region(s["ocr_region"])
            s["lobby_anchor"] = round_region(s.get("lobby_anchor", DEFAULT_SETTINGS["lobby_anchor"]))
            _s_mtime, _s_cache = mtime, s
            return json.loads(json.dumps(s))
        except Exception:
            return json.loads(json.dumps(DEFAULT_SETTINGS))


def write_settings(s):
    global _s_mtime, _s_cache
    with _settings_lock:
        s = deep_merge(DEFAULT_SETTINGS, s)
        s["ocr_region"] = round_region(s["ocr_region"])
        s["lobby_anchor"] = round_region(s.get("lobby_anchor", DEFAULT_SETTINGS["lobby_anchor"]))
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(s, f, ensure_ascii=False, indent=2)
        _s_mtime = os.path.getmtime(SETTINGS_PATH)
        _s_cache = s


state = {
    "raw": "", "value": 0, "start": None, "gain": 0,
    "updated": "", "running": False, "last_frame_ts": 0.0, "in_lobby": True
}
shared = {"frame": None}


def parse(text):
    t = re.sub(r'[^0-9.,KMBkmb]', '', text).upper()
    t = re.sub(r'(\d+)[,.](\d{3})([KMB])', r'\1\2\3', t)
    t = t.replace(',', '')
    # [変更] 単位(K/M/B)必須。戦闘中の座標(単位なし)を誤検知しないため
    m = re.match(r'(\d+\.?\d*)([KMB])', t)
    if not m:
        return None
    try:
        n = float(m.group(1))
    except Exception:
        return None
    u = m.group(2)
    if u == 'K': n *= 1_000
    elif u == 'M': n *= 1_000_000
    elif u == 'B': n *= 1_000_000_000
    return int(n)


def fmt(v, signed=True):
    if v is None:
        return "---"
    sign = "+" if (signed and v > 0) else ("-" if v < 0 else "")
    a = abs(v)
    if a >= 1_000_000_000: return f"{sign}{a/1_000_000_000:.2f}B"
    if a >= 1_000_000:     return f"{sign}{a/1_000_000:.1f}M"
    if a >= 1_000:         return f"{sign}{a/1_000:.1f}K"
    return f"{sign}{int(a)}"


def crop_region(frame, r):
    h, w = frame.shape[:2]
    x1 = max(0, int(w * r["x"])); y1 = max(0, int(h * r["y"]))
    x2 = min(w, int(w * (r["x"] + r["w"]))); y2 = min(h, int(h * (r["y"] + r["h"])))
    if x2 <= x1 or y2 <= y1:
        return None
    return frame[y1:y2, x1:x2]


# ロビー判定 — 左上タブ帯を日本語OCRで読み、メニュー画面を検出
PROJECT_TESSDATA = os.path.join(BASE_DIR, "tessdata")
# メニュー画面はタブ単語が画面ごとに異なるため、特定語ではなく
# 「日本語文字数」で判定する（メニュー=多い / 戦闘=ほぼ無い）。
# しきい値は settings の elements.lobby_gate.min_chars で調整可能（既定8）
LOBBY_MIN_JP_DEFAULT = 6


def _jpn_available():
    """日本語OCRデータが使えるか（プロジェクト内 or 既定tessdata）"""
    if os.path.exists(os.path.join(PROJECT_TESSDATA, "jpn.traineddata")):
        return True
    try:
        return "jpn" in pytesseract.get_languages(config="")
    except Exception:
        return False


JPN_AVAILABLE = _jpn_available()


def preprocess_tab(roi):
    """タブ帯ROIを日本語OCR用に前処理（3x拡大→白文字を黒文字/白地に反転）"""
    big  = cv2.resize(roi, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(big, cv2.COLOR_BGR2GRAY)
    _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    return th


def ocr_tab_image(th):
    """前処理済み画像を日本語OCRして文字列を返す"""
    cfg = "--psm 6"   # 横並びメニューはブロック扱いの方が安定
    if os.path.exists(os.path.join(PROJECT_TESSDATA, "jpn.traineddata")):
        # Windowsパスはスラッシュ化＋引用符なし（pytesseractの引数分割/エスケープ対策）
        cfg += " --tessdata-dir " + PROJECT_TESSDATA.replace("\\", "/")
    try:
        return pytesseract.image_to_string(th, lang="jpn", config=cfg).strip()
    except Exception:
        return ""


def ocr_lobby_text(frame, anchor):
    """タブ帯領域を日本語OCRして読み取り文字列を返す"""
    roi = crop_region(frame, anchor)
    if roi is None or roi.size == 0:
        return ""
    return ocr_tab_image(preprocess_tab(roi))


def count_jp_chars(text):
    """ひらがな/カタカナ/漢字/長音符の数を数える"""
    n = 0
    for c in text:
        o = ord(c)
        if (0x3040 <= o <= 0x30FF) or (0x4E00 <= o <= 0x9FFF) or c == "\u30fc":
            n += 1
    return n


# 実ログ分析の結論：戦闘中はOCRが3D背景をゴミ文字化して最大84文字も生成するため、
# 「文字数」では分離不可能（戦闘 > ロビー）。一方「ロビー/倉庫/オペレーター」等の
# 実在タブ単語は、戦闘ノイズには絶対に出現しない（暴走フレームで漏れ0を実測確認）。
# よって判定は「文字数」ではなく「ロビー固有単語が読めているか」で行う。
LOBBY_WORDS = ("ロビー", "倉庫", "オペレーター")

def _strip_spaces(text):
    return text.replace(" ", "").replace("\u3000", "")

def matched_lobby_word(text):
    """OCR文字列(空白除去)にロビー固有単語が含まれればその語を返す。無ければNone"""
    s = _strip_spaces(text)
    for w in LOBBY_WORDS:
        if w in s:
            return w
    return None

def judge_lobby(text, min_jp=None):
    """ロビー固有単語が読めていればロビー(min_jpは後方互換のため受けるが未使用)"""
    return matched_lobby_word(text) is not None


def is_lobby(frame, anchor, min_jp=LOBBY_MIN_JP_DEFAULT):
    """ロビー判定。戦闘固有語があれば除外＋文字数判定。jpn未導入/エラー時はTrue"""
    if not JPN_AVAILABLE:
        return True
    try:
        return judge_lobby(ocr_lobby_text(frame, anchor), min_jp)
    except Exception:
        return True


def lobby_probe(frame, anchor, min_jp):
    """ロビー判定の詳細を返す: (raw_lobby, ocr文字列, 日本語文字数, マーカー有無)"""
    if not JPN_AVAILABLE:
        return True, "", 0, False
    try:
        text = ocr_lobby_text(frame, anchor)
        word = matched_lobby_word(text)
        n    = count_jp_chars(text)
        return (word is not None), text, n, word
    except Exception:
        return True, "", 0, None


def log_lobby_debug(text, n, word, raw, gate_open):
    """調査用：各フレームのOCR読み取り内容をCSVに追記（utf-8-sig=Excel対応）"""
    try:
        path = LOBBY_DEBUG_LOG
        is_new = not os.path.exists(path)
        clean = text.replace("\n", " ").replace("\r", " ").strip()
        with open(path, "a", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            if is_new:
                w.writerow(["time", "ocr_text", "jp_count", "matched_word", "raw_lobby", "gate_open"])
            w.writerow([datetime.now().strftime("%H:%M:%S.%f")[:-3],
                        clean, n, (word or ""), int(raw), int(gate_open)])
    except Exception:
        pass


def run_ocr(roi):
    big  = cv2.resize(roi, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(big, cv2.COLOR_BGR2GRAY)
    _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    cfg = '--oem 1 --psm 6 -c tessedit_char_whitelist=0123456789.,KMBkmb'
    try:
        return pytesseract.image_to_string(th, config=cfg).strip()
    except Exception:
        return ""


def ocr_loop():
    cap      = None
    cur_idx  = -1
    fail_cnt = 0
    MAX_FAILS = 5
    pending  = {"val": None, "count": 0}
    prev_logged_v = None
    # ロビー判定スムージング（直近数フレームの移動窓でチラつき吸収）
    gate_open       = True
    lobby_window    = []
    LOBBY_WIN       = 5
    prev_in_lobby   = True

    while True:
        try:
            s   = load_settings()
            idx = s.get("camera_index", 1)

            if cap is None or not cap.isOpened() or idx != cur_idx:
                if cap is not None:
                    cap.release()
                cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
                cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1920)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
                cur_idx  = idx
                fail_cnt = 0
                time.sleep(0.5)
                continue

            ret, frame = cap.read()
            if not ret:
                fail_cnt += 1
                if fail_cnt >= MAX_FAILS:
                    cap.release()
                    cap     = None
                    cur_idx = -1
                    fail_cnt = 0
                time.sleep(1)
                continue

            fail_cnt = 0
            with _frame_lock:
                shared["frame"] = frame.copy()
            state["last_frame_ts"] = time.time()

            # ロビー判定ゲート（タブ帯OCR + ヒステリシス）
            gate = s.get("elements", {}).get("lobby_gate", {})
            if gate.get("enabled", False):
                min_jp = gate.get("min_chars", LOBBY_MIN_JP_DEFAULT)
                raw_lobby, dbg_text, dbg_n, dbg_word = lobby_probe(
                    frame, s.get("lobby_anchor", {}), min_jp)
                lobby_window.append(raw_lobby)
                if len(lobby_window) > LOBBY_WIN:
                    lobby_window.pop(0)
                # 単語一致は戦闘ノイズに出ないクリーンな信号なので、直近窓に1回でも
                # 一致があればON（ロビー側の一時的な読み逃しを橋渡し）。戦闘は一致0でOFF
                gate_open = any(lobby_window)
                in_lobby = gate_open
                # 調査用ログ（ONの時だけCSV追記）
                if gate.get("debug", False):
                    log_lobby_debug(dbg_text, dbg_n, dbg_word, raw_lobby, gate_open)
            else:
                in_lobby, gate_open = True, True
                lobby_window = []
            state["in_lobby"] = in_lobby
            if in_lobby != prev_in_lobby:
                print("[ロビー判定] " + ("ロビー検出 → 計測ON" if in_lobby else "戦闘検出 → 計測OFF"))
                prev_in_lobby = in_lobby

            roi = crop_region(frame, s["ocr_region"])
            if roi is not None and in_lobby:
                val = parse(run_ocr(roi))
                if val and 1_000 < val < 100_000_000_000:
                    prev     = state["value"]
                    big_jump = prev and (abs(val - prev) / prev) > 0.45

                    if big_jump:
                        if pending["val"] == val:
                            pending["count"] += 1
                        else:
                            pending = {"val": val, "count": 1}
                        if pending["count"] < 2:
                            state["running"] = True
                            time.sleep(1)
                            continue
                        pending = {"val": None, "count": 0}
                    else:
                        pending = {"val": None, "count": 0}

                    state["value"]   = val
                    state["updated"] = datetime.now().strftime("%H:%M:%S")
                    state["raw"]     = str(val)
                    if state["start"] is not None:
                        state["gain"] = val - state["start"]

                    if (s.get("session", {}).get("log", True)
                            and (prev_logged_v is None
                                 or (gate_open == 1 and val != prev_logged_v))):
                        try:
                            with open(SESSION_LOG, "a", encoding="utf-8") as lf:
                                lf.write(json.dumps({
                                    "t": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                                    "v": val
                                }) + "\n")
                            prev_logged_v = val
                        except Exception:
                            pass

            state["running"] = True
            time.sleep(1)

        except Exception as _e:
            print("[OCRループ警告] " + str(_e) + " — このフレームをスキップして継続します")
            time.sleep(1)
            continue

app = FastAPI()


@app.get("/asset")
def asset():
    return {
        "gain_fmt":  fmt(state["gain"]),
        "start_fmt": fmt(state["start"], False),
        "now_fmt":   fmt(state["value"],  False),
        "gain":      state["gain"],
        "has_start": state["start"] is not None,
        "running":   state["running"],
        "updated":   state["updated"],
    }


@app.get("/health")
def health():
    now = time.time()
    return {
        "camera": (now - state["last_frame_ts"]) < 5,
        "ocr":    bool(state["updated"]) and state["value"] > 0,
        "start":  state["start"] is not None,
        "tesseract": os.path.exists(pytesseract.pytesseract.tesseract_cmd),
        "jpn":       os.path.exists(os.path.join(PROJECT_TESSDATA, "jpn.traineddata")),
    }


@app.get("/settings")
def get_settings():
    return load_settings()


@app.post("/settings")
async def post_settings(request: Request):
    data = await request.json()
    cur  = load_settings()
    write_settings(deep_merge(cur, data))
    return {"ok": True}


@app.post("/wizard_done")
def wizard_done():
    s = load_settings()
    s["first_run_done"] = True
    write_settings(s)
    return {"ok": True}


@app.get("/logo")
def logo():
    """ロゴ画像を動的に配信（install.py 再実行なしでロゴ変更可能）"""
    path = os.path.join(BASE_DIR, "assets", "logo.png")
    try:
        with open(path, "rb") as f:
            data = f.read()
        return Response(content=data, media_type="image/png")
    except FileNotFoundError:
        # フォールバック: 1×1 透過PNG
        import base64 as _b64
        data = _b64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwC"
            "AAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
        )
        return Response(content=data, media_type="image/png")


@app.get("/lobby_status")
def lobby_status():
    """設定画面のライブ表示用：タブ帯OCR結果とロビー判定"""
    with _frame_lock:
        f = shared["frame"]
        f = f.copy() if f is not None else None
    if f is None:
        return {"ok": False, "jpn": JPN_AVAILABLE, "text": "", "matched": None, "in_lobby": False}
    if not JPN_AVAILABLE:
        return {"ok": True, "jpn": False, "text": "", "matched": None, "in_lobby": True}
    s   = load_settings()
    roi = crop_region(f, s.get("lobby_anchor", {}))
    if roi is None or roi.size == 0:
        return {"ok": False, "jpn": True, "text": "", "matched": None, "in_lobby": False}
    th   = preprocess_tab(roi)
    text = ocr_tab_image(th)
    n    = count_jp_chars(text)
    word = matched_lobby_word(text)
    in_lobby = word is not None
    # 視覚確認用：枠の中身 と OCRに渡す画像
    _, b1 = cv2.imencode(".jpg", cv2.resize(roi, None, fx=2, fy=2))
    _, b2 = cv2.imencode(".jpg", th)
    crop = "data:image/jpeg;base64," + base64.b64encode(b1.tobytes()).decode()
    proc = "data:image/jpeg;base64," + base64.b64encode(b2.tobytes()).decode()
    return {"ok": True, "jpn": True, "text": text, "jp_count": n,
            "word": (word or ""), "in_lobby": in_lobby, "crop": crop, "proc": proc}


@app.get("/preview")
def preview():
    with _frame_lock:
        f = shared["frame"]
        f = f.copy() if f is not None else None
    if f is None:
        return Response(content=b"", media_type="image/jpeg")
    ok, buf = cv2.imencode(".jpg", f, [cv2.IMWRITE_JPEG_QUALITY, 70])
    return Response(content=buf.tobytes(), media_type="image/jpeg")


@app.get("/ocr_test")
def ocr_test():
    with _frame_lock:
        f = shared["frame"]
        f = f.copy() if f is not None else None
    if f is None:
        return {"ok": False, "msg": "カメラ映像がありません。OBSの仮想カメラを開始してください"}
    s   = load_settings()
    roi = crop_region(f, s["ocr_region"])
    if roi is None:
        return {"ok": False, "msg": "読み取り範囲が不正です"}
    text = run_ocr(roi)
    val  = parse(text)
    ok, buf = cv2.imencode(".jpg", cv2.resize(roi, None, fx=3, fy=3))
    crop = "data:image/jpeg;base64," + base64.b64encode(buf.tobytes()).decode()
    return {
        "ok":        val is not None,
        "raw":       text,
        "value_fmt": fmt(val, False) if val else "読み取り失敗",
        "crop":      crop,
    }


@app.post("/reset")
def reset():
    state["start"] = state["value"] if state["value"] else None
    if state["start"] is not None:
        state["gain"] = 0
    return {"ok": True, "start": state["start"]}


@app.get("/cameras")
def list_cameras():
    found = []
    for i in range(8):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                found.append(i)
            cap.release()
    return {"cameras": found}


def get_stable_balance():
    entries = []
    try:
        with open(SESSION_LOG, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                    if isinstance(item.get("v"), int):
                        entries.append(item)
                except Exception:
                    continue
    except FileNotFoundError:
        return None

    if not entries:
        return None

    values = [item["v"] for item in entries[-5:]]
    if len(values) < 3:
        return values[-1]
    if values[-1] == values[-2] == values[-3]:
        return values[-1]

    counts = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    best = values[-1]
    for value in reversed(values):
        if counts[value] > counts[best]:
            best = value
    return best


def get_last_marker():
    last = None
    try:
        with open(MARKERS_LOG, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                    if isinstance(item.get("balance"), int):
                        last = item
                except Exception:
                    continue
    except FileNotFoundError:
        return None
    return last


@app.post("/cut")
def cut_segment():
    balance = get_stable_balance()
    if balance is None:
        return Response(
            json.dumps({"ok": False, "error": "balance_unavailable", "message": "残高未取得"}, ensure_ascii=False),
            status_code=409,
            media_type="application/json")

    marker = {
        "t": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "balance": balance,
        "type": "manual"
    }
    try:
        with open(MARKERS_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(marker, ensure_ascii=False) + "\n")
    except Exception as e:
        print("[cutエラー] " + str(e))
        return Response(
            json.dumps({"ok": False, "error": "marker_write_failed", "message": str(e)}, ensure_ascii=False),
            status_code=500,
            media_type="application/json")
    return {"ok": True, "marker": marker}


@app.get("/current_segment")
def current_segment():
    last_marker = get_last_marker()
    current_balance = get_stable_balance()
    net = None
    if last_marker is not None and current_balance is not None:
        net = current_balance - last_marker["balance"]
    return {
        "last_marker": last_marker,
        "current_balance": current_balance,
        "net": net
    }


@app.get("/sessions")
def get_sessions():
    entries = []
    try:
        with open(SESSION_LOG, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except Exception:
                        pass
    except FileNotFoundError:
        pass
    return {"entries": entries[-1000:]}


@app.delete("/sessions")
def clear_sessions():
    try:
        open(SESSION_LOG, "w").close()
    except Exception:
        pass
    return {"ok": True}


@app.delete("/lobby_debug")
def clear_lobby_debug():
    try:
        if os.path.exists(LOBBY_DEBUG_LOG):
            os.remove(LOBBY_DEBUG_LOG)
    except Exception:
        pass
    return {"ok": True}


@app.get("/startup/status")
def startup_status():
    import winreg
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_READ)
        val, _ = winreg.QueryValueEx(key, "DeltaForceHUD")
        winreg.CloseKey(key)
        return {"registered": True, "path": val}
    except Exception:
        return {"registered": False}


@app.post("/startup")
def register_startup():
    import winreg
    try:
        bat = os.path.join(BASE_DIR, "start.bat")
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "DeltaForceHUD", 0, winreg.REG_SZ, bat)
        winreg.CloseKey(key)
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "msg": str(e)}


@app.delete("/startup")
def unregister_startup():
    import winreg
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key, "DeltaForceHUD")
        winreg.CloseKey(key)
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "msg": str(e)}


@app.get("/", response_class=HTMLResponse)
def hud():
    try:
        return open(os.path.join(BASE_DIR, "obs.html"), encoding="utf-8").read()
    except Exception:
        return "<h1>obs.html が見つかりません。install.py を再実行してください</h1>"


@app.get("/setup", response_class=HTMLResponse)
def setup():
    try:
        return open(os.path.join(BASE_DIR, "setup.html"), encoding="utf-8").read()
    except Exception:
        return "<h1>setup.html が見つかりません</h1>"


@app.get("/log", response_class=HTMLResponse)
def log_page():
    try:
        return open(os.path.join(BASE_DIR, "sessions.html"), encoding="utf-8").read()
    except Exception:
        return "<h1>sessions.html が見つかりません</h1>"


if __name__ == "__main__":
    threading.Thread(target=ocr_loop, daemon=True).start()
    print("=" * 54)
    print("  Delta Force HUD 起動完了")
    print("  設定画面      : http://localhost:8765/setup")
    print("  セッション履歴 : http://localhost:8765/log")
    print("  OBS 用 URL   : http://localhost:8765/")
    print("  終了          : Ctrl+C")
    print("=" * 54)
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="warning")
