# DeltaForceHUD

> **OpenAI Build Week 2026 submission.** DeltaForceHUD is an unofficial, Windows-first OCR overlay for extraction-shooter streamers. It reads only the user’s own captured screen and shows asset gain/loss in OBS without accessing game memory or modifying network traffic.

## In 30 seconds

- **Problem:** viewers can see combat, but they cannot easily understand whether the streamer’s assets increased or decreased.
- **For:** Delta Force streamers who want asset progression to be part of the broadcast.
- **Solution:** a local OpenCV + Tesseract OCR pipeline reads the visible asset value and serves an OBS browser-source HUD, session history, and cut-based segment change.
- **Safety boundary:** screen capture and OCR only. No game-memory access and no network modification. Screen-capture software may still interact with anti-cheat policies, so use remains the user’s responsibility.

## Completed features

- OBS Virtual Camera capture
- Asset-value OCR with OpenCV, pytesseract, and Japanese Tesseract data
- Browser setup wizard for camera and OCR-region selection
- Lobby-state word matching and combat-time OCR gating
- OBS browser-source gain/loss overlay
- Session history, trend graph, and CSV export
- “Cut Here” marker and net change from the latest marker
- Camera-freeze detection and reconnect handling

## OpenAI Build Week 2026 boundary

DeltaForceHUD existed before Build Week. The OCR pipeline, setup wizard, OBS overlay, history view, and cut UI predated the event.

At the event baseline (`31c38ca`), the cut UI called backend endpoints that were absent from `main.py`. During Build Week, Codex running on GPT-5.6 inspected the frontend call contract, restored and completed `POST /cut` and `GET /current_segment`, added `markers.jsonl` persistence, corrected the HTTP failure contract, and verified 400/200/500 paths. See [Build Week boundary and evidence](docs/build-week-2026.md).

Primary Codex Session ID: `019f74dc-5f11-79e3-86e1-a290fa97cc42`

Supporting Session IDs: AI video-production harness `019f7771-99df-7ae2-ac4f-561d9694b693`; OBS capture and editing `019f793c-84ba-72e3-a36c-916984651004`.

## How AI was used

This was a human-directed, multi-model workflow:

1. The human developer defined the product goal.
2. Claude assisted with structured specification and review.
3. Codex running on GPT-5.6 handled repository diagnosis, implementation, and endpoint verification.
4. A follow-up review challenged the original HTTP-status assumption; Codex applied the correction and re-verified the error and success paths.
5. The human developer handled in-game actions, footage judgment, narration alignment, final approval, and publication.

Codex also built a supporting Windows video-production harness and handled OBS recording control, footage validation, synchronization, and export. The final demo was rendered through a dedicated PowerShell/FFmpeg workflow rather than a canonical harness project.

## Supported environment

- Windows 10/11
- Python 3.10
- OBS Studio with Virtual Camera, or another OpenCV-readable capture device
- Tesseract OCR installed at `C:\Program Files\Tesseract-OCR\tesseract.exe`
- Japanese `jpn.traineddata` available under `tessdata\`

The current launcher and default paths are Windows-specific. Other operating systems are not currently documented or supported.

## Windows setup

1. Install Python and confirm:

   ```powershell
   python --version
   ```

2. Install Tesseract OCR. The launcher expects:

   ```text
   C:\Program Files\Tesseract-OCR\tesseract.exe
   ```

3. Place Japanese OCR data at:

   ```text
   tessdata\jpn.traineddata
   ```

4. Create a virtual environment and install Python dependencies:

   ```powershell
   python -m venv venv
   .\venv\Scripts\pip install -r requirements.txt
   ```

5. Start OBS Virtual Camera or another capture source, then run:

   ```powershell
   .\start.bat
   ```

6. Open `http://localhost:8765/setup`, select the capture device, and draw the OCR region around readable numeric text.

7. Register `http://localhost:8765/` as an OBS browser source.

## Judge quick test

The intended Delta Force workflow requires the game, but the local server and OCR path can be inspected without it by capturing another suitable screen with readable numeric text.

1. Complete the Windows setup above and start the server.
2. Open `http://localhost:8765/health` and inspect the five readiness flags: `camera`, `ocr`, `start`, `tesseract`, and `jpn`.
3. Open `http://localhost:8765/setup`, select the capture source, and draw an OCR region around a clearly visible number.
4. Request `GET http://localhost:8765/ocr_test` and inspect `ok`, `raw`, `value_fmt`, and the returned crop.
5. Open `http://localhost:8765/log` to inspect session history and the existing “Cut Here” UI.
6. For the complete cut flow, a valid current balance is required. `POST /cut` records the current balance and `GET /current_segment` returns the change from the latest marker.

No automated test suite is currently included. The Build Week endpoint evidence is documented in `docs/build-week-2026.md`.

## Main URLs

- OBS HUD: `http://localhost:8765/`
- Setup: `http://localhost:8765/setup`
- Session history: `http://localhost:8765/log`
- Health: `http://localhost:8765/health`
- OCR test: `http://localhost:8765/ocr_test`

## Planned work

- Standalone Windows packaging with Tesseract included
- Additional game and screen-layout profiles
- Additional viewer-facing overlay options

These items are plans, not completed features.

## Repository hygiene

Do not commit personal settings, runtime logs, recordings, or secrets. Before publication, inspect `git status --short` and run appropriate local secret and static-analysis scans.

Tracked application files include:

- `main.py`
- `obs.html`
- `sessions.html`
- `setup.html`
- `requirements.txt`
- `start.bat`
- `LICENSE`
- `assets/logo.png`
- project documentation

Runtime/local-only files include:

- `venv/`
- `settings.json`
- `session_log.jsonl`
- `markers.jsonl`
- `lobby_debug.csv`
- `tessdata/*.traineddata`
- recordings and generated packages

## Contact

- Issues: https://github.com/factorysamuraispirits-png/DeltaForceHUD/issues
- X: https://x.com/mochiya888

## Disclaimer and trademarks

Use this tool at your own risk. DeltaForceHUD is an unofficial fan-made tool. It is not affiliated with or endorsed by Team Jade, TiMi Studio Group, Level Infinite, OBS Project, OpenAI, or Anthropic. Product names and trademarks belong to their respective owners.

## License and redistribution

DeltaForceHUD is licensed under the Apache License, Version 2.0 (`Apache-2.0`). See the standalone `LICENSE` file for the full terms. Redistribution and modification are permitted under that license, subject to its conditions.

© 2026 Factory-mo（もちや。。）
