---
title: "マイクロサービスの罠とDR対策：Cursor×MCP×オープン重みモデルで構築する次世代の高可搬・高信頼システム"
date: "2025-02-15"
tags: ["DevOps", "Microservices", "Cursor", "MCP", "AI", "Frontend", "DisasterRecovery"]
description: "「マイクロサービスは本当に必要か？」という本質的問合せから、大規模災害（DR）に耐えうるシステム構成、そして機密情報を守りながらCursorとMCP（Model Context Protocol）＋オープン重みLLMで開発を劇的に効率化する実践ガイド。"
---


こんにちは。フロントエンドからDevOps、AIツールを活用した開発プロセスの改善までを追求している技術ブロガーです。

最近の海外テックForumでは、**大規模地震（Japan Earthquake）を契機としたDR（災害復旧）とシステムレジリエンスの再定義**、**オープン重みモデル（Open-weights Models）の評価とプライバシー問題**、そして**「マイクロサービスって結局何なんだ？」というアーキテクチャの原点回帰**の3つが大きな話題となっています。

一見ばらばらに見えるこれらのトピックですが、現場のエンジニアにとっては**「複雑化しすぎたアーキテクチャをいかに整理し、AIの力を安全に借りて、止まらないシステムを作るか」**という1つの大きなテーマに集約されます。

本記事では、マイクロサービスの地雷を回避しつつ、**Cursor**と**MCP（Model Context Protocol）**、そして**オープン重みモデル**を活用して、高信頼なシステム（Edge/Frontend + DevOps）を迅速に構築・運用する実践的なアプローチを解説します。

---

## 1. 「それ、本当にマイクロサービスにする必要ある？」とDR（災害対策）の現実

海外Forumでも議論が紛糾している「*What Even Are Microservices?*」。多くの現場が**「分散モノリス（Distributed Monolith）」**の罠にハマり、運用コストとネットワーク遅延に苦しんでいます。

さらに、地震などの大規模障害に備える**DR（Disaster Recovery）構成**をマイクロサービスでやろうとすると、サービス間の依存関係が複雑すぎて「どの順番で復旧・フェイルオーバーすればいいのか分からない」という致命的な地雷を踏むことになります。

### 現場で目指すべきアーキテクチャの解
* **フロントエンド/Edge:**  
  Next.js (App Router) や Remix を Cloudflare Workers / Vercel などのエッジに展開。静的アセットと軽量ロジックをグローバルに分散し、単一リージョン障害の影を消す。
* **バックエンド:**  
  最初から無理にサービスを分割せず、まずは境界が明確な**モジュラーモノリス（Modular Monolith）**を採用する。ビジネスドメインが明確に独立し、チームが別々にスケールさせる必要が出て初めてマイクロサービス化を検討する。

```
[ Frontend: Next.js Edge (Cloudflare / Vercel) ]
                      │
                      ▼ (BFF / Route Handlers)
                      │
        ┌─────────────┴─────────────┐
        │   Modular Monolith App   │  <-- DR復旧が極めて容易
        │ ┌───────┐┌───────┐┌──────┐│
        │ │ Domain││ Domain││Domain││
        │ │   A   ││   B   ││  C   ││
        │ └───────┘└───────┘└──────┘│
        └─────────────┬─────────────┘
                      │
           [ Multi-Region DB (Aurora / PlanetScale) ]
```

---

## 2. セキュリティと文脈を両立する「Cursor × MCP × オープン重みモデル」

インフラ構成（IaC）やDR設計、ドメインモデルの再設計をAIエディタ（Cursor等）に手伝わせる際、最大の障害となるのが**「セキュリティとプライバシー」**です。本番環境のインフラ構成図やDBスキーマ、AWSのTerraformコードをパブリックなSaaS LLMに投げるのはリスクがあります。

