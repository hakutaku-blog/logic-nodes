```markdown
---
title: "Cursor × MCP (Model Context Protocol) 現場導入の地雷：コンテキスト汚染とセキュリティ事故を防ぐ実践ハック"
date: "2026-07-27"
tags: ["Cursor", "MCP", "LLM", "DevOps", "CI/CD", "Security"]
author: "Logic-Nodes 編集部"
description: "開発現場におけるCursorとMCPの本格運用で見えてきた「トークン暴走」「チーム間の設定崩壊」「秘匿情報漏洩」の回避策。プロダクション環境で今すぐ使える設定例とCI/CDハックを解説します。"
---

こんにちは。「Logic-Nodes」AI技術ライターチームです。

2026年現在、AIエディタの標準となった **Cursor** と、外部データソースやツールを柔軟に接続する **MCP（Model Context Protocol）** の組み合わせは、開発現場の生産性を劇的に向上させています。データベースのスキーマ確認、Kubernetesクラスタの状態取得、社内Wikiの参照などがエディタ内のチャットやAgentからシームレスに行える時代になりました。

しかし、チーム全体で本格運用を始めると、**「トークン消費の急増」「プロンプト応答の低速化」「意図しない秘匿情報のLLM送信」** といった現場特有の「地雷」に直面するケースが急増しています。

本記事では、Cursor × MCP 運用において現場で実際に発生しているトラブルの背景と、それを防ぐための実践的な設定ハック・CI/CDパイプラインでの自動化手法を解説します。

---

## 現場で発生する3つの「MCP地雷」

MCPは強力ですが、標準設定のままチーム開発に投入すると以下の問題が発生します。

### 1. レスポンス肥大化による「コンテキスト汚染」とコスト暴走
MCPサーバー（例: DBクエリツールやログ検索ツール）が巨大なJSONやログを出力した場合、それがそのままCursorのコンテキストウィンドウに注入されます。
結果として、**トークンコストが跳ね上がる**だけでなく、重要度の低いデータでコンテキストが埋まり、**LLMの推論精度が著しく低下（コンテキスト汚染）** します。

### 2. ローカルMCP設定（`mcp.json`）の秘伝のタレ化
開発者ごとに `.cursor/mcp.json`（またはグローバルな `mcp.json`）を個別に手動構築することで、チーム内で利用するMCPツールのバージョン差分や設定漏れが生じます。結果として「AさんのローカルではAgentが動くが、Bさんの環境ではエラーになる」という事態が発生します。

### 3. MCP経由のプロンプトインジェクション・秘匿情報流出
MCPツールが社内の未マスクデータ（顧客の個人情報、環境変数のAPI Key等）を取得し、そのまま外部LLM API（OpenAI, Anthropic等）に送信されてしまうリスクです。

---

## 解決策：現場で効く3つの実践ハック

これらの地雷を回避し、安全かつ高効率にMCPを運用するための解決策を提示します。

---

### ハック1: MCPサーバー出力のサニタイズ＆軽量化ラッパーの導入

MCPツールが Cursor にレスポンスを返す手前で、**「文字列の切り捨て（Truncation）」** と **「マスク処理」** を行う軽量なミドルウェア（または自作MCPラッパー）を挟みます。

以下は、TypeScriptで記述した「MCPレスポンスのコンテキストガード」の例です。

```typescript
// mcp-guard-wrapper.ts
// 既存のMCPツールの出力をラップし、トークン暴走と情報漏洩を防ぐ

const MAX_RESPONSE_LENGTH = 1500; // LLMに渡す最大文字数

