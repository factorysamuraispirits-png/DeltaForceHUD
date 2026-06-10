# OBS HUD: Gitリポジトリ化・初回コミット指示書 v2

## ゴール

このOBS HUDフォルダをGitリポジトリ化し、現状を最初のコミットとして記録する。
**初回コミットの前に秘密情報スキャン（gitleaks→Semgrep）を必ず通す。**

---

# 最重要ルール

* 勝手に進めないこと
* 承認が必要な工程では必ず停止すること
* 判断に迷ったら作業を止めて質問すること
* 既存コード・既存設定・既存データを変更しないこと
* ファイル削除を行わないこと
* 指示されていないリファクタリングを行わないこと

---

# 環境前提

* OS: Windows
* シェル: PowerShell
* gitleaks / Semgrep はローカル実行（無料・OSS）。課金が必要な操作は一切行わない。

---

# 作業ディレクトリ

* 現在開いているOBS HUDプロジェクト直下のみ
* 親フォルダでは実行しない
* 作業開始時に現在のパスを表示すること

実施：

```powershell
Get-Location
```

現在位置を確認して報告すること。
（git導入後は `git rev-parse --show-toplevel` でリポジトリ直下も確認すること。）

---

# 範囲（やること）

1. フォルダ構成の調査
2. 既存 `.git` の有無確認
3. git ユーザー設定（user.name / user.email）の確認
4. git init
5. .gitignore案の作成
6. 承認後に .gitignore 作成
7. git status --short で追跡対象の目視確認
8. 承認後に git add
9. **コミット前セキュリティスキャン（gitleaks→Semgrep）の実行**
10. スキャンがクリーンであることの承認
11. 承認後に commit

---

# 非対象（やらないこと）

* git push
* GitHub連携
* branch作成
* tag作成
* release作成
* GitHub Actions作成
* 既存コード変更（Tesseract絶対パス直書きを含め、今回は一切触らない）
* ファイル削除
* リネーム
* フォーマッタ実行
* 自動修正

---

# 着手前調査

まず以下を報告すること。

## 1. 現在のパス

表示すること。

---

## 2. .git の有無

確認すること。

もし `.git` が存在する場合：

* git init は実行しない
* 現在の状態のみ報告する
* 以降の作業を停止する
* 私の指示を待つ

---

## 3. git ユーザー設定の確認

以下を表示すること。

```powershell
git config user.name
git config user.email
```

報告内容：

* 現在の user.name / user.email
* それがこのプロジェクトに刻んでよい身元か（後でGitHub公開予定のため、意図しない本名・個人メールが履歴に残らないようにする）

意図しない身元、または未設定の場合：

* commit は実行しない
* 状態のみ報告して停止する
* 私の指示を待つ

（※ 設定変更が必要な場合も、私の承認後に私が指示した値だけを設定すること。勝手にグローバル設定を書き換えない。）

---

## 4. フォルダ構成

上位階層をツリー表示または一覧表示すること。

報告対象：

* フォルダ構成
* ファイル一覧
* ディレクトリ一覧

---

## 5. 機密ファイル候補

以下を探して報告すること。

* .env
* .env.*
* config.json
* settings.json
* local_settings.json
* secrets.*
* credential*
* token*
* key*
* APIキーを含む可能性のあるファイル
* Supabaseキーを含む可能性のあるファイル
* OpenAIキーを含む可能性のあるファイル
* Claudeキーを含む可能性のあるファイル
* Discord Webhookを含む可能性のあるファイル

※ ここはファイル名ベースの一次スクリーニング。直書きされた秘密情報（main.py内のWebhook URL等）はこの段階では拾えない前提で扱うこと。中身の検出は後段の gitleaks が担当する（だから初回コミット前に必須）。

---

## 6. 大容量ファイル候補

以下を探して報告すること。

対象：

* png
* jpg
* jpeg
* webp
* mp4
* mov
* mkv
* zip

さらに、

* 50MB以上のファイル

を一覧化すること。

報告内容：

* ファイル名
* サイズ
* 用途の推定

### 画像の仕分け（重要）

検出した画像ファイルは、一覧化したうえで以下のどちらかに仕分けして報告すること。

* **UI素材・アイコン（Git管理する）**: obs.html等で使うHUD素材
* **デバッグ吐き出し・キャプチャ（除外する）**: OCR検証で生成されたスクリーンショット等

仕分けの判断がつかない画像、または `captures/` `screenshots/` 以外の場所に散在するキャプチャを発見した場合：

* 一覧と判断材料を報告して停止する
* .gitignore方針を私と相談する

---

# .gitignore

勝手に作成しないこと。

まず候補案を提示すること。

私の承認後にのみ作成してよい。

---

## 除外候補

### Python

```text
__pycache__/
*.pyc
.venv/
venv/
```

### 環境依存

```text
.env
.env.*
```

### OS

```text
Thumbs.db
desktop.ini
.DS_Store
```

### IDE

```text
.idea/
.vscode/
```

### ログ

```text
logs/
*.log
```

### 録画・配布物

```text
recordings/
*.mp4
*.mov
*.mkv
*.zip
```

### キャプチャ

重要：

画像拡張子（*.png / *.jpg）を一律除外しないこと。

理由：

