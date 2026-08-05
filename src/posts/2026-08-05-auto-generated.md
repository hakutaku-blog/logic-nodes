---
title: "【2026年最新】Gemini API (google-genai) の 404 NOT_FOUND と Free Tier limit: 0 完全対策"
date: "2026-08-05"
tags: ["Gemini API", "Python", "GitHub Actions", "エラーハンドリング", "DevOps"]
description: "Gemini APIのv1beta移行や旧モデル廃止に伴う404エラーと、無料枠（Free Tier）での limit: 0 枯渇問題に対する実践的な回避策とブラックリスト設計を解説します。"
---

## はじめに

AIを活用したブログの自動生成やアプリケーションにおいて、LLM APIの突然の仕様変更やクォータ制限はシステム停止の致命的な原因となります。

特に最近のGoogle Gemini API（`google-genai` SDK）では、**旧モデルの廃止による 404 エラー**や、**無料枠（Free Tier）における突然の利用制限（limit: 0）**が頻発しています。本記事では、これらのエラーの背景と、システムを止めないための堅牢なフェイルセーフ設計（自己学習型ブラックリスト）について解説します。

---

## 1. 直面する2つの致命的エラー

### ① `404 NOT_FOUND` (旧モデルや未サポートAPIバージョンの呼び出し)
```json
"message": "models/gemini-1.5-flash is not found for API version v1beta, or is not supported for generateContent."
```
Google AI Studioでは、モデルの世代交代が非常に早く行われます。SDKがデフォルトで参照するAPIバージョン（例: `v1beta`）において、過去のモデル（`1.5-flash` や `1.5-pro` など）が突然未サポートとなり、上記のような404エラーを返すケースが増加しています。

### ② `429 RESOURCE_EXHAUSTED` (limit: 0)
```json
"message": "Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 0"
```
一時的なレート制限（RPM超過）とは異なり、`limit: 0` は**「現在利用中のAPIキー（無料枠）に対して、そのモデルの利用枠がそもそも提供されていない」**ことを意味します。例えば、最新の `gemini-2.0-flash` などが無料枠対象外となった瞬間にこのエラーが発生します。

---

## 2. 実践的対策：自己学習型ブラックリスト（Circuit Breaker）

これらのエラーに対し、「単にリスト内のモデルを片っ端から試す」設計では、毎日無駄なエラーリクエストを発生させてしまい、僅かな無料枠を浪費することになります。

そこで有効なのが**自己学習型のブラックリスト（サーキットブレーカー）パターン**です。

### アーキテクチャの要点
1. **エラーの永続化**: 404 や 429(limit: 0) のような「明日になっても回復しない致命的エラー」を検知した場合、そのモデル名を外部の JSON ファイル（`model_blacklist.json`）に記録します。
2. **リクエストの事前ブロック**: 次回以降の実行時は、ブラックリストに載っているモデルをリクエスト候補から完全に除外します。
3. **GitHubへの状態保存**: GitHub Actions でスクリプトがエラー終了した場合でも、`if: always()` を用いて必ずブラックリストの更新結果だけは Commit & Push してリポジトリに記憶させます。

### Python実装例のイメージ
```python
import json

def generate_with_circuit_breaker(models, prompt):
    blacklist = load_blacklist()
    valid_models = [m for m in models if m not in blacklist]
    
    for model in valid_models:
        try:
            return call_api(model, prompt)
        except Exception as e:
            if "404" in str(e) or "limit: 0" in str(e):
                blacklist[model] = str(e)
                save_blacklist(blacklist)
                # 致命的エラーの場合は次のモデルへフォールバック
            else:
                # 一時的エラーの場合は連投を避けて安全停止
                raise e
```

## まとめ

LLM APIのように提供側の仕様変更が激しい外部依存サービスを組み込む場合、**「APIは必ず失敗するもの」として設計する**ことが重要です。

ブラックリストによるアクセス遮断（Circuit Breaker）を実装することで、無駄なリクエストによるクォータ枯渇を防ぎ、真の意味で自律稼働する安定したシステムを構築することができます。
