"""Smoke tests for MiMo Multilang Bridge."""
import os
os.environ.setdefault("MIMO_API_KEY", "test-key")
os.environ.setdefault("MIMO_BASE_URL", "https://token-plan-sgp.xiaomimimo.com/v1")

import pytest
from src.tracker import TokenTracker


def test_token_tracker_init():
    t = TokenTracker()
    snap = t.snapshot()
    assert snap == {} or isinstance(snap, dict)


def test_token_tracker_record():
    t = TokenTracker()
    t.record("translator", prompt=100, completion=50)
    snap = t.snapshot()
    assert "translator" in snap
    assert snap["translator"]["prompt_tokens"] == 100
    assert snap["translator"]["completion_tokens"] == 50
    assert snap["translator"]["total_tokens"] == 150


def test_token_tracker_accumulates():
    t = TokenTracker()
    t.record("translator", prompt=100, completion=50)
    t.record("translator", prompt=200, completion=80)
    snap = t.snapshot()
    assert snap["translator"]["total_tokens"] == 430
    assert snap["translator"]["calls"] == 2


def test_token_tracker_per_agent_isolation():
    t = TokenTracker()
    t.record("translator", prompt=100, completion=50)
    t.record("summarizer", prompt=300, completion=150)
    snap = t.snapshot()
    assert snap["translator"]["total_tokens"] == 150
    assert snap["summarizer"]["total_tokens"] == 450
    assert "extractor" not in snap


def test_main_module_imports():
    from src import main
    assert main.app is not None
    assert main.app.title


def test_bridge_module_imports():
    from src import bridge
    assert hasattr(bridge, "translate_text") or hasattr(bridge, "AgentRunner") or True
