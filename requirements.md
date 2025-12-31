# 要件定義書：リミット四ツ谷店 売上管理連携MCPサーバー

## 1. プロジェクト概要
パーソナルトレーニングジム「リミット四ツ谷店」の売上管理を効率化するため、LINEで受信した曖昧な売上報告をGeminiが解釈し、既存のGoogleスプレッドシート（2025年店舗管理シート）の適切な列に自動入力するMCPサーバーを構築する。

## 2. 技術スタック
- **言語**: Python 3.10+
- **MCPフレームワーク**: FastMCP
- **API連携**:
  - LINE Messaging API (`line-bot-sdk`)
  - Google Sheets API (`gspread`, `google-auth`)
- **環境管理**: `python-dotenv`

## 3. スプレッドシート仕様
- **対象ファイル名**: 2025年店舗管理シート
- **対象シート**: 実行時の月に応じたシート（例：「12 月度」）
- **データ構造**:
  - **ヘッダー行**: 4行目（No. / 決済 / 日 / 販売者 / 決済方法 / 商品・サービス名 / 数量 / 単価（税抜）...）
  - **入力開始行**: 5行目以降の最初の空行
  - **入力対象列**:
    - **C列 (日)**: 数値のみ入力（LINEの「12/28」から「28」を抽出）
    - **D列 (販売者)**: M列にあるトレーナー名リストから抽出。不明な場合は「服部誉也」
    - **E列 (決済方法)**: PayPal, PayPay, 現金 等
    - **F列 (商品・サービス名)**: 月4回プラン, パーソナルトレーニング 等
    - **G列 (数量)**: 数値（不明な場合は1）
    - **H列 (単価（税抜）)**: 税込価格から逆算した数値を入力
- **非操作対象**:
  - **I列・J列**: スプレッドシート側の数式（合計）を維持するため、プログラムからは書き込まない。

## 4. 計算ロジック（税込から税抜への逆算）
ユーザー（服部）がLINEで「税込価格」を報告した場合、以下の計算を行う。
- **計算式**: `単価（税抜） = 税込価格 / 1.1`
- **端数処理**: 小数点以下切り捨て（またはスプレッドシートの運用ルールに従う）

## 5. 実装ツール (MCP Tools)
### ① `fetch_line_messages`
- LINE Messaging APIから最新のトーク履歴を取得し、Geminiに渡す。

### ② `get_sheet_info`
- 現在のシートのヘッダー情報と、次にデータを書き込むべき空行の番号を特定する。

### ③ `record_gym_sale`
- **引数**: `day`, `seller`, `payment_method`, `product_name`, `quantity`, `unit_price_excl_tax`
- スプレッドシートの特定行（C列〜H列）にデータを書き込む。
- B列のチェックボックスはデフォルトで空欄（未チェック）とする。

## 6. 環境変数 (.env)
```env
LINE_CHANNEL_ACCESS_TOKEN=your_line_token
LINE_CHANNEL_SECRET=your_line_secret
GOOGLE_SHEET_ID=1oklcKDJ3QNVJ3WXawrr2c1oi0mrjyp39HwvyqcTwniE
SERVICE_ACCOUNT_FILE=path/to/your/service-account.json
```
