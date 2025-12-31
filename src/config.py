"""
Configuration loader for the MCP server
環境変数を読み込み、設定を管理
"""

import os
import json
import base64
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration"""

    # LINE Messaging API
    LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

    # Google Sheets API
    GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
    SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")

    # Gemini API
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def get_google_credentials(cls):
        """
        Google Service Account認証情報を取得

        優先順位:
        1. GOOGLE_APPLICATION_CREDENTIALS_JSON（Base64エンコード） - クラウドデプロイ用
        2. SERVICE_ACCOUNT_FILE（ファイルパス） - ローカル開発用

        Returns:
            dict: Service Account認証情報（JSON形式）

        Raises:
            ValueError: 認証情報が見つからない、または不正な形式の場合
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
        service_account_file = cls.SERVICE_ACCOUNT_FILE or "config/service-account.json"
        if Path(service_account_file).exists():
            with open(service_account_file, 'r', encoding='utf-8') as f:
                return json.load(f)

        raise ValueError(
            "Google credentials not found. Set either:\n"
            "  - GOOGLE_APPLICATION_CREDENTIALS_JSON (Base64 encoded JSON for cloud)\n"
            "  - SERVICE_ACCOUNT_FILE (file path for local development)"
        )

    @classmethod
    def validate(cls):
        """Validate that all required environment variables are set"""
        required_vars = [
            "GOOGLE_SHEET_ID",
            "GEMINI_API_KEY"
        ]

        missing_vars = [var for var in required_vars if not getattr(cls, var)]

        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}\n"
                f"Please copy .env.example to .env and fill in the values."
            )

        # Check if Google credentials are available
        try:
            cls.get_google_credentials()
        except ValueError as e:
            raise ValueError(f"Google credentials validation failed: {e}")
