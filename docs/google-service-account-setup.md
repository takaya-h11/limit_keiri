# Googleサービスアカウント設定ガイド

Google Sheets APIを使用するために必要なサービスアカウントの作成手順

## 1. Google Cloud Projectの作成

1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. 新しいプロジェクトを作成
   - プロジェクト名：「limit-sales-management」など
   - 「作成」をクリック

## 2. Google Sheets APIの有効化

1. Google Cloud Consoleで作成したプロジェクトを選択
2. 左メニューから「APIとサービス」→「ライブラリ」を選択
3. 「Google Sheets API」を検索
4. 「Google Sheets API」をクリック
5. 「有効にする」をクリック

同様に、**Google Drive API**も有効化してください。

## 3. サービスアカウントの作成

1. 左メニューから「APIとサービス」→「認証情報」を選択
2. 「認証情報を作成」→「サービスアカウント」をクリック
3. サービスアカウントの詳細を入力：
   - サービスアカウント名：「limit-sales-bot」など
   - サービスアカウントID：自動生成される
   - 説明：「売上管理MCPサーバー用」など
4. 「作成して続行」をクリック
5. 役割の選択：
   - 「編集者」または「オーナー」を選択
   - （より厳密には、Sheets APIの権限のみでも可）
6. 「続行」→「完了」をクリック

## 4. サービスアカウントキー（JSON）の作成

1. 作成したサービスアカウントをクリック
2. 「キー」タブを選択
3. 「鍵を追加」→「新しい鍵を作成」をクリック
4. キーのタイプ：「JSON」を選択
5. 「作成」をクリック
6. JSONファイルが自動的にダウンロードされます

## 5. JSONファイルの配置

1. ダウンロードしたJSONファイルの名前を `service-account.json` に変更
2. プロジェクトの `config/` ディレクトリに配置：
   ```
   limit_keiri/
   ├── config/
   │   └── service-account.json  ← ここに配置
   ```

## 6. Googleスプレッドシートへの共有設定

**重要**: サービスアカウントにスプレッドシートへのアクセス権を付与する必要があります。

1. `service-account.json` を開く
2. `client_email` フィールドの値をコピー
   - 例：`limit-sales-bot@project-id.iam.gserviceaccount.com`
3. 対象のGoogleスプレッドシート（2025年店舗管理シート）を開く
4. 「共有」ボタンをクリック
5. コピーしたメールアドレスを追加
6. 権限を「編集者」に設定
7. 「送信」をクリック

## 7. 環境変数の設定

`.env` ファイルに以下を設定：

```env
SERVICE_ACCOUNT_FILE=config/service-account.json
GOOGLE_SHEET_ID=1oklcKDJ3QNVJ3WXawrr2c1oi0mrjyp39HwvyqcTwniE
```

## セキュリティ上の注意

- ⚠️ **service-account.json は機密情報です**
- `.gitignore` に追加されているか確認してください
- Gitリポジトリにコミットしないでください
- 他人と共有しないでください

## 確認方法

設定が正しく完了しているか確認：

```bash
# Python環境で以下を実行
python -c "
import gspread
from google.oauth2.service_account import Credentials

creds = Credentials.from_service_account_file(
    'config/service-account.json',
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)
client = gspread.authorize(creds)
sheet = client.open_by_key('1oklcKDJ3QNVJ3WXawrr2c1oi0mrjyp39HwvyqcTwniE')
print(f'接続成功: {sheet.title}')
"
```

成功すれば「接続成功: 2025年店舗管理シート」のようなメッセージが表示されます。
