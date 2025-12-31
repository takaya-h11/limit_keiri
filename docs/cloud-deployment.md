# クラウドデプロイガイド

このガイドでは、MCPサーバーをクラウド（PaaS）にデプロイする手順を説明します。

## 対応プラットフォーム

- **Render** (推奨)
- **Railway**
- **Heroku**
- その他のPythonをサポートするPaaS

---

## 前提条件

1. GitHubリポジトリにコードをプッシュ済み
2. 以下の認証情報を準備：
   - LINE Channel Access Token
   - LINE Channel Secret
   - Google Sheets ID
   - Google Service Account JSON（Base64エンコード）

---

## 1. Renderへのデプロイ

### 1-1. Renderアカウント作成

https://render.com でアカウントを作成

### 1-2. 新規Web Serviceを作成

1. **Dashboard** → **New** → **Web Service**
2. GitHubリポジトリを接続
3. 以下の設定を入力：

| 項目 | 値 |
|-----|-----|
| Name | `limit-sales-mcp` (任意) |
| Environment | `Python 3` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `python -m src.mcp_server` |

### 1-3. 環境変数の設定

**Environment** タブで以下を設定：

```bash
# MCP Server設定
MCP_TRANSPORT=sse

# LINE API
LINE_CHANNEL_ACCESS_TOKEN=your_line_channel_access_token
LINE_CHANNEL_SECRET=your_line_channel_secret

# Google Sheets
GOOGLE_SHEET_ID=1oklcKDJ3QNVJ3WXawrr2c1oi0mrjyp39HwvyqcTwniE

# Google Service Account（後述）
GOOGLE_APPLICATION_CREDENTIALS_JSON=<Base64エンコードされたJSON>
```

### 1-4. Google Service Accountの設定

`config/service-account.json` をBase64エンコードして環境変数に設定：

**Linux/Mac:**
```bash
cat config/service-account.json | base64 -w 0
```

**Windows (PowerShell):**
```powershell
[Convert]::ToBase64String([System.IO.File]::ReadAllBytes("config\service-account.json"))
```

エンコードされた文字列を `GOOGLE_APPLICATION_CREDENTIALS_JSON` に設定。

### 1-5. デプロイ

**Create Web Service** をクリックしてデプロイ開始。

デプロイ後、以下のようなURLが発行されます：
```
https://limit-sales-mcp.onrender.com
```

---

## 2. Railwayへのデプロイ

### 2-1. Railwayアカウント作成

https://railway.app でアカウントを作成

### 2-2. プロジェクト作成

1. **New Project** → **Deploy from GitHub repo**
2. リポジトリを選択

### 2-3. 環境変数の設定

**Variables** タブで以下を設定：

```bash
MCP_TRANSPORT=sse
LINE_CHANNEL_ACCESS_TOKEN=your_token
LINE_CHANNEL_SECRET=your_secret
GOOGLE_SHEET_ID=your_sheet_id
GOOGLE_APPLICATION_CREDENTIALS_JSON=<Base64 encoded JSON>
```

### 2-4. デプロイコマンド設定

**Settings** → **Start Command**:
```bash
python -m src.mcp_server
```

### 2-5. デプロイ

自動的にデプロイが開始されます。

デプロイ後、以下のようなURLが発行されます：
```
https://limit-sales-mcp.up.railway.app
```

---

## 3. 環境変数の詳細

### 必須環境変数

| 環境変数 | 説明 | 例 |
|---------|------|-----|
| `MCP_TRANSPORT` | Transport方式（必ず `sse`） | `sse` |
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Bot アクセストークン | `abc123...` |
| `LINE_CHANNEL_SECRET` | LINE Bot チャネルシークレット | `def456...` |
| `GOOGLE_SHEET_ID` | Google Sheets ID | `1oklcKD...` |

### Google認証（2つの方法）

#### 方法1: JSON文字列（推奨）

```bash
GOOGLE_APPLICATION_CREDENTIALS_JSON=<Base64エンコードされたJSON>
```

