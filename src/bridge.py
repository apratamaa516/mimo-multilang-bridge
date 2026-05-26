"""Bridge core — translator + summarizer + extractor + synthesizer."""
import asyncio
import logging
import os
import re
from dataclasses import dataclass

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from src.tracker import TokenTracker

logger = logging.getLogger("bridge")


@dataclass
class BridgeConfig:
    base_url: str
    api_key: str
    model_primary: str
    model_secondary: str

    @classmethod
    def from_env(cls):
        key = os.getenv("MIMO_API_KEY")
        if not key:
            raise RuntimeError("MIMO_API_KEY not set")
        return cls(
            base_url=os.getenv("MIMO_BASE_URL", "https://token-plan-sgp.xiaomimimo.com/v1"),
            api_key=key,
            model_primary=os.getenv("MIMO_MODEL_PRIMARY", "mimo-v2.5-pro"),
            model_secondary=os.getenv("MIMO_MODEL_SECONDARY", "mimo-v2.5"),
        )


LANG_NAMES = {"id": "Indonesian", "en": "English", "zh": "Chinese (Simplified)"}


def detect_lang(text: str) -> str:
    """Cheap language detector — heuristic-only, no model call."""
    if re.search(r"[\u4e00-\u9fff]", text):
        return "zh"
    id_markers = re.findall(r"\b(yang|tidak|dengan|untuk|sudah|akan|bisa|gimana|gini)\b", text.lower())
    if len(id_markers) >= 2:
        return "id"
    return "en"