OBS HUDのUI素材やアイコン画像まで除外される可能性があるため。

キャプチャ画像が存在する場合は、上記「画像の仕分け」結果に基づき、

```text
captures/
screenshots/
```

などフォルダ単位で除外すること。
（散在するキャプチャがあった場合は、仕分け結果を反映した除外案を別途提示すること。）

### .gitattributes（任意・要相談）

Windows環境のため、改行コード差分ノイズを抑える `.gitattributes` を入れる選択肢がある。

```text
* text=auto
```

* 必須ではない。入れる場合も私の承認後にのみ作成すること。
* 不要なら省略してよい。判断は私に確認すること。

---

## .gitignore作成後

以下を表示すること。

```powershell
git status --short
```

さらに、

* .gitignore全文
* 除外対象一覧
* 除外理由

を表示すること。

ここで停止すること。

承認待ち。

---

# git add ルール

`git status --short` で追跡対象を目視確認し、承認を得てから add すること。

## add前に表示

以下を表示すること。

### 追加対象

Git管理するファイル一覧（`git status --short` の結果）

### 除外対象

.gitignoreで除外されたファイル一覧

### 除外理由

なぜ除外したのか

ここで停止すること。

承認待ち。

---

## add方法

* `.gitignore` が正しく機能していることを `git status --short` で目視確認・承認済みであること。
* その前提が満たされた場合に限り、`git add .`（.gitignoreを尊重する）を使用してよい。
* 個別ファイルの取りこぼし防止のため、上記の「目視→承認→`git add .`」を1セットで扱う。
* 承認前に勝手に add しないこと。

---

# git add 実行後

以下を表示すること。

```powershell
git status
git diff --cached
```

さらに、

コミット対象ファイル一覧（`git ls-files --cached`）

を表示すること。

ここで停止すること。

承認待ち。

---

# コミット前セキュリティスキャン（必須・今回実施）

**commit の前に必ず実行すること。** git履歴は追記式で、一度コミットした秘密情報は後からファイルを消しても履歴に残り続ける。だから「公開前」ではなく「初回コミット前」にスキャンする。

## インストール確認（スキャン前に必須）

スキャン実行の前に、両ツールが利用可能か確認すること。

```powershell
gitleaks version
semgrep --version
```

### gitleaks または Semgrep が未インストールの場合

* commit は実行しない
* インストール状況（どちらが無いか）を報告する
* 私の指示を待つ

（インストール作業は勝手に行わない。無料ベース・課金は管理者承認必須の原則に従う。
スキャンをスキップして commit に進むことは絶対にしない＝スキャンせずにコミットする事態を防ぐ。）

## 実施

```powershell
gitleaks detect --source . --no-git
semgrep scan --config auto
```

報告内容：

* gitleaks の結果（検出件数・該当ファイル・該当箇所）
* semgrep の結果（検出件数・重要度・該当箇所）

### ヒットした場合

* **commit は実行しない**
* 検出内容を報告して停止する
* 私の指示を待つ（秘密情報の除去・対応は別タスクで行う）

### クリーンの場合

* その旨を報告し、承認待ちで停止する
* 私の承認後にのみ commit へ進む

---

# commit

私の承認後のみ実行。

---

## コミットメッセージ

必ず以下を使用すること。

```text
Initial commit: OBS HUD baseline
```

変更禁止。

---

# 成功条件

* git status が clean
* 初回コミットが作成されている
* 機密ファイルが追跡されていない
* **gitleaks→Semgrep がクリーン（秘密情報が履歴に入っていない）**
* 巨大バイナリが追跡されていない
* .gitignore が適切に機能している
* commit の身元（user.name / user.email）が意図通り

---

# 完了報告

以下を表示すること。

---

## .gitignore全文

---

## セキュリティスキャン結果

* gitleaks: 件数・結果
* semgrep: 件数・結果

---

## コミットハッシュ

```powershell
git rev-parse HEAD
```

---

## git status

```powershell
git status
```

---

## git log

```powershell
git log --oneline -n 5
```

---

## 追跡対象ファイル一覧

```powershell
git ls-files
```

---

# 公開前チェック（GitHub公開時・別スレで実施）

GitHub公開は今回の範囲外（非対象）。公開を行う別スレッドで、最終ゲートとして以下を再実施予定。

```powershell
gitleaks detect --source . --no-git
semgrep scan --config auto
trivy fs .
```

今回はここまで（push・公開は行わない）。

---

# 停止条件

以下に該当した場合は作業を停止し、理由を説明して指示を待つこと。

* 既存 `.git` が存在する
* git の user.name / user.email が未設定、または意図しない身元
* APIキーや秘密情報を発見した
* **gitleaks / Semgrep が未インストール（この場合は commit しない）**
* **gitleaks / Semgrep でヒットした（この場合は commit しない）**
* 100MB超のファイルを発見した
* 除外すべきか判断できないファイルがある
* .gitignore方針に影響する素材ファイル（散在キャプチャ等）を発見した
* 指示内容と現状が矛盾している

---

# 補足メモ（今回は対応しない・記録のみ）

* main.py / start.bat 内の Tesseract 絶対パス直書きは既知。ポータブル化は別スレで対応する方針のため、今回の「現状をそのままコミット」では一切変更しない。
