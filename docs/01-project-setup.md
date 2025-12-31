# チケット01: プロジェクトセットアップ

## 概要
MCPサーバーの基本構成と環境設定を行う

## TODO
- [x] Python 3.10+のインストール確認（要ユーザー対応）
- [x] プロジェクトディレクトリ構成の作成
- [x] 必要なライブラリの定義（requirements.txt作成済み）
  - [x] FastMCP
  - [x] line-bot-sdk
  - [x] gspread
  - [x] google-auth
  - [x] python-dotenv
- [x] .envファイルのテンプレート作成（.env.example）
  - [x] LINE_CHANNEL_ACCESS_TOKEN
  - [x] LINE_CHANNEL_SECRET
  - [x] GOOGLE_SHEET_ID (154oKRpM6sQUv7yJ0SowIjWVHlO-IEZZ1fSnpwf2JOgw)
  - [x] SERVICE_ACCOUNT_FILE
- [ ] Googleサービスアカウントの作成とJSONキーの取得（要ユーザー対応）
- [x] requirements.txtの作成

## 成果物
- [x] プロジェクトディレクトリ構成（src/, tests/, config/, docs/）
- [x] .env.exampleファイル（テンプレート）
- [x] 依存関係管理ファイル（requirements.txt）
- [x] .gitignoreファイル
- [x] 基本的なソースコードファイル（config.py, mcp_server.py等）
- [x] README.md
- [x] Googleサービスアカウント設定ガイド
- [ ] サービスアカウントJSONファイル（要ユーザー対応）
- [ ] .envファイル（要ユーザー対応）

## 関連ドキュメント
- requirements.md の「2. 技術スタック」「6. 環境変数」

## ステータス
🔄 作業中（ユーザー対応待ち）

## 次のアクション（ユーザー対応必要）

1. **Python 3.10+のインストール**
   - https://www.python.org/downloads/ からインストール
   - インストール時に「Add Python to PATH」にチェック

2. **依存関係のインストール**
   ```bash
   # 仮想環境の作成
   python -m venv venv

   # 有効化（Windows）
   venv\Scripts\activate

   # 依存関係のインストール
   pip install -r requirements.txt
   ```

3. **Googleサービスアカウントの作成**
   - [docs/google-service-account-setup.md](./google-service-account-setup.md) を参照
   - `service-account.json` を `config/` に配置
   - スプレッドシートに共有設定

4. **.envファイルの作成**
   ```bash
   cp .env.example .env
   # .envを編集してLINEトークンなどを設定
   ```
