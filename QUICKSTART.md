# AIコクピット クイックスタートガイド

このガイドでは、売上管理AIコクピットを5分でセットアップする方法を説明します。

---

## 前提条件

- GitHubアカウント
- Google Service Accountの認証情報（JSON）
- Gemini API Key（オプション - Apps Script使用時）

---

## ステップ1: GitHubにプッシュ

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/your-username/limit_keiri.git
git push -u origin main
```

---

## ステップ2: Google Service AccountをBase64エンコード

### Linux/Mac

```bash
cat config/service-account.json | base64 -w 0 > credentials_base64.txt
```

### Windows (PowerShell)

```powershell
[Convert]::ToBase64String([System.IO.File]::ReadAllBytes("config\service-account.json")) | Out-File credentials_base64.txt
```

`credentials_base64.txt` の内容をコピーしておく。

---

## ステップ3: Renderにデプロイ

### 3-1. Renderアカウント作成

https://render.com にアクセスしてサインアップ

### 3-2. Web Serviceを作成

1. Dashboard → **New** → **Web Service**
2. GitHubリポジトリを接続
3. 以下の設定を入力：

| 項目 | 値 |
|-----|-----|
| Name | `limit-sales-mcp` |
| Environment | `Python 3` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `python -m src.mcp_server` |

### 3-3. 環境変数を設定

**Environment** タブで以下を追加：

```bash
MCP_TRANSPORT=sse
LINE_CHANNEL_ACCESS_TOKEN=<LINEトークン>
LINE_CHANNEL_SECRET=<LINEシークレット>
GOOGLE_SHEET_ID=1oklcKDJ3QNVJ3WXawrr2c1oi0mrjyp39HwvyqcTwniE
GOOGLE_APPLICATION_CREDENTIALS_JSON=<Base64エンコードされたJSON>
```

### 3-4. デプロイ

**Create Web Service** をクリック。

数分でデプロイが完了し、以下のようなURLが発行されます：
```
https://limit-sales-mcp.onrender.com
```

---

## ステップ4: 動作確認

### ヘルスチェック

```bash
curl https://your-app.onrender.com/health
```

期待される出力：
```json
{
  "status": "healthy"
}
```

---

## ステップ5: Claude Desktopから接続

### 5-1. Claude Desktopをインストール

https://claude.ai/download からインストール

### 5-2. 設定ファイルを編集

**macOS:**
```bash
nano ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**Windows:**
```
notepad %APPDATA%\Claude\claude_desktop_config.json
```

以下を追加：

```json
{
  "mcpServers": {
    "limit-sales": {
      "transport": {
        "type": "sse",
        "url": "https://your-app.onrender.com/sse"
      }
    }
  }
}
```

### 5-3. Claude Desktopを再起動

設定を反映するため、Claude Desktopを再起動。

### 5-4. 動作確認

Claude Desktopで以下を試す：

```
LINEの最新メッセージを取得して
```

期待される動作：
- `fetch_line_messages` ツールが呼ばれる
- 最新のLINEメッセージが表示される

---

## トラブルシューティング

### デプロイが失敗する

**ログを確認:**
- Render: **Logs** タブ

**よくあるエラー:**
- `ModuleNotFoundError`: requirements.txt を確認
- `Invalid credentials`: 環境変数を確認

### Claude Desktopから接続できない

1. URLが正しいか確認（`/sse` を忘れずに）
2. ヘルスチェックが成功するか確認
3. Claude Desktopを再起動

---

## 次のステップ

- ✅ **LINE Webhook URLを設定**: https://your-app.onrender.com/webhook
- ✅ **売上を記録してみる**: 「12/28 PayPal 月4回プラン 35,200円 をスプレッドシートに記録して」
- ✅ **詳細なドキュメント**: [docs/cloud-deployment.md](docs/cloud-deployment.md)

---

## 参考リンク

- [詳細デプロイガイド](docs/cloud-deployment.md)
- [Gemini接続ガイド](docs/gemini-connection.md)
- [Render Documentation](https://render.com/docs)
