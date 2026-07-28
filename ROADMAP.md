# Logic-Nodes プロジェクト概要 & ロードマップ

## 1. プロジェクトの背景・目的

### なぜこのブログを作成したか？
* **目的:** **広告収入による収益化**を目的とした全自動IT技術メディアプロジェクト。
* **経緯:** 従来は **Note** で技術ブログを運営していたが、有料記事が購入されないと収入が発生しないビジネスモデルに限界を感じ、アクセス数（PV数）に応じた広告収入モデルへシフトするため、GitHub Pages による自前ブログ運営（**Logic-Nodes**）へ移行した。
* **コアコンセプト:** 人間が介在せず、トレンド取得・執筆・パブリッシュまでを完全自動化する「完全自動パブリッシュ型技術メディア」。

---

## 2. 今後の展望 & アクションプラン

### 🎯 課題1: 検索エンジン最適化（SEO）とインデックス確認
> **「そもそもこのサイトは検索エンジン（Google等）で見えているか？」**

* **現状:** デフォルトの GitHub Pages URL (`https://hakutaku-blog.github.io/logic-nodes/`)。
* **対応策・実装案:**
  1. `robots.txt` および `sitemap.xml` の自動生成仕組みを構築。
  2. **Google Search Console (GSC)** へのサイト登録・所有権確認。
  3. `site:hakutaku-blog.github.io/logic-nodes/` でのインデックス状況の追跡。
  4. 記事ごとの動的 OGP / SEO メタタグ（Title, Description）の最適化。

---

### 📊 課題2: アクセス解析（PV数・プレビュー数）の把握
> **「どれだけの人がサイトを訪れているか（PV数）の可視化」**

* **対応策・実装案:**
  1. **Google Analytics 4 (GA4)** トラッキングコード（`gtag.js`）の `index.html` への導入。
  2. （選択肢2）軽量・プライバシー配慮型の **Cloudflare Web Analytics** や **Umami** の導入。
  3. 日次・月次のPV数推移を確認できるダッシュボード環境の整頓。

---

### 💰 課題3: Google AdSense（広告収入）の実装
> **「広告を掲載し、自動的に広告収益を得る仕組みの構築」**

* **対応策・審査通過に向けた準備:**
  1. **審査通過用コンテンツの整備:**
     - プライバシーポリシーページ（`privacy.html`）の追加（AdSense審査必須要件）。
     - 運営者情報・お問い合わせフォーム（`about.html`）の設置。
  2. **ドメイン検討:**
     - ※`github.io` サブドメインのまま審査が通らない場合、独自ドメイン（例: `.com` / `.dev` など年間数0円〜1000円程度）の取得・接続を検討。
  3. **AdSense広告コードの挿入:**
     - `index.html` の記事上部・記事下部・サイドバー等への自動広告スクリプト配置。

---

## 3. 完了済みシステム構成
* **自動執筆・配信:** GitHub Actions (`auto-publish.yml`) ＋ Gemini API (`generate.py`, `gemini_api.py`)
* **一次情報取得:** Hacker News API から最新海外テックトレンドの自動巡回 (`fetch_tech_trends`)
* **フロントエンド:** Vanilla HTML/CSS/JS ＋ Marked.js (`index.html`)
* **静的配信構成:** `.nojekyll` 設置済み ＋ `src/posts/posts.json` マニフェスト管理
