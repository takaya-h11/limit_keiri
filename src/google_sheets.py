"""
Google Sheets integration module
Googleスプレッドシートへの読み書き機能
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

import gspread
from google.oauth2.service_account import Credentials

from .config import Config

logger = logging.getLogger(__name__)


class GoogleSheetsClient:
    """Google Sheets API client for 2025年店舗管理シート"""

    # Google Sheets APIのスコープ
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    def __init__(self):
        """Initialize Google Sheets client"""
        # 認証情報を取得（環境変数またはファイルから）
        credentials_dict = Config.get_google_credentials()

        # gspread認証
        self.credentials = Credentials.from_service_account_info(
            credentials_dict,
            scopes=self.SCOPES
        )
        self.client = gspread.authorize(self.credentials)
        self.spreadsheet = None
        self.current_sheet = None

    def connect(self):
        """Connect to the Google Spreadsheet"""
        try:
            self.spreadsheet = self.client.open_by_key(Config.GOOGLE_SHEET_ID)
            logger.info(f"Connected to spreadsheet: {self.spreadsheet.title}")
        except Exception as e:
            logger.error(f"Failed to connect to spreadsheet: {e}")
            raise

    def get_current_month_sheet(self) -> gspread.Worksheet:
        """
        Get the worksheet for the current month
        現在の月に応じたシートを取得（例：「12 月度」）
        シートが存在しない場合は「テンプレート」から自動作成

        Returns:
            gspread.Worksheet: Current month's worksheet
        """
        if not self.spreadsheet:
            self.connect()

        # Get current month (1-12)
        current_month = datetime.now().month
        sheet_name = f"{current_month} 月度"

        logger.info(f"[シート取得] 対象シート名: {sheet_name}")

        try:
            self.current_sheet = self.spreadsheet.worksheet(sheet_name)
            logger.info(f"[シート取得成功] シート '{sheet_name}' を開きました")
            return self.current_sheet
        except gspread.WorksheetNotFound:
            logger.warning(f"[シート未検出] シート '{sheet_name}' が見つかりません。テンプレートから作成します。")
            return self._create_sheet_from_template(sheet_name)

    def _create_sheet_from_template(self, sheet_name: str) -> gspread.Worksheet:
        """
        テンプレートシートから新しいシートを作成

        Args:
            sheet_name: 作成するシート名（例：「1 月度」）

        Returns:
            gspread.Worksheet: 作成されたシート

        Raises:
            gspread.WorksheetNotFound: テンプレートシートが見つからない場合
        """
        try:
            # テンプレートシートを取得
            template = self.spreadsheet.worksheet("テンプレート")
            logger.info(f"[テンプレート取得成功] 'テンプレート' シートを取得しました")

            # テンプレートを複製
            new_sheet = template.duplicate(new_sheet_name=sheet_name)
            logger.info(f"[シート作成成功] '{sheet_name}' シートを作成しました（テンプレートID: {template.id}）")

            # 作成したシートをcurrent_sheetとして設定
            self.current_sheet = new_sheet
            return new_sheet

        except gspread.WorksheetNotFound:
            logger.error(f"[テンプレート未検出] 'テンプレート' シートが見つかりません。スプレッドシートに 'テンプレート' という名前のシートを作成してください。")
            raise ValueError("テンプレートシートが見つかりません。スプレッドシートに 'テンプレート' という名前のシートを作成してください。")
        except Exception as e:
            logger.error(f"[シート作成失敗] シート '{sheet_name}' の作成に失敗しました: {e}")
            raise

    def get_sheet_info(self) -> Dict:
        """
        Get sheet information: headers and next empty row
        ヘッダー情報と次に書き込むべき空行の番号を取得

        Returns:
            dict: {
                "headers": List[str],
                "next_row": int,
                "trainers": List[str]
            }
        """
        if not self.current_sheet:
            self.get_current_month_sheet()

        # ヘッダー行（4行目）を取得
        headers = self.current_sheet.row_values(4)

        # M列のトレーナー名リストを取得（5行目以降）
        trainers_column = self.current_sheet.col_values(13)  # M列 = 13
        trainers = [name for name in trainers_column[4:] if name]  # 4行目以降、空でないもの

        # 次の空行を見つける（5行目以降）
        all_values = self.current_sheet.get_all_values()
        next_row = 5  # デフォルトは5行目から開始

        for i, row in enumerate(all_values[4:], start=5):  # 5行目から検索
            # C列（日付）が空なら、その行が次の書き込み先
            if not row[2]:  # C列 = index 2
                next_row = i
                break
        else:
            # 全ての行が埋まっている場合は、最後の行の次
            next_row = len(all_values) + 1

        logger.info(f"Next empty row: {next_row}")

        return {
            "headers": headers,
            "next_row": next_row,
            "trainers": trainers
        }

    def record_sale(
        self,
        day: int,
        seller: str,
        payment_method: str,
        product_name: str,
        quantity: int,
        unit_price_excl_tax: float,
        unit_price_incl_tax: float = None
    ) -> Dict:
        """
        Record a sale to the spreadsheet
        売上情報をスプレッドシートに記録

        Args:
            day: 日付（数値のみ）
            seller: 顧客名（D列）
            payment_method: 決済方法
            product_name: 商品・サービス名
            quantity: 数量
            unit_price_excl_tax: 単価（税抜）
            unit_price_incl_tax: 単価（税込） - I列表示用

        Returns:
            dict: {"success": bool, "row": int, "message": str}
        """
        logger.info(f"[売上記録開始] day={day}, seller={seller}, payment_method={payment_method}, product_name={product_name}, quantity={quantity}, unit_price_excl_tax={unit_price_excl_tax}, unit_price_incl_tax={unit_price_incl_tax}")

        if not self.current_sheet:
            self.get_current_month_sheet()

        # スプレッドシートとシート名をログ出力
        logger.info(f"[接続先] スプレッドシート: '{self.spreadsheet.title}', シート名: '{self.current_sheet.title}'")

        # 次の空行を取得
        sheet_info = self.get_sheet_info()
        next_row = sheet_info["next_row"]
        logger.info(f"[書き込み先] 次の空行: {next_row} 行目")

        # I列・J列の計算
        # I列: 税込金額（元の入力値をそのまま表示）
        if unit_price_incl_tax is not None:
            subtotal_incl_tax = quantity * unit_price_incl_tax  # I列: 小計（税込）
        else:
            # 後方互換性: 税込が渡されない場合は税抜から逆算
            subtotal_incl_tax = int(quantity * unit_price_excl_tax * 1.1)

        subtotal_excl_tax = quantity * unit_price_excl_tax  # 税抜小計（計算用）
        consumption_tax = int(subtotal_excl_tax * 0.1)       # J列: 消費税（整数）

        # データを準備（C列〜J列）
        # B列（決済チェックボックス）は空欄のまま
        row_data = [
            day,                    # C列: 日
            seller,                 # D列: 顧客名
            payment_method,         # E列: 決済方法
            product_name,           # F列: 商品・サービス名
            quantity,               # G列: 数量
            unit_price_excl_tax,    # H列: 単価（税抜）
            subtotal_incl_tax,      # I列: 小計（税込）
            consumption_tax         # J列: 消費税
        ]

        logger.info(f"[書き込みデータ] C列〜J列: {row_data}")
        logger.info(f"[計算結果] 小計（税込）={subtotal_incl_tax}, 小計（税抜）={subtotal_excl_tax}, 消費税={consumption_tax}")

        try:
            # C列から始めて、J列まで書き込み
            # range_nameは "C{row}:J{row}" の形式
            range_name = f"C{next_row}:J{next_row}"
            logger.info(f"[書き込み範囲] {range_name}")

            self.current_sheet.update(range_name, [row_data])

            logger.info(f"[書き込み成功] {next_row} 行目に売上を記録しました")

            return {
                "success": True,
                "row": next_row,
                "message": f"売上を {next_row} 行目に記録しました",
                "sheet_name": self.current_sheet.title
            }
        except Exception as e:
            logger.error(f"[書き込み失敗] エラー: {e}")
            return {
                "success": False,
                "row": next_row,
                "message": f"エラー: {str(e)}",
                "sheet_name": self.current_sheet.title if self.current_sheet else "不明"
            }
