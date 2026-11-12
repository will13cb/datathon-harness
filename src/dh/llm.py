"""The one place LLM calls happen (adapted from will13cb/hackathon-template api/app/llm.py).

LLM_PROVIDER = mock (offline, default) | bedrock (Amazon Bedrock Converse API).
Responses are cached in .cache/llm/ so reruns are free and the demo is reproducible.

    from dh.llm import ask
    ask("Summarise the main risks in this filing: ...", system="You are a buy-side analyst.")
"""

from __future__ import annotations

import hashlib
import json
import os
from functools import lru_cache

from .config import ROOT

CACHE = ROOT / ".cache" / "llm"


def provider() -> str:
    return os.getenv("LLM_PROVIDER", "mock").lower()


def model() -> str:
    return (
        os.getenv("BEDROCK_MODEL_ID", "us.amazon.nova-lite-v1:0")
        if provider() == "bedrock"
        else "mock"
    )


@lru_cache(maxsize=1)
def _bedrock():
    import boto3

    return boto3.client(
        "bedrock-runtime", region_name=os.getenv("AWS_REGION", "us-east-1")
    )


def ask(
    prompt: str,
    system: str = "",
    max_tokens: int = 1024,
    temperature: float = 0.0,
    cache: bool = True,
) -> str:
    p, m = provider(), model()
    if p == "mock":
        return f"[mock] {prompt[:200]}"
    if p != "bedrock":
        raise ValueError(f"LLM_PROVIDER={p!r}; use mock or bedrock")
    key = hashlib.sha256(
        json.dumps([m, system, prompt, max_tokens, temperature]).encode()
    ).hexdigest()
    path = CACHE / f"{key}.json"
    if cache and path.exists():
        return json.loads(path.read_text())["text"]
    kw = dict(
        modelId=m,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": max_tokens, "temperature": temperature},
    )
    if system:
        kw["system"] = [{"text": system}]
    resp = _bedrock().converse(**kw)
    text = "".join(b.get("text", "") for b in resp["output"]["message"]["content"])
    CACHE.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"model": m, "system": system, "prompt": prompt, "text": text})
    )
    return text
