---
title: "【2026年最新】Gemini API無料枠の制限（429/クォータ枯渇）回避とGitHub Actions自動投稿パイプラインの完全堅牢化設計"
date: "2026-08-04"
tags: ["Gemini API", "GitHub Actions", "Python", "DevOps", "自動化"]
description: "Gemini APIの無料枠制限（15 RPM / 日時クォータ）やモデル非推奨（404）による自動パイプライン停止を防ぐ、実用的なフォールバックとセーフティ設計を徹底解説。"
---

## はじめに

完全自動化されたAI技術ブログや自動投稿パイプラインを運用する際、最も頻繁に遭遇する障壁が**「LLM APIのレート制限（429 RESOURCE_EXHAUSTED）」**や**「モデル仕様変更に伴う404エラー」**です。

本記事では、Google Gemini API と GitHub Actions を組み合わせた自動更新システムにおいて、APIクォータ枯渇や連続エラー通知によるシステムダウンを物理的に防止するセーフティ設計について解説します。

---

## 1. 自動投稿パイプラインで直面する主なエラーパターン

### ① 404 NOT_FOUND（モデルの非推奨・廃止）
Google AI Studio ではモデルのライフサイクルが早く、`gemini-2.5-flash` や旧バージョンモデルが事前予告なく新規リクエスト停止となるケースがあります。固定のモデル名だけをコードに記述していると、突然パイプライン全体が 404 エラーで停止します。

### ② 429 RESOURCE_EXHAUSTED（レート制限・日次クォータ枯渇）
Gemini API の無料枠（Free Tier）には以下の厳格な制限が存在します：
- **RPM (Requests Per Minute)**: 15 リクエスト/分
- **TPM (Tokens Per Minute)**: 1,000,000 トークン/分
- **RPD (Requests Per Day)**: 1,500 リクエスト/日

テスト実行やエラー時の安易な「自動再試行ループ」を実装してしまうと、わずか数分で1日の上限に達し、その日のAPI利用が完全にロックされます。

---

## 2. 解決策：堅牢なフェイルセーフ設計のPython実装

APIクォータ枯渇を防ぐ最大のポイントは、**「エラーが発生した際に無理な連投・リトライを行わず、静かに安全終了（Exit）して翌日の定期実行へ引き継ぐ」**ことです。

以下は、最新の `google-genai` SDK を使用した堅牢なフォールバック処理の実装例です。

```python
import os
from google import genai

# Google AI Studioのアクティブ推奨モデル優先順位
PREFERRED_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
]

def generate_text_with_safeguard(api_key: str, prompt: str):
    """
    安定モデルを試行し、クォータ制限時は連投せずに安全終了する
    """
    client = genai.Client(api_key=api_key)
    
    errors = []
    for model_name in PREFERRED_MODELS:
        try:
            print(f"Generating content using model: {model_name}...")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            if response and response.text:
                return response.text, model_name
        except Exception as e:
            err_str = str(e)
            print(f"Model {model_name} failed: {err_str}")
            errors.append(f"{model_name}: {err_str}")

    # クォータオーバー時は無理にリトライせず、安全にエラーを出して翌日へ委ねる
    raise RuntimeError(
        "API利用制限（クォータ制限）が検知されました。\n"
        "クォータリセット後（翌日）の定時投稿で自動復旧します。\n"
        f"詳細: {'; '.join(errors)}"
    )
```

---

## 3. GitHub Actions 運用上のベストプラクティス

1. **ワークフロー手動連投の防止**:
   テスト段階での手動トリガー（`workflow_dispatch`）は数分以上の十分なインターバルを空けて実行する。
2. **通知スパムの抑制**:
   エラー通知は1回の実行につき1通のみとし、エラー時のループ実行を防ぐ。
3. **静的なフォールバック手段の確保**:
   万が一APIが完全に停止した場合でも、サイト構造や `posts.json` / `sitemap.xml` の更新処理は正常に行われる独立設計にしておく。

---

## まとめ

完全自動化システムを長期間安定して運用するためには、**「例外発生時に焦ってリトライしまくらない設計（Fail-Safe Design）」**が不可欠です。

適切なフォールバックとクォータ管理を組み込むことで、運用コスト0円の完全無人ブログを末長く安定稼働させることができます。
