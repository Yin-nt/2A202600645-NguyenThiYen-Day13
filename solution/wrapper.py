"""Mitigation and observability boundary for the opaque agent."""
from __future__ import annotations

import re
import time

from telemetry.cost import cost_from_usage
from telemetry.logger import logger, set_correlation_id
from telemetry.redact import redact


_NOTE_MARKER = re.compile(r"(?im)^\s*(?:ghi\s*chu|note|system|instruction)\s*[:\-].*$")
_CONTACT_SUFFIX = re.compile(r"\s*\(\s*lien he\s*:\s*\[REDACTED(?::[A-Z_]+)?\]\s*\)", re.I)


def _sanitize(question):
    """Remove obvious instruction-bearing note lines while retaining order fields."""
    return _NOTE_MARKER.sub("[untrusted note removed]", question)


def _cache_key(question, config):
    return (
        question.casefold().strip(),
        config.get("provider"),
        config.get("model"),
    )


def _log(result, context, wall_ms, attempts, cache_hit, sanitized):
    meta = result.get("meta") or {}
    usage = meta.get("usage") or {}
    answer = result.get("answer") or ""
    _, pii_count = redact(answer)
    trace = result.get("trace") or []
    logger.log_event("AGENT_CALL", {
        "qid": context.get("qid"),
        "session_id": context.get("session_id"),
        "turn_index": context.get("turn_index"),
        "status": result.get("status"),
        "steps": result.get("steps"),
        "wall_ms": wall_ms,
        "latency_ms": meta.get("latency_ms"),
        "usage": usage,
        "cost_usd": cost_from_usage(meta.get("model", ""), usage),
        "tools_used": meta.get("tools_used", []),
        "trace": trace,
        "attempts": attempts,
        "cache_hit": cache_hit,
        "input_sanitized": sanitized,
        "pii_found_in_raw_answer": pii_count,
    })


def _grounded_answer(result):
    """Build the final answer from tool observations, never from model arithmetic."""
    stock = discount = shipping = None
    for step in result.get("trace") or []:
        observation = step.get("observation") or {}
        if step.get("tool") == "check_stock":
            stock = observation
        elif step.get("tool") == "get_discount":
            discount = observation
        elif step.get("tool") == "calc_shipping":
            shipping = observation

    if stock:
        if not stock.get("found", False):
            return "Khong tim thay san pham; khong the dat hang."
        if not stock.get("in_stock", False):
            return "San pham hien het hang; khong the dat hang."
    if shipping and (shipping.get("error") or shipping.get("cost_vnd") is None):
        return "Dia diem giao hang khong duoc ho tro; khong the dat hang."

    answer = result.get("answer") or ""
    if stock and shipping and stock.get("unit_price_vnd") is not None:
        quantity = _quantity_from_trace(result, stock)
        available = stock.get("quantity")
        if quantity and isinstance(available, int) and quantity > available:
            return "So luong yeu cau vuot qua ton kho; khong the dat hang."
        if quantity:
            percent = discount.get("percent", 0) if discount and discount.get("valid") else 0
            total = stock["unit_price_vnd"] * quantity * (100 - percent) // 100
            total += shipping["cost_vnd"]
            return f"Tong cong: {total} VND"
    return _CONTACT_SUFFIX.sub("", answer).strip()


def _quantity_from_trace(result, stock):
    weight = stock.get("weight_kg")
    for step in result.get("trace") or []:
        if step.get("tool") == "calc_shipping" and weight:
            total_weight = (step.get("observation") or {}).get("weight_kg")
            if isinstance(total_weight, (int, float)):
                quantity = round(total_weight / weight)
                if quantity > 0 and abs(quantity * weight - total_weight) < 0.001:
                    return quantity
    return None


def mitigate(call_next, question, config, context):
    set_correlation_id("req-" + str(context.get("qid", "unknown")))
    clean_question = _sanitize(question)
    conf = dict(config)
    conf.update({
        "temperature": 0.1,
        "loop_guard": True,
        "normalize_unicode": True,
        "redact_pii": True,
        "tool_budget": 4,
        "max_steps": 7,
    })

    cache = context.get("cache")
    lock = context.get("cache_lock")
    key = _cache_key(clean_question, conf)
    if cache is not None and lock is not None:
        with lock:
            cached = cache.get(key)
        if cached is not None:
            _log(cached, context, 0, 0, True, clean_question != question)
            return cached

    started = time.time()
    attempts = 0
    result = {}
    for attempts in range(1, 3):
        result = call_next(clean_question, conf)
        if result.get("status") == "ok":
            break
        time.sleep(0.15 * attempts)

    result["answer"] = _grounded_answer(result)
    answer = result.get("answer")
    if isinstance(answer, str):
        result["answer"] = redact(answer)[0]

    if result.get("status") == "ok" and cache is not None and lock is not None:
        with lock:
            cache[key] = result

    wall_ms = int((time.time() - started) * 1000)
    _log(result, context, wall_ms, attempts, False, clean_question != question)
    return result
