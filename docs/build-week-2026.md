# DeltaForceHUD — OpenAI Build Week 2026 boundary

## Event boundary

- Official start: 2026-07-13 09:00 PDT (2026-07-13 16:00 UTC / 2026-07-14 01:00 JST)
- Pre-event baseline: `31c38ca71d7c3a170938e4fa16c2fbe62836d675`
- Audited HEAD: `45b57b3fb6ed83e1144ce05d83054e967ff3a218`
- Primary Codex Session ID: `019f74dc-5f11-79e3-86e1-a290fa97cc42`
- Supporting harness implementation Session ID: `019f7771-99df-7ae2-ac4f-561d9694b693`
- Supporting capture/editing Session ID: `019f793c-84ba-72e3-a36c-916984651004`

## What changed

| Item | Before Build Week | During Build Week | Evidence | Verification |
|---|---|---|---|---|
| Cut/segment UI | `sessions.html` already contained “Cut Here” and called `/cut` and `/current_segment`. | UI was not changed. | Pre-event history including `a6ff430` and baseline tree `31c38ca`; Build Week commit `85ef29b` did not modify `sessions.html`. | Source inspection of `sessions.html` call sites. |
| Backend availability in the event baseline | Baseline `31c38ca` did not contain the backend endpoints, so the existing UI could not complete the flow. Earlier repository history had an experimental implementation, but it was absent from the event baseline. | Codex restored and completed `POST /cut`, `GET /current_segment`, `MARKERS_LOG`, and error responses in `main.py`. | `85ef29b`, 48 insertions and 1 deletion in `main.py`; Primary Session ID above. | `ast_parse=PASS`; recorded curl results: 400 for missing balance, 200 for successful marker save, 500 for forced save failure; browser alert verified. |
| Error contract | The first implementation instruction incorrectly assumed HTTP 200 was compatible with the frontend. The frontend actually branches on `res.ok`. | Follow-up review corrected the contract to HTTP 400/500 while preserving HTTP 200 for success. | `docs/session_cut_backend_指示書_v1.md`, `docs/session_cut_backend_指示書_v2_fix.md`, and `85ef29b`. | Recorded `curl -i` evidence in the Primary Codex Session. |
| Judge documentation | No Build Week judge quick-start section. | README gained judge testing steps and a summary of Codex/GPT-5.6 use. | `d9efac7`; follow-up wording/license commit `45b57b3`. | README/source inspection and link/path audit. |
| License | The event baseline had no standalone license file. | A standalone license file was added during Build Week and later standardized to Apache License 2.0 with human approval. | `45b57b3` and the current license transition. | `LICENSE` matches the official Apache License 2.0 text. |
| Supporting video-production harness | The audited repository has no pre-event commit; its history begins with one root commit during Build Week. | Codex implemented a Windows walking skeleton for canonical script/JSON state, journaled atomic updates, CAS ingest, Scene/Shot/Clip tracking, freshness, timeline validation, and verified FFmpeg export. | Private support repo commit `66b12de`; harness Session ID above. | Current audit rerun: `50 passed in 3.78s`; T16 session evidence: 90-frame 1280x720 30fps MP4 with 48kHz audio. |
| Demo capture and editing | The final demo had not been produced. | Codex diagnosed OBS capture failures, controlled recording and source routing, verified real OCR values, removed recursive preview, cut the accepted footage, synchronized 16 English voice clips, and exported a 126.25-second MP4. | Capture/editing Session ID above; `Codex撮影指示書.md`; `build_buildweek_video.ps1`; final MP4 SHA-256 `6D104E729B89233520F5E8F7E2D1E61FA6E191A0B5EFFC6F1301BC55BDD4196D`. | `ffprobe`: H.264, 1920x1080, 60fps; AAC, 48kHz stereo. Human review confirmed three accepted source clips and the corrected 43,828K OCR view. |

## Accurate Build Week claim

DeltaForceHUD existed before Build Week. The event-period engineering contribution was not the original OCR HUD, setup wizard, lobby detection, OBS overlay, history graph, CSV export, freeze recovery, or the original cut UI. During Build Week, Codex on GPT-5.6 diagnosed and completed the missing backend integration required by the pre-existing cut UI, aligned backend error status codes with the frontend’s `res.ok` contract, and verified success and failure paths. Judge-facing documentation and a standalone license file were also added during the event period; the license was later standardized to Apache License 2.0 with human approval.

Separately, Codex implemented a supporting AI video-production harness and used a dedicated OBS/FFmpeg workflow to diagnose, capture, validate, edit, and export the submission demo. The final demo was produced by the dedicated PowerShell/FFmpeg workflow; the audit did not find evidence that it was exported from a canonical project inside the harness.

## Human-directed multi-model workflow

The work was human-directed. Claude was used as an auxiliary specification and review aid. Codex handled repository diagnosis, implementation, endpoint verification, OBS recording control, footage validation, synchronization, and export. The human developer handled the product goal, in-game actions, footage judgment, narration alignment, final approval, and publication.

For the demo, Codex diagnosed a stopped Virtual Camera and stale frame, verified the real 43,410K to 43,828K balance change, and removed a recursive setup preview. The human developer clicked “Cut Here,” performed the in-game currency action, rejected technically valid but visually unusable footage, and approved the corrected clips.

## Known limitations

- Windows-first launcher and paths.
- Tesseract must be installed separately, and Japanese `jpn.traineddata` must be available.
- OCR accuracy depends on capture device, resolution, crop, game UI, and readable numeric text.
- Delta Force is required for the actual intended gameplay workflow, although the server and OCR path can be inspected against another suitable captured numeric screen.
- This is an unofficial fan tool and is not affiliated with or endorsed by Team Jade, TiMi Studio Group, Level Infinite, OBS Project, OpenAI, or Anthropic.
