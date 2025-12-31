"""
REST API Server for Google AI Studio Integration
Gemini APIのFunction Callingから呼び出すためのREST APIサーバー
"""

import logging
import os
from typing import Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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
    seller: str
    payment_method: str
    product_name: str
    quantity: int
    unit_price_excl_tax: int


@app.get("/")
async def root():
    """ヘルスチェックエンドポイント"""
    return {
        "status": "ok",
        "service": "Limit Yotsuya Sales API",
        "version": "1.0.0",
        "description": "売上管理AI「コクピット」"
    }


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
