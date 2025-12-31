# リミット四ツ谷店 売上管理「AIコクピット」アーキテクチャ

## システム概要

**スマホ完結 × AI解析 × クラウド連携**で売上記録を自動化する「AIコクピット」システム。

---

## アーキテクチャ図

```
┌─────────────────────────────────────────────────────────┐
│                   ユーザー操作（スマホ）                  │
└──────────────────────┬──────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
        ▼                             ▼
┌──────────────┐              ┌──────────────┐
│     LINE     │              │ Google Apps  │
│  メッセージ   │              │    Script    │
└──────┬───────┘              └──────┬───────┘
       │ コピー                       │
       │                             │
       └──────────────┬──────────────┘
                      │ 貼り付け
                      ▼
         ┌─────────────────────────┐
         │  Google AI Studio       │
         │  (Gemini 2.0/3.0)       │
         │  ┌───────────────────┐  │
         │  │ テキスト解析      │  │
         │  │ 税抜逆算計算      │  │
         │  │ (floor(税込/1.1)) │  │
         │  └───────────────────┘  │
         └──────────┬──────────────┘
                    │ Function Calling (HTTPS)
                    ▼
         ┌─────────────────────────┐
         │  REST API Server        │
         │  (Render - PaaS)        │
         │  ┌───────────────────┐  │
         │  │ POST /api/        │  │
         │  │   record_sale     │  │
         │  │                   │  │
         │  │ GET /api/schema   │  │
         │  └───────────────────┘  │
         └──────────┬──────────────┘
                    │ gspread (Google Sheets API)
                    ▼
         ┌─────────────────────────┐
         │ Google Spreadsheet      │
         │ 「2025年店舗管理シート」 │
         │  ┌──┬──┬──┬──┬──┬──┐  │
         │  │No│決│日│販│決│商│  │
         │  │  │済│ │売│済│品│  │
         │  ├──┼──┼──┼──┼──┼──┤  │
         │  │1 │✓│28│服│PP│月4│  │
         │  └──┴──┴──┴──┴──┴──┘  │
         └─────────────────────────┘
```

---

## コンポーネント詳細

### 1. ホスト（Brain）: Google AI Studio

**役割:** 自然言語解析と計算処理

**機能:**
- LINEメッセージからの情報抽出
- 税抜単価の逆算（`floor(税込金額 / 1.1)`）
- Function Calling経由でAPIサーバーを呼び出し

**技術:**
- Gemini 2.0 Flash Experimental
- Gemini 3.0 Flash/Pro（将来）
- Function Calling API

**入力例:**
```
12/28 PayPalで月4回プラン 35,200円 販売しました。販売者: 服部誉也
```

**処理:**
1. テキスト解析 → 構造化データ抽出
2. 税抜計算 → `floor(35200 / 1.1) = 32000`
3. Function Call → `record_gym_sale(...)`

---

### 2. サーバー（Hands）: REST API Server

**役割:** データ永続化の「純粋な道具」

**実装:** `src/api_server.py`
- FastAPI
- Python 3.10+
- gspread（Google Sheets API）

**エンドポイント:**

#### `POST /api/record_sale`
売上情報をスプレッドシートに記録

**リクエスト:**
```json
{
  "day": 28,
  "seller": "服部誉也",
  "payment_method": "PayPal",
  "product_name": "月4回プラン",
  "quantity": 1,
  "unit_price_excl_tax": 32000
}
```

**処理:**
1. 現在の月のシートを取得（例: "12 月度"）
2. 次の空行を検索（5行目以降）
3. C列〜H列にデータを書き込み
4. I列・J列の数式を維持

**レスポンス:**
```json
{
  "success": true,
  "row": 15,
  "message": "売上を 15 行目に記録しました"
}
```

#### `GET /api/schema`
Gemini Function Calling用のJSONスキーマを返す

**レスポンス:** [gemini_function_schema.json](gemini_function_schema.json:1)

---

### 3. データ（Storage）: Google Spreadsheet

**対象シート:** 「2025年店舗管理シート」

**月次シート構造:**
- シート名: `{月} 月度` （例: "12 月度"）
- ヘッダー行: 4行目
- データ開始: 5行目以降

**列定義:**
| 列 | 項目 | 説明 |
|----|------|------|
| A | No. | 連番（手動入力） |
| B | 決済 | チェックボックス |
| C | 日 | 日付（数値のみ） |
| D | 販売者 | トレーナー名 |
| E | 決済方法 | PayPal, PayPay, 現金等 |
| F | 商品・サービス名 | 月4回プラン等 |
| G | 数量 | 数値 |
| H | 単価（税抜） | 整数値 |
| I | 小計（税抜） | 自動計算: G列 × H列 |
| J | 消費税 | 自動計算: I列 × 0.1（整数） |