ここで活きてくるのが、**「オープン重みモデル（DeepSeek-R1, Llama 3, Qwen 2.5等）」**のローカル/プライベート運用と、Anthropicが提唱する**MCP（Model Context Protocol）**です。

### なぜオープン重みモデルなのか？
* **データプライバシーの担保:** ソースコードやIaC、社内ドキュメントを外部の学習やログに残さず処理できる。
* **コスト効率:** 大量のログ解析やリファクタリングタスクをトークンコストを気にせず回せる。
* **Cursorでのローカルモデル利用:** Ollie / LM Studio や Ollama 経由で、Cursorの補完エンジンやチャットバックエンドをローカルのオープン重みモデルに切り替えることが可能。

---

## 3. 実践：MCPを使ってCursorにインフラ文脈とコードベースを同期させる

MCP（Model Context Protocol）を使うことで、CursorなどのAIエディタが**ローカルのデータベース、GitHub CLI、Terraformのステート情報**へ安全にアクセスできるようになります。

ここでは、MCPサーバーを介して「インフラの構成」と「アプリケーションコード」の依存関係をAIに理解させ、DR対応のリファクタリングを行わせる環境を作ります。

### MCP Server 設定例 (`~/.cursor/mcp.json`)

以下の設定で、Cursorから自作のローカルツールやGitHub/インフラ構成にアクセスできるようにします。

```json
{
  "mcpServers": {
    "git-architecture-analyzer": {
      "command": "node",
      "args": ["/Users/developer/mcp-servers/dist/git-analyzer.js"],
      "env": {
        "REPO_PATH": "/Users/developer/projects/my-resilient-app"
      }
    },
    "terraform-state-reader": {
      "command": "python3",
      "args": ["/Users/developer/mcp-servers/tf_reader.py"],
      "env": {
        "TF_STATE_PATH": "./terraform/env/prod/terraform.tfstate"
      }
    }
  }
}
```

### Cursorプロンプト例：モジュラー化とDRフェイルオーバーのコード生成

Cursorのチャット画面で、MCP経由でコンテキストを引き出しながら指示を出します。

```text
@terraform-state-reader と @git-architecture-analyzer の文脈を参照してください。

現在、UserサービスとOrderサービスがHTTP通信で密結合になっており、
リージョン障害時のフェイルオーバーで問題が発生するリスクがあります。

1. この2つのサービスをモジュラーモノリス内のイベント駆動型（In-memory Event Bus）に統合するためのリファクタリング案を提示してください。
2. Cloudflare Workersからプライマリ（東京）およびセカンダリ（大阪）のバックエンドへ自動フェイルオーバーするNext.jsのRoute Handlerコードを作成してください。
```

#### 生成されるNext.js (App Router) エッジフェイルオーバー処理例

```typescript
// app/api/proxy/[...path]/route.ts
import { NextRequest, NextResponse } from 'next/server';

const PRIMARY_ORIGIN = process.env.PRIMARY_BACKEND_URL; // 東京リージョン
const SECONDARY_ORIGIN = process.env.SECONDARY_BACKEND_URL; // 大阪リージョン (DR)

async function fetchWithTimeout(url: string, options: RequestInit, timeoutMs = 2000) {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, { ...options, signal: controller.signal });
    return response;
  } finally {
    clearTimeout(id);
  }
}

export async function ALL(request: NextRequest, { params }: { params: { path: string[] } }) {
  const path = params.path.join('/');
  const body = request.method !== 'GET' && request.method !== 'HEAD' ? await request.blob() : undefined;
  
  const requestInit: RequestInit = {
    method: request.method,
    headers: request.headers,
    body: body,
  };

  // 1. プライマリリージョンへのリクエスト試行
  try {
    const primaryUrl = `${PRIMARY_ORIGIN}/${path}${request.nextUrl.search}`;
    const res = await fetchWithTimeout(primaryUrl, requestInit, 1500);
    
    // 5xxエラーの場合はDR環境へフォールバック
    if (res.ok || res.status < 500) {
      return res;
    }
    console.warn(`Primary region returned status ${res.status}. Falling back to secondary.`);
  } catch (error) {
    console.error('Primary region failed or timed out. Initiating DR Failover:', error);
  }

  // 2. セカンダリ（DR）リージョンへのフォールバック
  try {
    const secondaryUrl = `${SECONDARY_ORIGIN}/${path}${request.nextUrl.search}`;
    const secondaryRes = await fetchWithTimeout(secondaryUrl, requestInit, 3000);
    
    // ヘッダーにDR経由であることを付与して返却
    const newHeaders = new Headers(secondaryRes.headers);
    newHeaders.set('X-Served-By', 'DR-Secondary-Region');
    
    return new NextResponse(secondaryRes.body, {
      status: secondaryRes.status,
      statusText: secondaryRes.statusText,
      headers: newHeaders,
    });
  } catch (drError) {
    return NextResponse.json(
      { error: 'Service Unavailable in both regions. Disaster recovery in progress.' },
      { status: 503 }
    );
  }
}
```

