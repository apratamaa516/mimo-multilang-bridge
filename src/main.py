"""MiMo Multilang Bridge — FastAPI gateway."""
import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.bridge import Bridge
from src.tracker import TokenTracker

load_dotenv()

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("mimo_bridge")

bridge: Bridge | None = None
tracker = TokenTracker()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global bridge
    bridge = Bridge(tracker=tracker)
    logger.info("Bridge ready (model=%s)", bridge.config.model_primary)
    yield
    await bridge.aclose()


app = FastAPI(
    title="MiMo Multilang Bridge",
    description="ID/EN/ZH translation + summarization gateway powered by Xiaomi MiMo V2.5",
    version="0.1.0",
    lifespan=lifespan,
)


class TranslateReq(BaseModel):
    text: str = Field(..., min_length=1, max_length=20_000)
    target: str = Field(..., pattern="^(id|en|zh)$")
    source: str | None = None


class SummarizeReq(BaseModel):
    text: str = Field(..., min_length=1, max_length=200_000)
    max_bullets: int = Field(default=7, ge=3, le=20)
    target_lang: str = Field(default="en", pattern="^(id|en|zh)$")


class ExtractReq(BaseModel):
    text: str = Field(..., min_length=1, max_length=200_000)
    target_lang: str = Field(default="en", pattern="^(id|en|zh)$")


class SynthesizeReq(BaseModel):
    text: str = Field(..., min_length=1, max_length=200_000)
    target_lang: str = Field(..., pattern="^(id|en|zh)$")


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "provider": "xiaomi-mimo",
        "model_primary": bridge.config.model_primary,
        "model_secondary": bridge.config.model_secondary,
    }


@app.get("/api/stats")
async def stats():
    return tracker.snapshot()


@app.post("/api/translate")
async def translate(req: TranslateReq):
    try:
        return await bridge.translate(req.text, target=req.target, source=req.source)
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/api/summarize")
async def summarize(req: SummarizeReq):
    try:
        return await bridge.summarize(req.text, max_bullets=req.max_bullets, target_lang=req.target_lang)
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/api/extract")
async def extract(req: ExtractReq):
    try:
        return await bridge.extract(req.text, target_lang=req.target_lang)
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/api/synthesize")
async def synthesize(req: SynthesizeReq):
    try:
        return await bridge.synthesize(req.text, target_lang=req.target_lang)
    except Exception as e:
        raise HTTPException(500, str(e))