**重要:**
- APIは**C列〜J列**を書き込み
- I列（小計）= 数量 × 単価（税抜）
- J列（消費税）= 小計 × 0.1（整数化）

---

## データフロー

### 標準フロー（Apps Script経由）

```
1. LINEでメッセージ受信
   ↓
2. メッセージをコピー
   ↓
3. Google Sheetsアプリを開く
   ↓
4. メニュー「売上管理」→「売上を記録」
   ↓
5. テキストを貼り付け
   ↓
6. Apps Script実行
   ├─ Gemini APIでテキスト解析
   │  ├─ 日付抽出: "12/28" → 28
   │  ├─ 販売者抽出: "服部誉也"
   │  ├─ 決済方法抽出: "PayPal"
   │  ├─ 商品名抽出: "月4回プラン"
   │  ├─ 数量: 1（デフォルト）
   │  └─ 税抜計算: floor(35200 / 1.1) = 32000
   ├─ REST API呼び出し
   │  POST https://limit-yotsuya-cockpit.onrender.com/api/record_sale
   └─ 結果通知
   ↓
7. スプレッドシート更新確認
```

### 直接呼び出しフロー（開発・デバッグ用）

```bash
curl -X POST https://limit-yotsuya-cockpit.onrender.com/api/record_sale \
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

---

## 設計原則

### 1. 純粋な道具（Dumb Hands）

**APIサーバーは一切の判断をしない:**
- ✅ 指示された行にデータを書き込む
- ❌ データの妥当性チェック
- ❌ 税計算
- ❌ 自然言語解析

### 2. スマホ完結

**すべての操作をスマホから実行可能:**
- LINEアプリでメッセージコピー
- Google Sheetsアプリでスクリプト実行
- 確認もスプレッドシートで完結

### 3. 確実性の担保

**人間による確認ステップ:**
1. Geminiが解析した内容を表示
2. ユーザーが確認
3. OKボタンで実行

### 4. 低コスト運用

**インフラコスト最小化:**
- ✅ PaaS（Render）の無料枠を活用
- ✅ 自宅PC不要
- ✅ Gemini Advanced（月額課金）で高度な推論を実現
- ❌ 常時起動サーバー不要

---

## セキュリティ

### 認証情報管理

**Google Service Account:**
- クラウド環境: 環境変数（Base64エンコード）
- ローカル環境: JSONファイル

**環境変数:**
```bash
GOOGLE_SHEET_ID=1oklcKDJ3QNVJ3WXawrr2c1oi0mrjyp39HwvyqcTwniE
GOOGLE_APPLICATION_CREDENTIALS_JSON=<Base64エンコード>
```

### API保護

**現状:**
- CORS設定: 全開放（`allow_origins=["*"]`）

**推奨（本番環境）:**
```python
allow_origins=[
    "https://aistudio.google.com",
    "https://script.google.com"
]
```

---

## スケーラビリティ

### 現在の制約

- **Google Sheets API制限:** 1分あたり60リクエスト
- **Render無料枠:** 750時間/月、自動スリープあり

### 改善案

1. **Redis Cacheの導入**
   - シート情報のキャッシュ
   - API呼び出し削減

2. **バッチ処理**
   - 複数件の売上を一括記録
   - `batch_update` API使用

3. **有料プランへの移行**
   - Render: $7/月（常時起動）
   - Google Workspace: API制限緩和

---

## トラブルシューティング

### よくある問題

**1. APIサーバーが応答しない**
- Renderの無料枠は15分の非アクティブでスリープ
- 解決策: ヘルスチェックで起動 `curl https://your-app.onrender.com/health`

**2. スプレッドシートに書き込めない**
- サービスアカウントに編集権限があるか確認
- シート名が正しいか確認（例: "12 月度"）

**3. 税抜計算が合わない**
- `floor(税込 / 1.1)` を使用しているか確認
- 例: 35,200円 → 32,000円（正）、31,999円（誤）

---

## 開発ロードマップ

### Phase 1: MVP ✅
- [x] REST APIサーバー実装
- [x] Google Sheets連携
- [x] Renderデプロイ
- [x] Function Calling JSONスキーマ

### Phase 2: スマホUI強化
- [ ] Google Apps Script実装
- [ ] カスタムメニュー追加
- [ ] エラーハンドリング改善

### Phase 3: 機能拡張
- [ ] 売上集計機能
- [ ] 月次レポート自動生成
- [ ] 複数店舗対応

---

## 参考資料

- [README.md](README.md:1) - プロジェクト概要
- [docs/ai-studio-setup.md](docs/ai-studio-setup.md:1) - AI Studio接続ガイド
- [docs/cloud-deployment.md](docs/cloud-deployment.md:1) - クラウドデプロイガイド
- [gemini_function_schema.json](gemini_function_schema.json:1) - Function Calling定義

---

## ライセンス

MIT License

## 作成者

Claude Code + 服部誉也
