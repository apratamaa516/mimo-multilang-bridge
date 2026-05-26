---
name: multilang-bridge
description: Translate / summarize / extract structured facts across Indonesian, English, and Chinese using Xiaomi MiMo V2.5. Use when the main agent needs to consume multilingual sources (vendor docs, customer chats, vendor SDKs) and route to MiMo for cost-aware boilerplate translation work.
---

# multilang-bridge

OpenClaw skill for the **MiMo Multilang Bridge** — drop-in ID/EN/ZH translation + summarize + extract gateway.

## When to use

Use this skill when:
- User input is in a language other than the agent's working language (e.g. user types ID, agent reasons in EN)
- Source document is in Chinese (vendor SDK, Alibaba/Tencent/Xiaomi docs, etc.) and needs to be summarized
- Mixed-language thread or chat history needs unified summary
- Structured extraction (entities, dates, amounts, action items) from a long document

Skip when:
- Source and target language match
- Task needs deep reasoning (use main model directly)

## Setup

```bash
export MIMO_API_KEY=***
export MIMO_BASE_URL=https://token-plan-sgp.xiaomimimo.com/v1
```

## Verbs

### `bridge translate <target> <text>`

```bash
bridge translate id "The vendor's onboarding doc is 40 pages long"
bridge translate en "Halo sayang, bantu summarize doc Alibaba ya"
bridge translate zh "Please summarize the Q2 OKR document"
```

Output: 3-pass translation (literal → idiomatic → review).

### `bridge summarize <file|->`

```bash
bridge summarize vendor-sdk.md
cat slack-thread.txt | bridge summarize -
```

Output: bullet summary in target language (default EN, override `--lang id|zh`).

### `bridge extract <file|->`

```bash
bridge extract contract.txt
```

Output: JSON with `entities`, `dates`, `amounts`, `action_items`.

### `bridge synth <file|-> <target_lang>`

Full pipeline — translate (if needed) + summarize + extract + synthesize → one paragraph brief.

```bash
bridge synth alibaba-doc.zh id
```

## Cost-aware pattern

```bash
# Cheap: route boilerplate to MiMo
SUMMARY=$(bridge summarize vendor-spec.md)

# Then: pass clean summary to main reasoning step
echo "$SUMMARY" | run-main-reasoning
```

This pattern saves 30-50% of main-model context budget on multilingual ops workloads.

## Errors

- `401` → check `MIMO_API_KEY`
- `429` → rate limit, auto-retries 3x w/ exponential backoff
- `5xx` → MiMo API issue, fallback path falls through to error