export function sanitizeAndTruncateOutput(rawOutput: unknown): string {
  let stringified = typeof rawOutput === 'string' 
    ? rawOutput 
    : JSON.stringify(rawOutput, null, 2);

  // 1. 簡易マスク処理（API Keyやトークンと思われる文字列を置換）
  stringified = stringified.replace(/(sk-[a-zA-Z0-9]{32,}|Bearer\s+[a-zA-Z0-9\-\._~\+\/]+=*)/g, '[REDACTED_SECRET]');

  // 2. 文字数制限（コンテキスト汚染防止）
  if (stringified.length > MAX_RESPONSE_LENGTH) {
    const truncated = stringified.slice(0, MAX_RESPONSE_LENGTH);
    return `${truncated}\n\n... [警告: レスポンスが長すぎるため上位 ${MAX_RESPONSE_LENGTH} 文字に省略されました。必要に応じてクエリ条件を絞り込んでください。]`;
  }

  return stringified;
}
```

このガードをMCPサーバーのTool実行ロジックの直下に組み込むことで、LLMへ送信されるデータを常に安全かつコンパクトに保つことができます。

---

### ハック2: リポジトリ管理された `.cursor/mcp.json` と環境変数テンプレート

チームでMCP構成を同期するため、プロジェクト直下に `.cursor/mcp.json.template` を配置し、環境変数のみ `.env.local` から読み込む構成を標準化します。

#### 設定例: `.cursor/mcp.json.template`

```json
{
  "mcpServers": {
    "internal-db-inspector": {
      "command": "node",
      "args": ["./scripts/mcp/db-inspector.js"],
      "env": {
        "DB_READ_ONLY_URL": "${MCP_DB_READ_ONLY_URL}",
        "LOG_LEVEL": "warn"
      }
    },
    "github-issue-fetcher": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${MCP_GITHUB_TOKEN}"
      }
    }
  }
}
```

このテンプレートから、ローカル開発環境起動時（または `npm run setup` 時）に実際の `.cursor/mcp.json` を生成するスクリプトをCI/開発フローに組み込みます。これにより、**プロジェクト共通のMCPツール群をGit管理化** できます。

---

### ハック3: CI/CDでの `mcp.json` 検証とリークチェックの自動化

プルリクエスト（PR）作成時に、誤ってハードコードされたAPI Keyや不正なMCP設定がコミットされていないかを GitHub Actions で検証します。

#### GitHub Actions ワークフロー例 (`.github/workflows/mcp-ci-check.yml`)

```yaml
name: MCP Security and Syntax Check

on:
  pull_request:
    paths:
      - '.cursor/**'
      - 'scripts/mcp/**'

jobs:
  validate-mcp:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Validate JSON Syntax
        run: |
          jq . .cursor/mcp.json.template > /dev/null || (echo "Invalid JSON in mcp.json.template" && exit 1)

      - name: Secret Scan on MCP Configs
        uses: trufflesecurity/trufflehog-actions-experimental@main
        with:
          path: ./
          base: ${{ github.event.pull_request.base.sha }}
          head: ${{ github.event.pull_request.head.sha }}
          extra_args: --path-include-glob=".cursor/*"

      - name: Ensure no hardcoded tokens in template
        run: |
          if grep -E 'sk-[a-zA-Z0-9]{20,}' .cursor/mcp.json.template; then
            echo "Error: Hardcoded API Key detected in .cursor/mcp.json.template!"
            exit 1
          fi
```

---

## 運用チェックリスト

Cursor × MCP をチームで安全に利用するためのチェックリストです。デプロイやオンボーディングの際にご活用ください。

- [ ] **リードオンリー権限の徹底**: MCP経由でアクセスするDBやAPIアカウントは、書き込み権限を剥奪した読み取り専用のものを使用しているか？
- [ ] **出力量制限（Truncation）**: 1回のMCPツール実行でCursorに返されるデータ量が2,000文字（または約1,000トークン）以下に制限されているか？
- [ ] **設定ファイルのGit管理**: `.cursor/mcp.json` のテンプレート化が行われ、実際の鍵情報は `.env` 等で分離されているか？
- [ ] **CIでのシークレットスキャン**: GitHub Actions等でMCP関連ファイルにシークレットが紛れ込んでいないか自動検証されているか？

---

## まとめ

2026年のエンジニアリングにおいて、CursorとMCPは「開発速度を10倍にする強力な武器」ですが、ガードレールなしに導入すると「トークン破産」や「セキュリティ事故」を引き起こす諸刃の剣となります。

1. **MCPの出力はラッパーで切り捨て・サニタイズする**
2. **`mcp.json` はテンプレート化してリポジトリで管理する**
3. **CI/CDパイプラインでシークレット混入を機械的にブロックする**

この3点を徹底し、安全かつ快適なAI駆動開発環境を構築していきましょう。

---
*Logic-Nodesでは、最新のAIツール活用ノウハウやインフラ自動化の実践ハックを随時発信しています。記事へのフィードバックや取り上げてほしいトピックがあれば、ぜひコメント欄や公式X（旧Twitter）までお寄せください。*
```