---

## 4. 現場でハマる「3つの地雷」と徹底対策

AIツールとモダンインフラを組み合わせて構築する際に、現場で発生しやすい地雷とその対策をまとめました。

### 💣 地雷1：AIに言われるがまま「細切れのマイクロサービス」を作ってしまう
AIエディタは指示された通りにコードを分離してくれますが、サービス間の「分散トランザクション（Sagaパターン等）」や「ネットワーク遅延」のケアまで完璧にやってくれるわけではありません。結果として巨大な「分散モノリス」が完成します。

* **対策:**  
  最初は**「1つのリポジトリ・1つのデプロイユニット（モジュラーモノリス）」**で始め、モジュール間の参照ルール（ESLintの`no-restricted-imports`等）を厳格にする。分離するのはトラフィックやセキュリティ要件が格段に異なる場合のみとする。

### 💣 地雷2：IaCや環境変数をそのままAIチャット（パブリックLLM）に投げて漏洩する
AWSのVPC構成やDB接続文字列、`tfstate`ファイルには機密情報が詰まっています。便利だからとCursorからそのまま外部LLMに送信するのは大爆発の元です。

* **対策:**  
  * **オープン重みモデル（DeepSeek-R1 / Qwen等）**をOllama等でローカル環境で動かし、敏感なコードのリファクタリングはローカルLLMに限定する。
  * MCPサーバー側でマスク処理（サニタイズ）を挟み、接続情報やAPIキーがAIのコンテキストに入らないようにガードをかける。

### 💣 地雷3：DR（災害復旧）のフェイルオーバーロジックを「テストなし」で過信する
AIが生成した「綺麗に見える自動フェイルオーバーコード」は、実際に片方のリージョンを落とした時に「カスケードダウン（障害の連鎖）」を引き起こすリスクがあります。

* **対策:**  
  Chaos Engineering（Chaos MeshやAWS Fault Injection Service）をCI/CDに組み込み、**「あえてプライマリをタイムアウトさせてセカンダリに正しく切り替わるか」**を自動テストする。

---

## まとめ：これからのエンジニアに求められる姿勢

本日のトレンドトピックから見えてくる現実は以下の通りです。

1. **アーキテクチャはシンプルに保つ:** 地震やインフラ障害に強いのは、複雑なマイクロサービスではなく、依存関係が綺麗に整理されたシンプルなシステム（モジュラーモノリス＋エッジ）。
2. **AIの文脈を安全に制御する:** MCPを活用してCursorにローカルの正確な文脈（IaCやDB構造）を与えつつ、オープン重みモデルを活用してセキュリティリスクを排除する。

「流行りのアーキテクチャだから」と飛びつくのではなく、最新のAI開発環境（Cursor / MCP）を安全に使いこなしながら、真に頑丈（Resilient）でシンプルなシステムを設計していきましょう。