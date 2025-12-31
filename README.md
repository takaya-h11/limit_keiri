# リミット四ツ谷店 売上管理「AIコクピット」

**スマホ完結 × AI解析 × クラウド連携**で売上記録を自動化

## 概要

パーソナルトレーニングジム「リミット四ツ谷店」の売上管理を**スマホから直接**操作できる「AIコクピット」システム。

### ワークフロー

1. **LINE** → 売上報告メッセージをコピー
2. **Google AI Studio（スマホブラウザ）** → Geminiが解析・税抜逆算
3. **クラウドAPI（Render）** → Googleスプレッドシートに記録

### 設計思想

- **確実性**: AIが解釈した内容を人間が確認してから実行
- **スマホ完結**: LINEコピー → AI Studio貼り付け → 完了
- **低コスト**: 自宅PC不要、PaaSで24時間稼働
- **純粋な道具**: 計算はAI、記録はAPI

## 技術スタック

- **ホスト（Brain）**: Google AI Studio（Gemini 2.0/3.0 Flash/Pro）
- **サーバー（Hands）**: Python 3.10+ / FastAPI
- **データ（Storage）**: Google Sheets API
- **デプロイ**: Render（PaaS）

## プロジェクト構成

```
limit_keiri/
├── docs/                               # ドキュメント
│   ├── ai-studio-setup.md             # Google AI Studio接続ガイド ⭐
│   ├── cloud-deployment.md            # クラウドデプロイガイド
│   └── google-service-account-setup.md
├── src/                                # ソースコード
│   ├── __init__.py
│   ├── config.py                      # 環境変数管理
│   ├── api_server.py                  # REST APIサーバー（メイン） ⭐
│   ├── mcp_server.py                  # MCPサーバー（オプション）
│   └── google_sheets.py               # Google Sheets連携
├── tests/                              # テストコード
│   ├── __init__.py
│   └── test_tax_calculator.py
├── config/                             # 設定ファイル
│   └── service-account.json           # Googleサービスアカウント（gitignore）
├── gemini_function_schema.json        # Gemini Function Calling定義 ⭐
├── .env                                # 環境変数（gitignore）
├── .env.example                       # 環境変数テンプレート
├── Procfile                           # Renderデプロイ設定
├── requirements.txt                   # Python依存関係
└── README.md                          # このファイル
```

## セットアップ

### 1. Python 3.10+のインストール

```bash
# Pythonバージョン確認
python --version

# 3.10未満の場合は https://www.python.org/downloads/ からインストール
```

### 2. 依存関係のインストール

```bash
# 仮想環境の作成（推奨）
python -m venv venv

# 仮想環境の有効化
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 依存関係のインストール
pip install -r requirements.txt
```

### 3. 環境変数の設定

```bash
# .env.example をコピー
cp .env.example .env

# .env を編集して実際の値を設定
```

`.env` の設定項目：

```env
# Google Sheets API
GOOGLE_SHEET_ID=1oklcKDJ3QNVJ3WXawrr2c1oi0mrjyp39HwvyqcTwniE
SERVICE_ACCOUNT_FILE=config/service-account.json

# オプション
LOG_LEVEL=INFO
```

### 4. Googleサービスアカウントの設定

[docs/google-service-account-setup.md](docs/google-service-account-setup.md) を参照して、Googleサービスアカウントを作成してください。

**重要**:
1. `service-account.json` を `config/` ディレクトリに配置
2. スプレッドシートにサービスアカウントのメールアドレスを共有

## API Endpoint

このAPIサーバーは売上記録用のエンドポイントを提供します：

### `POST /api/record_sale`

売上情報をスプレッドシートに記録

**リクエスト:**
```json
{
    "day": 28,
    "seller": "服部誉也",
    "payment_method": "PayPal",
    "product_name": "月4回プラン",
    "quantity": 1,
    "unit_price_excl_tax": 32000
}
```

**レスポンス:**
```json
{
    "success": true,
    "row": 15,
    "message": "売上を 15 行目に記録しました"
}
```

### `GET /api/schema`

