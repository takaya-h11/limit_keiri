# Google AI Studio「コクピット」セットアップガイド

このガイドでは、スマホからGoogle AI Studioを使って、売上管理AIコクピットを操作する方法を説明します。

---

## システム構成

```
┌─────────────────────┐
│  LINE（メッセージ） │
└──────────┬──────────┘
           │ コピー
           ▼
┌─────────────────────────────┐
│ Google AI Studio            │
│ （モバイルブラウザ）         │
│ - Gemini 2.0/3.0 Flash/Pro  │
│ - 税抜逆算計算              │
└──────────┬──────────────────┘
           │ Function Calling (HTTPS)
           ▼
┌─────────────────────────────┐
│ REST API Server (Render)    │
│ - record_gym_sale           │
└──────────┬──────────────────┘
           │ gspread
           ▼
┌─────────────────────────────┐
│ Google Spreadsheet          │
│ 「2025年店舗管理シート」    │
└─────────────────────────────┘
```

---

## 重要な注意事項

**Google AI StudioはFunction Callingを直接サポートしていますが、UIから設定できるのはGemini API経由のみです。**

そのため、以下の2つのアプローチがあります：

### アプローチ1: Gemini API（SDK/CURL）- 推奨

Pythonスクリプトまたはcurlコマンドを使用して、Gemini APIからFunction Callingを実行します。

### アプローチ2: Google Apps Script（中間層）

Google Apps Scriptを使って、AI StudioのCode Executionから間接的に呼び出します。

---

## アプローチ1: Gemini API経由（推奨）

### 1-1. APIサーバーをデプロイ

[cloud-deployment.md](./cloud-deployment.md) を参照してRenderにデプロイ。

デプロイ後のURL例：
```
https://limit-sales-api.onrender.com
```

### 1-2. Function Calling JSONスキーマを取得

デプロイ後、以下のURLにアクセスしてスキーマを取得：

```bash
curl https://limit-sales-api.onrender.com/api/schema
```

レスポンス例：
```json
{
  "name": "record_gym_sale",
  "description": "リミット四ツ谷店の売上情報をGoogleスプレッドシートに記録します。税抜単価は既に計算済みの値を受け取ります。",
  "parameters": {
    "type": "object",
    "properties": {
      "day": {
        "type": "integer",
        "description": "日付（数値のみ、例：28）"
      },
      "seller": {
        "type": "string",
        "description": "販売者名（例：服部誉也）"
      },
      "payment_method": {
        "type": "string",
        "description": "決済方法（例：PayPal, PayPay, 現金, クレジットカード）"
      },
      "product_name": {
        "type": "string",
        "description": "商品・サービス名（例：月4回プラン, 月8回プラン, プロテイン）"
      },
      "quantity": {
        "type": "integer",
        "description": "数量（通常は1）"
      },
      "unit_price_excl_tax": {
        "type": "integer",
        "description": "単価（税抜・整数値）。税込金額から floor(税込/1.1) で計算した値。"
      }
    },
    "required": ["day", "seller", "payment_method", "product_name", "quantity", "unit_price_excl_tax"]
  }
}
```

### 1-3. Python SDKでFunction Callingを実装

```python
import google.generativeai as genai
import requests
import json

# Gemini API設定
genai.configure(api_key="YOUR_GEMINI_API_KEY")

# Function declaration
record_sale_function = {
    "name": "record_gym_sale",
    "description": "リミット四ツ谷店の売上情報をGoogleスプレッドシートに記録します。税抜単価は既に計算済みの値を受け取ります。",
    "parameters": {
        "type": "object",
        "properties": {
            "day": {"type": "integer", "description": "日付（数値のみ、例：28）"},
            "seller": {"type": "string", "description": "販売者名（例：服部誉也）"},
            "payment_method": {"type": "string", "description": "決済方法（例：PayPal, PayPay, 現金）"},
            "product_name": {"type": "string", "description": "商品・サービス名（例：月4回プラン）"},
            "quantity": {"type": "integer", "description": "数量（通常は1）"},
            "unit_price_excl_tax": {"type": "integer", "description": "単価（税抜・整数値）"}
        },
        "required": ["day", "seller", "payment_method", "product_name", "quantity", "unit_price_excl_tax"]
    }
}

# Function implementation
def record_gym_sale(day, seller, payment_method, product_name, quantity, unit_price_excl_tax):
    """実際のAPI呼び出し"""
    url = "https://limit-sales-api.onrender.com/api/record_sale"
    payload = {
        "day": day,
        "seller": seller,
        "payment_method": payment_method,
        "product_name": product_name,
        "quantity": quantity,
        "unit_price_excl_tax": unit_price_excl_tax
    }
    response = requests.post(url, json=payload)
    return response.json()

# Gemini modelの設定
model = genai.GenerativeModel(
    'gemini-2.0-flash-exp',
    tools=[record_sale_function]
)

# 使用例
chat = model.start_chat()
response = chat.send_message(
    "12/28 PayPalで月4回プランを35,200円で販売しました。販売者は服部誉也です。"
)

# Function callを実行
for part in response.parts:
    if fn := part.function_call:
        args = dict(fn.args)
        result = record_gym_sale(**args)
        print(f"✅ 売上記録完了: {result}")
```

