# Google AdSense 審査監視 ＆ API連携メモ

## 1. 現状の審査ステータス
* **審査申請日:** 2026年7月28日
* **対象サイト:** `https://hakutaku-blog.github.io/logic-nodes/`（およびルート `https://hakutaku-blog.github.io/`）
* **AdSense パブリッシャー ID:** `ca-pub-2248754336859319`
* **所有権認証・審査リクエスト:** 完了（AdSense 管理画面で「審査待ち ✔」）

---

## 2. 定期リマインド・確認タスク
* **週1回スケジューラ:** 毎週月曜日にAIが自動リマインドを行い、AdSense 審査通知メールの着信有無をユーザーに確認・サポートする。

---

## 3. 審査通過後の AdSense API 収益連携手順（TODO）
AdSense 審査通過通知メールが届いたら、以下の手順で「昨日の広告推定収益」の自動取得を有効化する：

1. **Google Cloud Console** (`logic-nodes-analytics` プロジェクト) を開く。
2. **「APIとサービス」➔「ライブラリ」** で `Google AdSense Management API` を検索し「有効にする」。
3. **「認証情報」➔「OAuth 2.0 クライアント ID」** を作成。
4. 発行された `ADSENSE_CLIENT_ID`, `ADSENSE_CLIENT_SECRET`, `ADSENSE_REFRESH_TOKEN` を GitHub Secrets に追加。
5. `analytics.py` ＆ Discord 通知へ「💰 昨日の広告推定収益」の項目を追加。