#### 方法2: ファイルパス（非推奨・ローカル開発のみ）

```bash
SERVICE_ACCOUNT_FILE=config/service-account.json
```

クラウドデプロイでは **方法1** を推奨。

---

## 4. Google Service Account設定の修正

クラウド環境では、`service-account.json` ファイルをアップロードできません。
代わりに、環境変数からJSONを読み込むように `config.py` を修正する必要があります。

### 4-1. config.pyの修正

`src/config.py` に以下の処理を追加：

```python
import os
import json
import base64
from pathlib import Path

class Config:
    # ... 既存のコード ...

    @staticmethod
    def get_google_credentials():
        """
        Google Service Account認証情報を取得

        優先順位:
        1. GOOGLE_APPLICATION_CREDENTIALS_JSON（Base64エンコード）
        2. SERVICE_ACCOUNT_FILE（ファイルパス）
        """
        # 環境変数から取得（クラウドデプロイ用）
        credentials_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
        if credentials_json:
            try:
                # Base64デコード
                decoded = base64.b64decode(credentials_json)
                return json.loads(decoded)
            except Exception as e:
                raise ValueError(f"Invalid GOOGLE_APPLICATION_CREDENTIALS_JSON: {e}")

        # ファイルから取得（ローカル開発用）
        service_account_file = os.getenv("SERVICE_ACCOUNT_FILE", "config/service-account.json")
        if Path(service_account_file).exists():
            with open(service_account_file, 'r') as f:
                return json.load(f)

        raise ValueError("Google credentials not found. Set GOOGLE_APPLICATION_CREDENTIALS_JSON or SERVICE_ACCOUNT_FILE")
```

### 4-2. google_sheets.pyの修正

`src/google_sheets.py` で認証方法を変更：

```python
from .config import Config

class GoogleSheetsClient:
    def connect(self):
        """Connect to Google Sheets API"""
        try:
            # 認証情報を取得
            credentials_dict = Config.get_google_credentials()

            # gspread認証
            credentials = service_account.Credentials.from_service_account_info(
                credentials_dict,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )

            self.client = gspread.authorize(credentials)
            # ... 以下省略 ...
```

---

## 5. デプロイ後の確認

### 5-1. ヘルスチェック

デプロイ後、以下のURLにアクセスしてサーバーが起動しているか確認：

```bash
curl https://your-app.onrender.com/health
```

期待されるレスポンス：
```json
{
  "status": "healthy",
  "server": "limit-sales-mcp",
  "version": "1.0.0"
}
```

### 5-2. MCPエンドポイント確認

MCPサーバーのSSEエンドポイント：
```
https://your-app.onrender.com/sse
```

---

## 6. トラブルシューティング

### デプロイが失敗する

**ログを確認:**
- Render: Logs タブ
- Railway: Deployments → Logs

**よくあるエラー:**
1. `ModuleNotFoundError`: requirements.txt を確認
2. `Invalid credentials`: 環境変数を確認
3. `Port already in use`: PORT環境変数を確認

### Google Sheets接続エラー

1. `GOOGLE_APPLICATION_CREDENTIALS_JSON` が正しくBase64エンコードされているか確認
2. サービスアカウントにスプレッドシートの編集権限があるか確認

### LINE Webhook接続エラー

1. LINE Developersコンソールで Webhook URL を設定：
   ```
   https://your-app.onrender.com/webhook
   ```
2. Webhook URLの検証が成功するか確認

---

## 7. 次のステップ

デプロイ完了後、以下を実施：

1. ✅ **ヘルスチェックでサーバーが起動していることを確認**
2. ✅ **LINE Webhook URLを設定**
3. ✅ **Gemini/Claude からMCPサーバーに接続** → [gemini-connection.md](./gemini-connection.md)

---

## 参考リンク

- [Render Documentation](https://render.com/docs)
- [Railway Documentation](https://docs.railway.app)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
