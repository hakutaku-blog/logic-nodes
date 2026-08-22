---
title: "マイクロサービスの罠とDR対策：Cursor×MCP×オープン重みモデルで構築する次世代の高可搬・高信頼システム"
date: "2026-07-28"
tags: ["DevOps", "Microservices", "Cursor", "MCP", "AI", "Frontend", "DisasterRecovery"]
description: "「マイクロサービスは本当に必要か？」という本質的問合せから、大規模災害（DR）に耐えうるシステム構成、そして機密情報を守りながらCursorとMCP（Model Context Protocol）＋オープン重みLLMで開発を劇的に効率化する実践ガイド。"
---

**ハク**: 最近の海外テックForumでは、大規模地震を契機としたDR（災害復旧）とシステムレジリエンス、オープン重みモデルのプライバシー問題、そして「マイクロサービスって結局何なんだ？」という議論が活発です。DR構成をマイクロサービスで構築する際、具体的にどのような問題が発生するのでしょうか。既存のフェイルオーバー手法と何が違うのですか。

**タク**: サービス間の依存関係が複雑になりすぎることが最大の問題です。具体的な課題と解決策は以下の通りです。

*   **依存関係の迷宮化**: どのサービスから順番に復旧・フェイルオーバーさせるべきかの判断が困難になる。
*   **ネットワーク遅延の増大**: リージョン間の通信が多発し、システム全体のパフォーマンスが劣化する。
*   **解決策（フロントエンド / Edge）**: Next.js (App Router) や Remix を Cloudflare Workers / Vercel などのエッジに展開し、静的アセットと軽量ロジックをグローバルに分散する。
*   **解決策（バックエンド）**: モジュラーモノリス（Modular Monolith）を採用する。ビジネスドメインが明確に独立し、チームが別々にスケールさせる必要が出て初めてマイクロサービス化を検討する。

**ハク**: インフラ構成やDR設計をAIエディタ（Cursor等）でリファクタリングさせる場合、本番環境のインフラ構成図やDBスキーマを外部に送信するセキュリティリスクがあります。オープン重みモデルとMCP（Model Context Protocol）を組み合わせることで、このリスクをどう回避できるのでしょうか。

**タク**: パブリックなSaaS LLMと、ローカルで稼働させるオープン重みモデルには以下のような明確な違いがあります。MCPを介すことで、安全にローカルの文脈をAIに渡すことが可能です。

| 比較項目 | パブリックSaaS LLM | オープン重みモデル (DeepSeek-R1, Llama 3等) + MCP |
| :--- | :--- | :--- |
| **データプライバシー** | クラウド側にデータが送信されるリスクあり | ローカルで完結。ソースコードやIaC、社内ドキュメントが外部に漏れない |
| **コスト効率** | トークン量に応じた従量課金 | トークンコストを気にせず、大量のログ解析やリファクタリングが可能 |
| **コンテキスト同期** | 手動でプロンプトに貼り付ける手間 | MCP経由でDB、GitHub CLI、Terraformステートへ安全に直接アクセス |

**ハク**: MCP経由でインフラ構成の依存関係をAIに理解させる具体的な仕組みと、Cloudflare Workersからバックエンドへ自動フェイルオーバーするRoute Handlerの実装はどうなりますか。

**タク**: `~/.cursor/mcp.json`にカスタムMCPサーバーを定義し、Terraformのステート情報などを読み込ませます。Next.js (App Router) エッジフェイルオーバー処理例は以下の通りです。

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

**ハク**: AIが生成したコードやインフラ構成を現場に導入する際、無意識に踏んでしまうデメリットや「地雷」はありますか。

**タク**: 主に以下の3つの地雷が存在します。事前に対策を講じることが重要です。

*   **「分散モノリス」の完成**: AIに指示するまま細切れのマイクロサービスを作ると、分散トランザクション等のケアが漏れる。最初は「1リポジトリ・1デプロイユニットのモジュラーモノリス」で始め、モジュール間の参照ルールを厳格化する。
*   **IaCや環境変数の漏洩**: Terraformステートなどの機密情報をパブリックLLMに送信してしまう。Ollama等でオープン重みモデルをローカルで動かし、MCPサーバー側でサニタイズ処理を挟む。
*   **未テストのフェイルオーバーロジック過信**: 片方のリージョンがダウンした際に、カスケードダウンを引き起こす危険性がある。Chaos Engineering（Chaos MeshやAWS Fault Injection Service）をCI/CDに組み込み、自動テストを実施する。