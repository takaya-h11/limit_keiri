# Gemini Gems接続ガイド

このガイドでは、デプロイしたMCPサーバーにGemini/Claude等のAIクライアントから接続する方法を説明します。

---

## 重要な注意事項

**2025年12月時点の状況:**

- **MCP (Model Context Protocol)** は主にClaudeエコシステムで使用されています
- **Gemini API** は現在MCPプロトコルをネイティブサポートしていません
- Gemini APIは **Function Calling** という独自の仕組みを使用します

そのため、以下の2つのアプローチがあります：

1. **Claude Desktop/Claude Code から接続** (推奨・すぐに使える)
2. **Gemini API + カスタムプロキシ** (要開発・将来的な選択肢)

---

## アプローチ1: Claude Desktopから接続（推奨）

### 1-1. デプロイURLの取得

クラウドにデプロイしたMCPサーバーのURL:
```
https://your-app.onrender.com
```

MCPエンドポイント:
```
https://your-app.onrender.com/sse
```

### 1-2. Claude Desktop設定

Claude Desktopの `claude_desktop_config.json` に以下を追加：

**macOS:**
`~/Library/Application Support/Claude/claude_desktop_config.json`

**Windows:**
`%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "limit-sales": {
      "transport": {
        "type": "sse",
        "url": "https://your-app.onrender.com/sse"
      },
      "env": {
        "GOOGLE_SHEET_ID": "1oklcKDJ3QNVJ3WXawrr2c1oi0mrjyp39HwvyqcTwniE"
      }
    }
  }
}
```

### 1-3. Claude Desktopを再起動

設定を反映するため、Claude Desktopを再起動します。

### 1-4. 動作確認

Claude Desktopで以下を試してください：

```
LINEから最新のメッセージを取得して
```

期待される動作：
1. `fetch_line_messages` ツールが呼ばれる
2. 最新のLINEメッセージが表示される

---

## アプローチ2: Claude Code CLIから接続

### 2-1. MCPサーバーを追加

```bash
claude mcp add limit-sales-cloud \
  --transport sse \
  --url https://your-app.onrender.com/sse \
  --scope project
```

### 2-2. 接続確認

```bash
claude mcp list
```

出力例：
```
limit-sales-cloud (sse)
  URL: https://your-app.onrender.com/sse
  Scope: project
  Status: connected
```

### 2-3. 使用例

```bash
claude "LINEの最新メッセージを確認して"
```

---

## アプローチ3: Gemini API（将来的な選択肢）

**注意:** Gemini APIは現在MCPをサポートしていません。以下は参考情報です。

### 3-1. Gemini APIのFunction Calling

Gemini APIで同様の機能を実現するには、MCPサーバーをREST APIラッパーでラップする必要があります。

**アーキテクチャ:**
```
Gemini API
   ↓ (Function Calling)
REST APIプロキシ
   ↓ (MCP Protocol)
MCPサーバー (https://your-app.onrender.com)
```

### 3-2. REST APIプロキシの実装例

`proxy_server.py` (別途実装が必要):

```python
from fastapi import FastAPI, HTTPException
from mcp import ClientSession
import httpx

app = FastAPI()

# MCP Client (SSE transport)
async def get_mcp_client():
    async with httpx.AsyncClient() as client:
        async with ClientSession(
            transport="sse",
            url="https://your-app.onrender.com/sse"
        ) as session:
            return session

@app.post("/api/fetch_line_messages")
async def fetch_line_messages():
    """Gemini Function Calling用エンドポイント"""
    session = await get_mcp_client()
    result = await session.call_tool("fetch_line_messages", {})
    return result

@app.post("/api/record_gym_sale")
async def record_gym_sale(
    day: int,
    seller: str,
    payment_method: str,
    product_name: str,
    quantity: int,
    unit_price_excl_tax: float
):
    """Gemini Function Calling用エンドポイント"""
    session = await get_mcp_client()
    result = await session.call_tool("record_gym_sale", {
        "day": day,
        "seller": seller,
        "payment_method": payment_method,
        "product_name": product_name,
        "quantity": quantity,
        "unit_price_excl_tax": unit_price_excl_tax
    })
    return result
```

### 3-3. Gemini API設定

Gemini API (Python SDK) での使用例：

