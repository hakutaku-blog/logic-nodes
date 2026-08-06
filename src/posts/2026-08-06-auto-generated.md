---
title: "AI時代の開発ループを極める：Cursor × MCPで回す「Discovery Loop」と地味だが最強なDevOps基盤の作り方"
date: "2026-08-06"
tags: ["Cursor", "MCP", "Frontend", "DevOps", "TypeScript"]
description: "単なるコード生成からツール連携・課題発見の時代へ。CursorとModel Context Protocol (MCP) を組み合わせて継続的な「Discovery Loop」を高速化し、地味になりがちな基盤整備や地雷対策を効率化する実践手法を解説します。"
---

## はじめに

最近のAI業界における巨頭の体制変更やフロンティアモデルの成熟を見るにつけ、私たちの開発現場におけるAIの役割は**「単なるコード自動生成（補完）」から「自律的なコンテキスト理解とツール連携（Agentic / Tool Integration）」のフェーズ**へと明確に移行したと感じます。

一方で、海外テックコミュニティで議論されている *「Crime Pays but Botany Doesn't（華やかな機能開発は評価されるが、地味な植物学＝基盤メンテは放置されがち）」* という言葉の通り、フロントエンドやDevOpsの現場では、型定義のメンテナンス、CI/CDの最適化、ドキュメントの更新といった「地味な作業」が後回しにされ、結果として巨大な技術負債やセキュリティの「地雷」を生み出しています。

この記事では、AIエディタ（Cursor等）と **MCP（Model Context Protocol）** を組み合わせることで、課題の発見から検証・修正までのサイクルである **「Discovery Loop（発見のループ）」** を高速化し、後回しにされがちな基盤整備や地雷対策をいかに効率良く自律化していくかを解説します。

---

## なぜ今「Discovery Loop」と「基盤整備」なのか？

従来の開発プロセスでは、以下のような「分断」が Discovery Loop（問題を発見し、解決策を検証するサイクル）を著しく阻害していました。

1. **コンテキストの分断**：フロントエンド（React/Next.jsなど）とインフラ/DevOps（Terraform, GitHub Actions, Datadog）の文脈が独立しており、エラー原因の追究に時間がかかる。
2. **「地味な作業」の放置**：OpenAPIスキーマの同期、型チェックの厳格化、依存ライブラリのセキュリティアップデート（Botany的な領域）が手動だとコストが高く、放置されやすい。

AIエディタにMCPを組み込むことで、**「エディタ側からインフラログ、型定義、ドキュメントへ直接アクセスし、AIに課題を発見・解決させる構造」** を作ることができます。

---

## Cursor × MCP によるコンテキスト統合アーキテクチャ

以下は、フロントエンド開発者がCursor上でMCPを介してプロダクションのログやスキーマにアクセスし、Discovery Loopを回す構成図です。

```
[ Cursor (AI Editor) ]
       │
       ├── (MCP Protocol) ──> [ OpenAPI / Supabase / GraphQL MCP ] ──> 最新の型・スキーマ取得
       │
       ├── (MCP Protocol) ──> [ Sentry / Datadog MCP ] ─────> リアルタイムエラーログ取得
       │
       └── (MCP Protocol) ──> [ GitHub / CI MCP ] ─────────> パイプライン状態 & 変更履歴
```

### 実践：カスタムMCPサーバーでCIエラーとフロントエンドの型を繋ぐ

ここでは、フロントエンドの型不整合やDevOps上のビルドエラーをCursorに直接フィードバックするための軽量なカスタムMCPサーバー（TypeScript）の例を紹介します。

`@modelcontextprotocol/sdk` を使用して、プロダクションやCI環境の型定義エラーの文脈をCursorに渡すツールを作成します。

```typescript
// mcp-server.ts
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import fs from "fs/promises";
import path from "path";

const server = new Server(
  { name: "devops-frontend-bridge", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

// ツール一覧の定義
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "get_latest_schema_diff",
        description: "バックエンドAPIとフロントエンド型定義の差分を検出します",
        inputSchema: {
          type: "object",
          properties: {
            schemaPath: { type: "string" },
          },
          required: ["schemaPath"],
        },
      },
    ],
  };
});

// ツールの実行処理
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === "get_latest_schema_diff") {
    const schemaPath = String(request.params.arguments?.schemaPath);
    
    // 実務ではここで remote API または CI 成果物を取得
    const rawSchema = await fs.readFile(path.resolve(schemaPath), "utf-8");
    
    return {
      content: [
        {
          type: "text",
          text: `[Schema Loaded successfully]\n${rawSchema.slice(0, 500)}...\n(型不整合のリスクがあるフィールドを修正候補としてCursorに提示します)`,
        },
      ],
    };
  }
  throw new Error("Tool not found");
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch(console.error);
```

---

## 現場で直面する「地雷」とMCPを活用した回避策

AIを活用した開発ループ（Discovery Loop）を回す上で、現場でよく発生するアンチパターン（地雷）と、その対策についてまとめます。

### 💣 地雷1: 「AIが生成したハルシネーション（嘘コード）によるサイレントブレイク」
- **発生原因**: コンテキストウィンドウに古い型定義や古いドキュメントしか存在しない状態のままAIに実装を行わせる。
- **対策**: MCP経由で **「常に最新のビルド結果/型チェック結果（`tsc --noEmit` の結果など）」** をリアルタイムでAIに読み込ませる。プロンプトだけでなくツール実行のループ内に型検証を組み込む。

### 💣 地雷2: 「インフラとフロントエンドの連携漏れ（環境変数のズレ）」
- **発生原因**: DevOps側で追加された環境変数やシークレットが、フロントエンドの `.env.example` や型定義（`env.mjs` 等）に反映されていない。
- **対策**: GitHub ActionsのCIとCursorをMCPで繋ぎ、デプロイ失敗時にCursor側で `@github-ci` ツールを呼んでログを解析させ、即座にフロントエンド側の環境変数バリデーション（Zod等）を修正させる。

```typescript
// env.mjs (Zodによる環境変数の厳格な型安全化)
import { createEnv } from "@t3-oss/env-nextjs";
import { z } from "zod";

export const env = createEnv({
  server: {
    DATABASE_URL: z.string().url(),
  },
  client: {
    NEXT_PUBLIC_API_URL: z.string().url(),
  },
  experimental__runtimeEnv: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  },
});
```

---

## まとめ：高速な「Discovery Loop」が地味な基盤を救う

地味な基盤整備（Botany）を怠ると、将来的に甚大なバグや障害（Crime）として跳ね返ってきます。

1. **MCP** を導入して、エディタ（Cursor）からインフラ・CI・型定義へのアクセスパスを確保する。
2. 課題の発見から修正までの **Discovery Loop** にAIを組み込み、開発者が手動で行うには面倒な「型同期」「ログ解析」「ドキュメント整合性維持」を自動化する。
3. これにより、フロントエンドエンジニアもDevOps領域のコンテキストを容易に扱いやすくなり、チーム全体の開発速度と品質が飛躍的に向上する。

最先端のAIモデルを「ただコードを書かせるツール」として使うのではなく、**「文脈を繋ぎ、ループを回す相棒」** としてアーキテクチャに組み込んでいきましょう。