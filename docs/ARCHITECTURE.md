# Architecture

## Pipeline

```
Input text (any of ID/EN/ZH)
    │
    ▼
detect_lang() — heuristic, no model call
    │
    ▼
┌────────────────────────────────────────────────┐
│  Three specialist agents run in parallel       │
│                                                │
│  🌐 Translator  ─────────────────              │
│     ─ Pass 1: Literal (temp 0.0)               │
│     ─ Pass 2: Idiomatic rewrite (temp 0.4)     │
│     ─ Pass 3: Review against source (temp 0.1) │
│                                                │
│  📋 Summarizer ─────────────────               │
│     ─ Chunk text (4000-char windows, 200       │
│       overlap)                                 │
│     ─ Summarize each chunk in parallel         │
│     ─ Merge + dedupe via Pro model             │
│                                                │
│  🎯 Extractor  ─────────────────               │
│     ─ Pull entities, dates, amounts,           │
│       action items                             │
│     ─ Output structured JSON                   │
└─────────────┬──────────────────────────────────┘
              │
              ▼
   ⚡ Synthesizer (mimo-v2.5-pro)
   ─ Merge bullets + facts + translation
   ─ Surface reasoning_content trace
   ─ Output one-paragraph brief
```

## Why three passes for translation

Single-pass translation drifts on either accuracy (if temperature is high) or fluency (if temperature is low). The 3-pass pipeline decouples those concerns:

1. **Literal** captures meaning at temperature 0.0
2. **Idiomatic** rewrites for naturalness at temperature 0.4
3. **Review** verifies against source at temperature 0.1

This is similar to what professional translation teams do: translator, editor, reviewer.

## Why MiMo V2.5 specifically

| Feature | Value for this workload |
|---|---|
| Native ZH ↔ EN bilingual | High — Chinese vendor docs are first-class |
| `reasoning_content` field | Debug-friendly — trace why a word was chosen |
| Token Plan endpoint | Predictable cost at scale |
| Long context window | Whole-document summarize without splitting context |
| OpenAI-compatible | Drop-in via env config |

## Token consumption

| Operation | Calls | Tokens |
|---|---:|---:|
| Translate (3 passes) | 3 | ~3K |
| Summarize (typical doc, 3 chunks) | 4 | ~5K |
| Extract | 1 | ~3K |
| Synthesize (full pipeline) | ~9 | ~12K |

A SE Asia ops team running 200 chat triages + 30 doc summarizes + 50 thread digests per day naturally consumes 6M tokens / day. At 50 teams that's 300M / day, or **~9B / month**.

## Failure modes

| Failure | Mitigation |
|---|---|
| Single agent timeout | Tenacity retry w/ exponential backoff (3 attempts) |
| Malformed JSON from extractor | Regex match + fallback to raw text |
| Translation drift on rare languages | 3-pass pipeline catches drift in review step |
| Chunk boundary loss | 200-char overlap |

## Provider portability

The bridge is built on `AsyncOpenAI`, configured via `MIMO_BASE_URL` and `MIMO_API_KEY`. Swap providers via `.env`:

```env
# Xiaomi MiMo Token Plan (default — recommended for ZH-heavy workloads)
MIMO_BASE_URL=https://token-plan-sgp.xiaomimimo.com/v1
MIMO_MODEL_PRIMARY=mimo-v2.5-pro

# OpenAI fallback
MIMO_BASE_URL=https://api.openai.com/v1
MIMO_MODEL_PRIMARY=gpt-4o
```