### 1-4. スマホでの運用フロー

1. **LINEからメッセージをコピー**
2. **上記Pythonスクリプトを実行**（PCまたはサーバー上）
3. **結果を確認**

---

## アプローチ2: Google Apps Script経由

### 2-1. Apps Scriptを作成

Google Sheetsで **Extensions** → **Apps Script** を開き、以下のコードを貼り付け：

```javascript
function recordSaleFromText(text) {
  // Gemini APIでテキストを解析
  const apiKey = "YOUR_GEMINI_API_KEY";
  const url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent";

  const payload = {
    contents: [{
      parts: [{
        text: `以下のテキストから売上情報を抽出してJSON形式で返してください：
${text}

出力形式:
{
  "day": 28,
  "seller": "服部誉也",
  "payment_method": "PayPal",
  "product_name": "月4回プラン",
  "quantity": 1,
  "unit_price_excl_tax": 32000
}

税抜単価は floor(税込金額 / 1.1) で計算してください。`
      }]
    }]
  };

  const options = {
    method: "POST",
    contentType: "application/json",
    headers: {
      "x-goog-api-key": apiKey
    },
    payload: JSON.stringify(payload)
  };

  const response = UrlFetchApp.fetch(url + "?key=" + apiKey, options);
  const result = JSON.parse(response.getContentText());
  const extractedText = result.candidates[0].content.parts[0].text;

  // JSONを抽出（```json ... ``` の中身）
  const jsonMatch = extractedText.match(/```json\n([\s\S]*?)\n```/);
  if (!jsonMatch) {
    throw new Error("JSONが見つかりませんでした");
  }

  const saleData = JSON.parse(jsonMatch[1]);

  // APIサーバーに送信
  const apiUrl = "https://limit-sales-api.onrender.com/api/record_sale";
  const apiOptions = {
    method: "POST",
    contentType: "application/json",
    payload: JSON.stringify(saleData)
  };

  const apiResponse = UrlFetchApp.fetch(apiUrl, apiOptions);
  return JSON.parse(apiResponse.getContentText());
}

// 使用例
function testRecordSale() {
  const result = recordSaleFromText("12/28 PayPalで月4回プラン 35,200円 販売者: 服部誉也");
  Logger.log(result);
}
```

### 2-2. スマホでの運用フロー

1. **LINEからメッセージをコピー**
2. **Google Sheetsアプリを開く**
3. **Apps Script実行ボタンをタップ**（カスタムメニューを作成可能）

---

## アプローチ3: 簡易版（REST API直接呼び出し）

### 3-1. curlコマンドで直接呼び出し

```bash
curl -X POST https://limit-sales-api.onrender.com/api/record_sale \
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

### 3-2. スマホアプリ（Termux等）で実行

AndroidのTermuxアプリなどでcurlコマンドを実行できます。

---

## 推奨アプローチまとめ

| アプローチ | 難易度 | スマホ完結 | AI活用 |
|----------|--------|----------|--------|
| **Gemini API (SDK)** | ⭐⭐⭐ | ❌ (PC必要) | ✅ |
| **Apps Script** | ⭐⭐ | ✅ | ✅ |
| **curl直接呼び出し** | ⭐ | ⚠️ (手動入力) | ❌ |

**推奨: Apps Script**
- スマホ完結
- AI解析機能あり
- Google Sheetsから直接実行

---

## セットアップ手順（Apps Script版）

### 1. APIサーバーをデプロイ

```bash
# Renderにデプロイ（cloud-deployment.md参照）
```

### 2. Gemini API Keyを取得

https://aistudio.google.com/app/apikey

### 3. Apps Scriptをセットアップ

上記のコードを貼り付けて、API Keyを設定。

### 4. カスタムメニューを追加

```javascript
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('売上管理')
    .addItem('売上を記録', 'showInputDialog')
    .addToUi();
}

function showInputDialog() {
  const ui = SpreadsheetApp.getUi();
  const result = ui.prompt(
    '売上情報を入力',
    'LINEからコピーしたテキストを貼り付けてください:',
    ui.ButtonSet.OK_CANCEL
  );

  if (result.getSelectedButton() == ui.Button.OK) {
    const text = result.getResponseText();
    const response = recordSaleFromText(text);
    ui.alert('✅ 売上記録完了', JSON.stringify(response), ui.ButtonSet.OK);
  }
}
```

### 5. スマホから使用

1. **Google Sheetsアプリを開く**
2. **メニュー → 売上管理 → 売上を記録**
3. **LINEからコピーしたテキストを貼り付け**
4. **OKをタップ**

---

## トラブルシューティング

### APIサーバーに接続できない

- ヘルスチェック: `https://your-app.onrender.com/health`
- ログ確認: Render Dashboard → Logs

### Apps Scriptがエラーになる

- API Keyが正しいか確認
- Apps Scriptの実行権限を許可

---

## 次のステップ

- ✅ **APIサーバーをデプロイ**
- ✅ **Apps Scriptをセットアップ**
- ✅ **スマホから売上記録を試す**

---

## 参考リンク

- [Gemini API Documentation](https://ai.google.dev/gemini-api/docs)
- [Google Apps Script Guide](https://developers.google.com/apps-script)
- [Render Deployment Guide](./cloud-deployment.md)
