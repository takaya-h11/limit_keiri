# LINE Developers チャネル設定ガイド

このガイドでは、LINE Messaging APIのチャネルを作成し、アクセストークンとシークレットを取得する手順を説明します。

## 前提条件
- LINEアカウントを持っていること
- LINE for Businessアカウント（無料で作成可能）

## 手順

### 1. LINE Developersコンソールにアクセス

1. [LINE Developers Console](https://developers.line.biz/console/) にアクセス
2. LINEアカウントでログイン

### 2. プロバイダーの作成

初めて使用する場合は、プロバイダーを作成する必要があります。

1. 「Create」または「作成」ボタンをクリック
2. プロバイダー名を入力（例：「リミット四ツ谷店」）
3. 「Create」をクリック

**既にプロバイダーがある場合は、この手順をスキップしてください。**

### 3. Messaging APIチャネルの作成

1. プロバイダーを選択
2. 「Create a Messaging API channel」または「Messaging APIチャネルを作成」をクリック
3. 以下の情報を入力：

   | 項目 | 入力例 |
   |------|--------|
   | **Channel type** | Messaging API（自動選択） |
   | **Provider** | 既に選択されているプロバイダー |
   | **Channel name** | リミット四ツ谷店 売上管理Bot |
   | **Channel description** | 売上報告を受け付けるBot |
   | **Category** | Business Tools & Productivity |
   | **Subcategory** | Business Management |
   | **Email address** | あなたのメールアドレス |

4. 利用規約に同意してチェック
5. 「Create」をクリック

### 4. チャネル設定の確認

チャネルが作成されたら、「Basic settings」タブで以下を確認：

#### 4-1. チャネルシークレットの取得

1. 「Basic settings」タブを開く
2. 「Channel secret」の値をコピー
3. `.env`ファイルの`LINE_CHANNEL_SECRET`に設定

```env
LINE_CHANNEL_SECRET=ここにコピーした値を貼り付け
```

### 5. チャネルアクセストークンの発行

1. 「Messaging API」タブを開く
2. 下にスクロールして「Channel access token」セクションを探す
3. **「Issue」**ボタンをクリック（初回のみ）
4. 発行されたトークン（長い文字列）をコピー
5. `.env`ファイルの`LINE_CHANNEL_ACCESS_TOKEN`に設定

```env
LINE_CHANNEL_ACCESS_TOKEN=ここにコピーした値を貼り付け
```

**重要**: アクセストークンは一度しか表示されません。必ずコピーして安全に保管してください。

### 6. Webhook設定

#### 6-1. Webhookを有効化

1. 「Messaging API」タブで「Use webhook」を**ON**にする

#### 6-2. Webhook URLの設定

1. Webhookサーバーを起動（後で設定する場合はスキップ可）
   ```bash
   # ローカルでサーバーを起動
   python -m src.webhook_server

   # 別のターミナルでngrokを起動
   ngrok http 8000
   ```

2. ngrokが表示するHTTPS URLをコピー（例: `https://xxxx-xx-xxx-xxx-xx.ngrok.io`）

3. LINE Developersコンソールに戻り、「Webhook URL」に以下を入力：
   ```
   https://xxxx-xx-xxx-xxx-xx.ngrok.io/webhook
   ```
   **重要**: 末尾に`/webhook`を付けること

4. 「Update」または「更新」をクリック
5. 「Verify」ボタンをクリックして接続テスト（サーバーが起動している場合）

### 7. 自動応答メッセージの無効化（推奨）

1. 「Messaging API」タブで「LINE Official Account features」セクションを探す
2. 「Auto-reply messages」を**Disabled**にする
3. 「Greeting messages」も**Disabled**にする（任意）

これにより、Botが自分で管理するメッセージのみを送信できます。

### 8. Botを友だち追加

1. 「Messaging API」タブで「QR code」を探す
2. QRコードをスマホで読み取る
3. Botを友だち追加

### 9. 動作確認

1. Webhookサーバーが起動していることを確認
   ```bash
   python -m src.webhook_server
   ```

2. LINEアプリでBotにメッセージを送信
   ```
   12/28 PayPal 月4回プラン 35,200円
   ```

3. サーバーのログにメッセージが表示されることを確認

4. ブラウザで受信メッセージを確認（デバッグ用）
   ```
   http://localhost:8000/messages
   ```

## トラブルシューティング

### Webhook接続エラー

**問題**: Webhook URLの検証が失敗する

**解決策**:
1. ngrokが起動しているか確認
2. Webhookサーバーが起動しているか確認（`python -m src.webhook_server`）
3. Webhook URLに`/webhook`が付いているか確認
4. ngrokの無料プランの場合、8時間でURLが変わるので注意

### アクセストークンエラー

**問題**: `Invalid access token`エラー

**解決策**:
1. `.env`ファイルの`LINE_CHANNEL_ACCESS_TOKEN`が正しいか確認
2. トークンの前後に余分なスペースがないか確認
3. トークンの有効期限を確認（通常は無期限だが、再発行した場合は古いものは無効）

### メッセージが受信できない

**問題**: LINEで送ったメッセージがWebhookサーバーに届かない

**解決策**:
1. Botを友だち追加しているか確認
2. Webhookが有効（ON）になっているか確認
3. Webhook URLが正しく設定されているか確認
4. サーバーのログを確認

## 参考リンク

- [LINE Developers ドキュメント](https://developers.line.biz/ja/docs/)
- [Messaging API リファレンス](https://developers.line.biz/ja/reference/messaging-api/)
- [ngrok ドキュメント](https://ngrok.com/docs)

## 完成した.envファイルの例

```env
# LINE Messaging API
LINE_CHANNEL_ACCESS_TOKEN=eyJhbGc...（長い文字列）
LINE_CHANNEL_SECRET=1234567890abcdef...

# Google Sheets API
GOOGLE_SHEET_ID=1oklcKDJ3QNVJ3WXawrr2c1oi0mrjyp39HwvyqcTwniE
SERVICE_ACCOUNT_FILE=config/service-account.json

# オプション
LOG_LEVEL=INFO
```

## 次のステップ

1. [Google サービスアカウント設定](./google-service-account-setup.md)
2. 依存関係のインストール: `pip install -r requirements.txt`
3. Webhookサーバーの起動: `python -m src.webhook_server`
4. MCPサーバーのテスト: `python -m src.mcp_server`
