"""
REST API Server for Google AI Studio Integration
Gemini APIのFunction Callingから呼び出すためのREST APIサーバー
"""

import logging
import os
import json
from typing import Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import google.generativeai as genai

from .config import Config
from .google_sheets import GoogleSheetsClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Limit Yotsuya Sales API",
    description="売上管理AI「コクピット」API - Google AI Studio連携用",
    version="1.0.0"
)

# CORS設定（Google AI Studioからのアクセスを許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切に制限してください
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Google Sheets client (lazy initialization)
sheets_client = None

# Gemini model (lazy initialization)
gemini_model = None

# 顧客リスト（最新）
KNOWN_CUSTOMERS = [
    "岩佐将平",
    "堀内さやか",
    "坂上明彦",
    "河村直子",
    "金子弘美",
    "平安彦",
    "西島優樹",
    "桜井彰人",
    "花田幸典",
    "大塚由美",
    "新津七海",
    "冨田博信",
    "竹内優馬",
    "荻野悠加"
]


def get_gemini_model():
    """Get or create Gemini model"""
    global gemini_model
    if gemini_model is None:
        genai.configure(api_key=Config.GEMINI_API_KEY)
        # gemini-1.5-flash-latest: 安定版、無料枠が大きい（15 RPM, 1M TPM）
        gemini_model = genai.GenerativeModel('gemini-1.5-flash-latest')
    return gemini_model


def get_sheets_client() -> GoogleSheetsClient:
    """Get or create Google Sheets client"""
    global sheets_client
    if sheets_client is None:
        sheets_client = GoogleSheetsClient()
        sheets_client.connect()
    return sheets_client


# Request models
class RecordSaleRequest(BaseModel):
    """売上記録リクエスト"""
    day: int
    seller: str  # 顧客名（D列）
    payment_method: str
    product_name: str
    quantity: int
    unit_price_excl_tax: int


class ProcessTextRequest(BaseModel):
    """テキスト処理リクエスト"""
    text: str


def parse_sale_text_with_gemini(text: str) -> Dict:
    """
    Gemini APIを使ってLINEメッセージから売上情報を抽出

    Args:
        text: LINEメッセージ（例：「12/28 PayPalで月4回プラン 35,200円 販売しました。顧客: 岩佐将平」）

    Returns:
        dict: {
            "day": int,
            "seller": str,
            "payment_method": str,
            "product_name": str,
            "quantity": int,
            "unit_price_incl_tax": int  # 税込
        }
    """
    logger.info(f"[Gemini解析開始] 入力テキスト: {text}")

    model = get_gemini_model()

    prompt = f"""
以下のテキストから売上情報を抽出してください。

テキスト: {text}

以下のJSON形式で回答してください（JSONのみを返し、他の文章は不要です）:
{{
    "day": 日付（数値のみ、例：28）,
    "seller": "顧客名",
    "payment_method": "決済方法（PayPal, PayPay, 現金, クレジットカードのいずれか）",
    "product_name": "商品・サービス名",
    "quantity": 数量（数値、通常は1）,
    "unit_price_incl_tax": 税込単価（数値のみ、カンマなし）
}}

重要:
- sellerは「顧客名」を指します（販売者名ではありません）
- unit_price_incl_taxは税込金額です
- quantityが明示されていない場合は1を返してください
"""

    try:
        response = model.generate_content(prompt)
        logger.info(f"[Gemini応答] {response.text}")

        # JSONを抽出（```json ... ``` の形式に対応）
        response_text = response.text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]  # ```json を削除
        if response_text.startswith("```"):
            response_text = response_text[3:]  # ``` を削除
        if response_text.endswith("```"):
            response_text = response_text[:-3]  # ``` を削除

        result = json.loads(response_text.strip())
        logger.info(f"[Gemini解析成功] {result}")
        return result

    except Exception as e:
        logger.error(f"[Gemini解析失敗] エラー: {e}")
        raise HTTPException(status_code=500, detail=f"Gemini APIでのテキスト解析に失敗しました: {str(e)}")