class Bridge:
    def __init__(self, tracker: TokenTracker | None = None, config: BridgeConfig | None = None):
        self.config = config or BridgeConfig.from_env()
        self.tracker = tracker or TokenTracker()
        self.client = AsyncOpenAI(base_url=self.config.base_url, api_key=self.config.api_key)

    async def aclose(self):
        await self.client.close()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    async def _chat(self, agent: str, messages: list[dict], model: str | None = None,
                    temperature: float = 0.2, max_tokens: int = 4000) -> dict:
        model = model or self.config.model_secondary
        resp = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        usage = resp.usage
        self.tracker.record(
            agent=agent,
            model=model,
            prompt=usage.prompt_tokens if usage else 0,
            completion=usage.completion_tokens if usage else 0,
        )
        choice = resp.choices[0]
        content = choice.message.content or ""
        reasoning = getattr(choice.message, "reasoning_content", None)
        return {"content": content, "reasoning": reasoning, "model": model}

    async def translate(self, text: str, target: str, source: str | None = None) -> dict:
        source = source or detect_lang(text)
        if source == target:
            return {"text": text, "source": source, "target": target, "passes": [], "skipped": True}

        src, tgt = LANG_NAMES[source], LANG_NAMES[target]

        # Pass 1 — literal
        p1 = await self._chat(
            "translator_p1",
            [
                {"role": "system", "content": f"Translate {src} → {tgt}. Literal pass: preserve exact meaning, ignore style. Output translation only, no commentary."},
                {"role": "user", "content": text},
            ],
            temperature=0.0,
        )

        # Pass 2 — idiomatic
        p2 = await self._chat(
            "translator_p2",
            [
                {"role": "system", "content": f"You are an idiomatic {tgt} editor. Rewrite the literal translation below to read naturally to a native {tgt} speaker. Keep meaning identical. Output rewritten text only."},
                {"role": "user", "content": f"Source ({src}):\n{text}\n\nLiteral ({tgt}):\n{p1['content']}"},
            ],
            temperature=0.4,
        )

        # Pass 3 — review
        p3 = await self._chat(
            "translator_p3",
            [
                {"role": "system", "content": f"Review the {tgt} translation against the {src} source for accuracy. If correct, output the translation verbatim. If incorrect, output corrected version. Output translation only."},
                {"role": "user", "content": f"Source ({src}):\n{text}\n\nCandidate ({tgt}):\n{p2['content']}"},
            ],
            temperature=0.1,
        )

        return {
            "text": p3["content"].strip(),
            "source": source,
            "target": target,
            "passes": [
                {"name": "literal", "model": p1["model"], "reasoning": p1.get("reasoning")},
                {"name": "idiomatic", "model": p2["model"], "reasoning": p2.get("reasoning")},
                {"name": "review", "model": p3["model"], "reasoning": p3.get("reasoning")},
            ],
        }

    async def summarize(self, text: str, max_bullets: int = 7, target_lang: str = "en") -> dict:
        chunks = self._chunk(text, size=4000, overlap=200)
        partial = await asyncio.gather(*[
            self._chat(
                f"summarizer_chunk_{i}",
                [
                    {"role": "system", "content": f"Summarize the chunk in {LANG_NAMES[target_lang]} as 2-4 bullet points. Output bullets only, prefix '- '."},
                    {"role": "user", "content": c},
                ],
            ) for i, c in enumerate(chunks)
        ])

        merged = "\n".join(p["content"] for p in partial)
        final = await self._chat(
            "summarizer_merge",
            [
                {"role": "system", "content": f"Merge and dedupe these bullets into max {max_bullets} key points in {LANG_NAMES[target_lang]}. Output bullets only, prefix '- '."},
                {"role": "user", "content": merged},
            ],
            model=self.config.model_primary,
            temperature=0.1,
        )
        bullets = [ln.strip(" -*•") for ln in final["content"].splitlines() if ln.strip().startswith(("-", "*", "•"))][:max_bullets]
        return {"bullets": bullets, "chunks_processed": len(chunks), "target_lang": target_lang}

    async def extract(self, text: str, target_lang: str = "en") -> dict:
        prompt = (
            "Extract a JSON object with these fields from the text: "
            "entities (list of {name, type}), dates (list of ISO strings), "
            "amounts (list of {value, currency}), action_items (list of strings). "
            f"All extracted values translated to {LANG_NAMES[target_lang]} where text-based. "
            "Output JSON only, no prose."
        )
        r = await self._chat(
            "extractor",
            [{"role": "system", "content": prompt}, {"role": "user", "content": text}],
            temperature=0.0,
        )
        import json
        try:
            data = json.loads(re.search(r"\{.*\}", r["content"], re.S).group(0))
        except Exception:
            data = {"raw": r["content"], "parse_error": True}
        return data

    async def synthesize(self, text: str, target_lang: str) -> dict:
        source = detect_lang(text)
        # Run translate (if needed) + summarize + extract in parallel
        tasks = [
            self.summarize(text, target_lang=target_lang),
            self.extract(text, target_lang=target_lang),
        ]
        if source != target_lang:
            tasks.append(self.translate(text, target=target_lang, source=source))
        results = await asyncio.gather(*tasks, return_exceptions=True)
        summary = results[0] if not isinstance(results[0], Exception) else {"error": str(results[0])}
        extract_ = results[1] if not isinstance(results[1], Exception) else {"error": str(results[1])}
        translation = results[2] if len(results) == 3 and not isinstance(results[2], Exception) else None

        synth = await self._chat(
            "synthesizer",
            [
                {"role": "system", "content": f"Synthesize a one-paragraph executive brief in {LANG_NAMES[target_lang]} combining the bullets, extracted facts, and translation context. Be concise, factual, no emoji."},
                {"role": "user", "content": f"Bullets: {summary.get('bullets')}\nFacts: {extract_}\nTranslation: {translation.get('text') if translation else 'n/a'}"},
            ],
            model=self.config.model_primary,
            temperature=0.2,
            max_tokens=600,
        )

        return {
            "brief": synth["content"].strip(),
            "reasoning_trace": synth.get("reasoning"),
            "summary": summary,
            "facts": extract_,
            "translation": translation,
        }

    @staticmethod
    def _chunk(text: str, size: int = 4000, overlap: int = 200) -> list[str]:
        if len(text) <= size:
            return [text]
        out = []
        i = 0
        while i < len(text):
            out.append(text[i : i + size])
            i += size - overlap
        return out
