# チケット06: MCPサーバー実装

## 概要
FastMCPを使用してMCPサーバーを構築し、全ての機能を統合する

## TODO
- [ ] FastMCPサーバーの基本構成作成
- [ ] 3つのツールをMCPツールとして登録
  - [ ] `fetch_line_messages` ツール
  - [ ] `get_sheet_info` ツール
  - [ ] `record_gym_sale` ツール
- [ ] ツール間の連携フロー実装
- [ ] Geminiとの連携テスト
- [ ] エラーハンドリングとログ出力
- [ ] 環境変数の読み込み確認
- [ ] サーバー起動スクリプト作成

## MCPツール仕様
### ① fetch_line_messages
```python
@mcp.tool()
def fetch_line_messages() -> dict:
    """LINE Messaging APIから最新のトーク履歴を取得"""
```

### ② get_sheet_info
```python
@mcp.tool()
def get_sheet_info() -> dict:
    """現在のシートのヘッダー情報と次の空行番号を取得"""
```

### ③ record_gym_sale
```python
@mcp.tool()
def record_gym_sale(
    day: int,
    seller: str,
    payment_method: str,
    product_name: str,
    quantity: int,
    unit_price_excl_tax: float
) -> dict:
    """売上情報をスプレッドシートに記録"""
```

## 統合フロー
1. Geminiが `fetch_line_messages` を呼び出し、LINEメッセージを取得
2. Geminiがメッセージを解釈し、構造化データを生成
3. Geminiが `get_sheet_info` を呼び出し、書き込み先を確認
4. Geminiが `record_gym_sale` を呼び出し、データを記録

## 成果物
- [ ] MCPサーバーメインファイル
- [ ] サーバー起動スクリプト
- [ ] 統合テスト
- [ ] README.md（使用方法）

## 依存関係
- チケット02（Google Sheets API連携）完了後
- チケット03（LINE API連携）完了後
- チケット04（売上記録機能）完了後
- チケット05（税計算ロジック）完了後

## 関連ドキュメント
- requirements.md の「1. プロジェクト概要」「5. 実装ツール」

## ステータス
⬜ 未着手