@app.get("/", response_class=HTMLResponse)
async def root():
    """売上記録専用フロントエンド"""
    html_content = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>リミット四ツ谷店 売上記帳</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            max-width: 500px;
            width: 100%;
            padding: 30px;
        }
        h1 {
            color: #333;
            font-size: 24px;
            margin-bottom: 8px;
            text-align: center;
        }
        .subtitle {
            color: #666;
            font-size: 14px;
            text-align: center;
            margin-bottom: 24px;
        }
        label {
            display: block;
            color: #555;
            font-weight: 600;
            margin-bottom: 8px;
            font-size: 14px;
        }
        textarea {
            width: 100%;
            min-height: 120px;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
            font-family: inherit;
            resize: vertical;
            transition: border-color 0.3s;
        }
        textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        .button-container {
            margin-top: 20px;
        }
        button {
            width: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 16px;
            border-radius: 8px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
        }
        button:active {
            transform: translateY(0);
        }
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }
        .result {
            margin-top: 20px;
            padding: 16px;
            border-radius: 8px;
            font-size: 16px;
            display: none;
        }
        .result.success {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
        }
        .result.error {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
        }
        .loading {
            text-align: center;
            color: #667eea;
            font-weight: 600;
            margin-top: 12px;
            display: none;
        }
        .example {
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 12px;
            margin-top: 16px;
            border-radius: 4px;
            font-size: 13px;
            color: #555;
        }
        .example-title {
            font-weight: 600;
            margin-bottom: 8px;
            color: #333;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏋️ リミット四ツ谷店</h1>
        <div class="subtitle">売上記帳 AIコクピット</div>

        <form id="saleForm">
            <label for="saleText">LINEメッセージを貼り付け:</label>
            <textarea
                id="saleText"
                name="text"
                placeholder="例: 12/28 PayPalで月4回プラン 35,200円 販売しました。顧客: 岩佐将平"
                required
            ></textarea>

            <div class="example">
                <div class="example-title">📝 入力例:</div>
                12/28 PayPalで月4回プラン 35,200円 販売しました。顧客: 岩佐将平
            </div>

            <div class="button-container">
                <button type="submit" id="submitBtn">記帳実行</button>
            </div>
        </form>

        <div class="loading" id="loading">処理中...</div>
        <div class="result" id="result"></div>
    </div>

    <script>
        const form = document.getElementById('saleForm');
        const submitBtn = document.getElementById('submitBtn');
        const loading = document.getElementById('loading');
        const result = document.getElementById('result');

        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            const text = document.getElementById('saleText').value.trim();
            if (!text) {
                showResult('テキストを入力してください', 'error');
                return;
            }

            // UI状態を更新
            submitBtn.disabled = true;
            loading.style.display = 'block';
            result.style.display = 'none';

            try {
                const response = await fetch('/api/process_and_record', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ text })
                });

                const data = await response.json();

                if (response.ok && data.success) {
                    showResult(data.message, 'success');
                    // 成功したらテキストエリアをクリア
                    document.getElementById('saleText').value = '';
                } else {
                    showResult(data.detail || data.message || '記帳に失敗しました', 'error');
                }
            } catch (error) {
                showResult('通信エラーが発生しました: ' + error.message, 'error');
            } finally {
                submitBtn.disabled = false;
                loading.style.display = 'none';
            }
        });

        function showResult(message, type) {
            result.textContent = message;
            result.className = 'result ' + type;
            result.style.display = 'block';
        }
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)