Gemini Function Calling用のJSONスキーマを取得

**レスポンス:** [gemini_function_schema.json](gemini_function_schema.json:1)

## デプロイ方法

### ローカル開発

詳細は「使用方法」セクションを参照してください。

### クラウドデプロイ（Render/Railway等）

クラウド環境へのデプロイ手順は **[docs/cloud-deployment.md](docs/cloud-deployment.md)** を参照してください。

#### クイックスタート（Render）

1. **Renderアカウント作成**: https://render.com
2. **リポジトリをプッシュ**: GitHubにコードをプッシュ
3. **Web Service作成**: Render Dashboardで New → Web Service
4. **環境変数設定**:
   ```bash
   MCP_TRANSPORT=sse
   LINE_CHANNEL_ACCESS_TOKEN=your_token
   LINE_CHANNEL_SECRET=your_secret
   GOOGLE_SHEET_ID=your_sheet_id
   GOOGLE_APPLICATION_CREDENTIALS_JSON=<Base64 encoded JSON>
   ```
5. **デプロイ**: 自動的にデプロイが開始されます

詳細手順とGemini接続方法は [docs/gemini-connection.md](docs/gemini-connection.md) を参照してください。

---

## 使用方法

### ローカル開発

#### REST APIサーバーの起動

```bash
# APIサーバーを起動（ポート8080）
python -m src.api_server

# カスタムポートで起動
PORT=8000 python -m src.api_server
```

#### 動作確認

```bash
# ヘルスチェック
curl http://localhost:8080/health

# スキーマ取得
curl http://localhost:8080/api/schema

# 売上記録（テスト）
curl -X POST http://localhost:8080/api/record_sale \
  -H "Content-Type: application/json" \
  -d '{
    "day": 28,
    "seller": "服部誉也",
    "payment_method": "PayPal",
    "product_name": "月4回プラン",
    "quantity": 1,
    "unit_price_excl_tax": 32000
  }'
```

### クラウドデプロイ

詳細は **[docs/cloud-deployment.md](docs/cloud-deployment.md)** を参照。

### Google AI Studioからの使用

詳細は **[docs/ai-studio-setup.md](docs/ai-studio-setup.md)** を参照。

#### クイックスタート

1. **LINEからメッセージをコピー**
   ```
   12/28 PayPalで月4回プラン 35,200円 販売しました
   ```

2. **Google AI Studioで解析**
   - Geminiが税抜金額を計算（35,200円 → 32,000円）
   - Function Callingで `record_gym_sale` を呼び出し

3. **スプレッドシートに自動記録**

## 開発

### テストの実行

```bash
# ユニットテストの実行
pytest tests/

# カバレッジ付きで実行
pytest --cov=src tests/
```

### コードフォーマット

```bash
# black を使用（オプション）
pip install black
black src/ tests/
```

## トラブルシューティング

### Python実行時にモジュールが見つからない

```bash
# 仮想環境が有効化されているか確認
which python  # Linuxvenv内のpythonを指しているはず

# 依存関係を再インストール
pip install -r requirements.txt
```

### Google Sheets API接続エラー

1. `service-account.json` が正しい場所にあるか確認
2. スプレッドシートにサービスアカウントのメールを共有しているか確認
3. Google Sheets API が有効化されているか確認

詳細は [docs/google-service-account-setup.md](docs/google-service-account-setup.md) を参照

### LINE API接続エラー

1. `.env` の `LINE_CHANNEL_ACCESS_TOKEN` が正しいか確認
2. LINE Developersコンソールでチャネル設定を確認

## 開発ロードマップ

開発の進捗は [docs/00-index.md](docs/00-index.md) を参照してください。

- [x] チケット01: プロジェクトセットアップ
- [x] チケット02: Google Sheets API連携
- [x] チケット03: LINE API連携（Webhook実装）
- [x] チケット04: 売上記録機能
- [x] チケット05: 税計算ロジック
- [x] チケット06: MCPサーバー実装
- [ ] チケット07: テストとデプロイ

## ライセンス

MIT License

## 作成者

Claude Code + 服部誉也
