"""
MCP Server for Limit Yotsuya Store Sales Management
FastMCPを使用したMCPサーバー実装

クラウドデプロイ対応:
- 環境変数 MCP_TRANSPORT で transport 方式を切り替え（stdio or sse）
- 環境変数 PORT でリッスンポートを指定（デフォルト: 8080）
"""

import logging
import os
from typing import Dict

from mcp.server.fastmcp import FastMCP

from .config import Config
from .google_sheets import GoogleSheetsClient

# Configure logging to stderr (IMPORTANT: avoid stdout for STDIO servers)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]  # Uses stderr by default
)
logger = logging.getLogger(__name__)

# Create MCP server instance
mcp = FastMCP("LimitYotsuya")

# Initialize Google Sheets client (will be initialized on first use)
sheets_client = None


def get_sheets_client() -> GoogleSheetsClient:
    """Get or create Google Sheets client"""
    global sheets_client
    if sheets_client is None:
        sheets_client = GoogleSheetsClient()
        sheets_client.connect()
    return sheets_client


@mcp.tool()
def record_gym_sale(
    day: int,
    seller: str,
    payment_method: str,
    product_name: str,
    quantity: int,
    unit_price_excl_tax: float
) -> Dict:
    """
    売上情報をスプレッドシートに記録

    Args:
        day: 日付（数値のみ、例：28）
        seller: 販売者名（例：服部誉也）
        payment_method: 決済方法（例：PayPal, PayPay, 現金）
        product_name: 商品・サービス名（例：月4回プラン）
        quantity: 数量
        unit_price_excl_tax: 単価（税抜）

    Returns:
        dict: {
            "success": bool,
            "row": int,
            "message": str
        }
    """
    try:
        client = get_sheets_client()
        result = client.record_sale(
            day=day,
            seller=seller,
            payment_method=payment_method,
            product_name=product_name,
            quantity=quantity,
            unit_price_excl_tax=unit_price_excl_tax
        )

        return result
    except Exception as e:
        logger.error(f"Error recording sale: {e}")
        return {
            "success": False,
            "row": 0,
            "message": f"エラー: {str(e)}"
        }


def main():
    """Main entry point for the MCP server"""
    try:
        # Validate configuration
        Config.validate()
        logger.info("Configuration validated successfully")

        # Determine transport mode from environment variable
        # - stdio: For local development (Claude Desktop, etc.)
        # - sse: For cloud deployment (Render, Railway, etc.)
        transport = os.getenv("MCP_TRANSPORT", "stdio").lower()

        if transport == "sse":
            # Cloud deployment mode (SSE transport)
            port = int(os.getenv("PORT", 8080))
            host = os.getenv("HOST", "0.0.0.0")

            logger.info(f"Starting MCP server in SSE mode on {host}:{port}")
            mcp.run(transport="sse", host=host, port=port)
        else:
            # Local development mode (STDIO transport)
            logger.info("Starting MCP server in STDIO mode")
            mcp.run(transport="stdio")

    except Exception as e:
        logger.error(f"Failed to start MCP server: {e}")
        raise


if __name__ == "__main__":
    main()