@app.get("/health")
async def health():
    """ヘルスチェック"""
    try:
        # Google Sheets接続確認
        client = get_sheets_client()
        return {
            "status": "healthy",
            "google_sheets": "connected",
            "spreadsheet": client.spreadsheet.title if client.spreadsheet else "not connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@app.post("/api/record_sale")
async def record_sale(request: RecordSaleRequest) -> Dict:
    """
    売上情報をスプレッドシートに記録

    Args:
        request: 売上記録リクエスト

    Returns:
        dict: {
            "success": bool,
            "row": int,
            "message": str,
            "sheet_name": str
        }
    """
    logger.info("=" * 80)
    logger.info("[API] POST /api/record_sale - リクエスト受信")
    logger.info(f"[リクエストデータ] {request.dict()}")

    try:
        client = get_sheets_client()

        logger.info("[処理開始] Google Sheetsクライアントを取得しました")

        # 顧客名の検証（警告のみ、処理は続行）
        if request.seller not in KNOWN_CUSTOMERS:
            logger.warning(f"[顧客名警告] '{request.seller}' は既知の顧客リストにありません。新規顧客の可能性があります。")

        result = client.record_sale(
            day=request.day,
            seller=request.seller,
            payment_method=request.payment_method,
            product_name=request.product_name,
            quantity=request.quantity,
            unit_price_excl_tax=request.unit_price_excl_tax
        )

        if result.get("success"):
            logger.info(f"[API成功] {result.get('message')} (シート: {result.get('sheet_name')})")
        else:
            logger.error(f"[API失敗] {result.get('message')}")

        logger.info("=" * 80)
        return result

    except Exception as e:
        logger.error(f"[API例外] エラーが発生しました: {e}", exc_info=True)
        logger.info("=" * 80)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/process_and_record")
async def process_and_record(request: ProcessTextRequest) -> Dict:
    """
    テキストを解析して売上を記帳（ワンストップ処理）

    Args:
        request: テキスト処理リクエスト

    Returns:
        dict: {
            "success": bool,
            "message": str,
            "row": int,
            "sheet_name": str,
            "parsed_data": dict
        }
    """
    logger.info("=" * 80)
    logger.info("[API] POST /api/process_and_record - リクエスト受信")
    logger.info(f"[入力テキスト] {request.text}")

    try:
        # 1. Gemini APIでテキスト解析
        parsed_data = parse_sale_text_with_gemini(request.text)

        # 2. 税抜単価を計算: floor(税込 / 1.1)
        unit_price_incl_tax = parsed_data["unit_price_incl_tax"]
        unit_price_excl_tax = int(unit_price_incl_tax / 1.1)
        logger.info(f"[税抜計算] 税込: {unit_price_incl_tax} → 税抜: {unit_price_excl_tax}")

        # 3. Google Sheetsに記帳
        client = get_sheets_client()
        logger.info("[処理開始] Google Sheetsクライアントを取得しました")

        # 顧客名の検証（警告のみ、処理は続行）
        seller = parsed_data["seller"]
        if seller not in KNOWN_CUSTOMERS:
            logger.warning(f"[顧客名警告] '{seller}' は既知の顧客リストにありません。新規顧客の可能性があります。")

        result = client.record_sale(
            day=parsed_data["day"],
            seller=seller,
            payment_method=parsed_data["payment_method"],
            product_name=parsed_data["product_name"],
            quantity=parsed_data["quantity"],
            unit_price_excl_tax=unit_price_excl_tax
        )

        if result.get("success"):
            # 成功メッセージをカスタマイズ
            custom_message = f"✅ {seller}様の売上 {unit_price_incl_tax:,}円を記帳しました（{result.get('sheet_name')} {result.get('row')}行目）"
            logger.info(f"[API成功] {custom_message}")

            logger.info("=" * 80)
            return {
                "success": True,
                "message": custom_message,
                "row": result.get("row"),
                "sheet_name": result.get("sheet_name"),
                "parsed_data": {
                    **parsed_data,
                    "unit_price_excl_tax": unit_price_excl_tax
                }
            }
        else:
            logger.error(f"[API失敗] {result.get('message')}")
            logger.info("=" * 80)
            raise HTTPException(status_code=500, detail=result.get("message"))

    except HTTPException:
        # HTTPExceptionはそのまま再スロー
        logger.info("=" * 80)
        raise
    except Exception as e:
        logger.error(f"[API例外] エラーが発生しました: {e}", exc_info=True)
        logger.info("=" * 80)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/schema")
async def get_schema():
    """
    Google AI Studio用のFunction Calling JSONスキーマを返す

    Returns:
        dict: OpenAPI形式のスキーマ
    """
    return {
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
                    "description": "顧客名（D列）",
                    "enum": [
                        "岩佐将平",
                        "堀内さやか",
                        "坂上明彦",
                        "河村直子",
                        "金子弘美",
                        "平安彦",
                        "西島優樹",
                        "桜井彰人",
                        "花田幸典",
                        "大塚由美",
                        "新津七海",
                        "冨田博信",
                        "竹内優馬",
                        "荻野悠加"
                    ]
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


def run_server(host: str = "0.0.0.0", port: int = None):
    """
    Run the API server

    Args:
        host: Host to bind to
        port: Port to bind to (defaults to PORT env var or 8080)
    """
    import uvicorn

    if port is None:
        port = int(os.getenv("PORT", 8080))

    # Validate configuration
    Config.validate()
    logger.info("Configuration validated successfully")

    logger.info(f"Starting API server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