```python
import google.generativeai as genai

# Function declarations for Gemini
tools = [
    {
        "function_declarations": [
            {
                "name": "fetch_line_messages",
                "description": "LINEから最新のメッセージを取得",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "record_gym_sale",
                "description": "売上情報をスプレッドシートに記録",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "day": {"type": "integer", "description": "日付"},
                        "seller": {"type": "string", "description": "販売者名"},
                        "payment_method": {"type": "string", "description": "決済方法"},
                        "product_name": {"type": "string", "description": "商品名"},
                        "quantity": {"type": "integer", "description": "数量"},
                        "unit_price_excl_tax": {"type": "number", "description": "単価（税抜）"}
                    },
                    "required": ["day", "seller", "payment_method", "product_name", "quantity", "unit_price_excl_tax"]
                }
            }
        ]
    }
]

model = genai.GenerativeModel('gemini-2.0-flash', tools=tools)

# 使用例
response = model.generate_content("LINEの最新メッセージを確認して")
```

**課題:**
- Gemini APIのFunction CallingとMCPプロトコルは互換性がない
- REST APIプロキシを自前で実装する必要がある
- メンテナンスコストが高い

---

## アプローチ4: Google AI Studio（Gems）

**2025年12月時点の状況:**

Google AI Studioの「Gems」機能は、カスタムAIアシスタントを作成できますが、**外部APIとの連携機能は限定的**です。

### 現状の制約

- Gemsは主にプロンプトベースのカスタマイズに特化
- 外部サーバーへのHTTPリクエストは直接サポートされていない
- MCPプロトコルはサポートされていない

### 代替案: Apps Script経由の統合

Google Apps Scriptを使用して、以下のような統合が可能：

```javascript
// Google Apps Script
function fetchLineMessages() {
  const url = "https://your-proxy.onrender.com/api/fetch_line_messages";
  const response = UrlFetchApp.fetch(url, {method: "POST"});
  return JSON.parse(response.getContentText());
}

function recordSale(data) {
  const url = "https://your-proxy.onrender.com/api/record_gym_sale";
  const options = {
    method: "POST",
    contentType: "application/json",
    payload: JSON.stringify(data)
  };
  const response = UrlFetchApp.fetch(url, options);
  return JSON.parse(response.getContentText());
}
```

しかし、これも追加開発が必要で複雑です。

---

## 推奨アプローチまとめ

### ✅ **すぐに使える（推奨）:**

1. **Claude Desktop** から接続
   - MCPネイティブサポート
   - 設定ファイルに1行追加するだけ
   - 追加開発不要

2. **Claude Code CLI** から接続
   - コマンドライン経由で利用
   - CI/CD統合も可能

### ⚠️ **追加開発が必要:**

3. **Gemini API + REST APIプロキシ**
   - MCPプロキシサーバーを自前で実装
   - Gemini Function Callingと統合
   - メンテナンスコストあり

4. **Google Apps Script**
   - スプレッドシートから直接呼び出し
   - Gemsとの統合は困難

---

## 次のステップ

### すぐに試す場合

1. **Claude Desktopをインストール**: https://claude.ai/download
2. **設定ファイルを編集** (上記参照)
3. **Claude Desktopを再起動**
4. **「LINEの最新メッセージを取得して」と指示**

### Gemini統合を検討する場合

1. **REST APIプロキシの実装を検討**
2. **Gemini APIのFunction Calling仕様を確認**
3. **プロキシサーバーのデプロイ**

---

## よくある質問

### Q1: Gemini GemsでMCPサーバーを使えますか？

**A:** 2025年12月時点では、Google AI Studio（Gems）はMCPプロトコルをサポートしていません。Claude Desktop/Claude Codeの使用を推奨します。

### Q2: 将来的にGeminiがMCPをサポートする可能性は？

**A:** GoogleがMCPプロトコルを採用するかは不明です。現在はFunction Calling APIが推奨されています。

### Q3: Claude以外のMCP対応クライアントはありますか？

**A:** MCP仕様はオープンですが、現時点ではClaudeエコシステムが主な実装です。今後、他のAIプラットフォームが採用する可能性があります。

---

## 参考リンク

- [MCP Documentation](https://modelcontextprotocol.io)
- [Claude Desktop Documentation](https://docs.anthropic.com/claude/docs)
- [Gemini API Function Calling](https://ai.google.dev/gemini-api/docs/function-calling)
- [FastMCP GitHub](https://github.com/jlowin/fastmcp)
