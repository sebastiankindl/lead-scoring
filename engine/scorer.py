from dataclasses import dataclass
from typing import Dict, List, Tuple
from .ontology import STRATEGIC_MAPPING

CONTEXT_MULTIPLIER = {
    "title": 2.0,
    "h1": 1.8,
    "body": 1.0,
    "footer": 0.2,
}

# optional: high signals
HIGH_SIGNAL_CONTEXTS = {"title", "h1"}

@dataclass
class LeadResult:
    primary_sector: str
    strategic_score: float
    strategic_fit: str
    confidence: str
    key_signals: List[str]
    why_call_next: str
    recommended_action: str
    time_saved_min_est: float
    high_signal_count: int


def _score_context(text: str, keywords: Dict[str, int], ctx: str) -> Tuple[float, List[Tuple[str, str, int]]]:
    """
    Returns:
      score,
      signals = list of (keyword, context, weight)
    """
    mult = CONTEXT_MULTIPLIER.get(ctx, 1.0)
    score = 0.0
    signals = []
    for kw, weight in keywords.items():
        if kw in text:
            score += weight * mult
            signals.append((kw, ctx, weight))
    return score, signals


def _confidence(signals: List[Tuple[str, str, int]]) -> str:
    # high: at least one strong keyword (weight>=3) AND found in strong context (title/h1),
    # OR many signals overall
    strong_ctx = any((w >= 3 and ctx in HIGH_SIGNAL_CONTEXTS) for _, ctx, w in signals)
    strong_weight = any((w >= 4) for _, _, w in signals)
    diverse_contexts = len(set(ctx for _, ctx, _ in signals))
    n = len(signals)

    if (strong_ctx and diverse_contexts >= 2) or (strong_weight and n >= 4) or (n >= 7):
        return "High"
    if n >= 2:
        return "Medium"
    return "Low"


def _why_call_and_action(primary_sector: str, signals: List[Tuple[str, str, int]]) -> Tuple[str, str]:
    # pick top 2 signals by (weight, context multiplier)
    def signal_strength(sig):
        kw, ctx, w = sig
        return w * CONTEXT_MULTIPLIER.get(ctx, 1.0)

    top = sorted(signals, key=signal_strength, reverse=True)[:2]
    if not top or primary_sector in ("No Match", "Connection Failed", "—"):
        return ("No reliable strategic signals found on the website.", "Deprioritize / Manual review")

    kw1, ctx1, _ = top[0]
    kw2, ctx2, _ = (top[1] if len(top) > 1 else (None, None, None))

    # short, executive-friendly
    if kw2:
        why = (f"Strong {primary_sector} signals driven by '{kw1}' ({ctx1}) and '{kw2}' ({ctx2}).")
    else:
        why = (f"Strong {primary_sector} signal driven by '{kw1}' ({ctx1}).")

    # recommended action
    if primary_sector in ("Life Science",):
        action = "Route to technical sales / request regulatory + spec details"
    elif primary_sector in ("Wind Energy",):
        action = "Ask for maintenance/tribology needs; propose reliability-focused additives"
    elif primary_sector in ("Mobility & Rubber",):
        action = "Qualify production process (compounding/extrusion); pitch processing aids"
    elif primary_sector in ("Construction & EPS",):
        action = "Validate polymer/EPS use-case; pitch polymerization or insulation additives"
    else:
        action = "Prioritize outreach with a sector-specific opener"

    return why, action


def score_lead(context_texts: Dict[str, str]) -> LeadResult:
    sector_scores = {}
    all_signals = []  # list of (kw, ctx, weight)

    for sector, meta in STRATEGIC_MAPPING.items():
        keywords = meta["keywords"]
        score = 0.0
        signals = []

        for ctx, txt in context_texts.items():
            s, sig = _score_context(txt, keywords, ctx)
            score += s
            signals.extend(sig)

        sector_scores[sector] = score
        all_signals.extend(signals)

    total_score = float(sum(sector_scores.values()))

    matched_sectors = [s for s, sc in sector_scores.items() if sc > 0]
    strategic_fit = ", ".join(matched_sectors) if matched_sectors else "No Match"

    primary = max(sector_scores, key=lambda k: sector_scores[k]) if total_score > 0 else "No Match"

    conf = _confidence(all_signals)
    why, action = _why_call_and_action(primary, all_signals)

    # time-saved estimate: map confidence -> minutes saved
    time_saved_map = {"High": 6.0, "Medium": 4.0, "Low": 2.0}
    time_saved = time_saved_map.get(conf, 3.0)

    # high-signal count: count signals in title/h1 or weight>=3
    high_signal_count = sum(1 for _, ctx, w in all_signals if (ctx in HIGH_SIGNAL_CONTEXTS or w >= 3))

    # key_signals string list
    key_signals = sorted({f"{kw} ({ctx})" for kw, ctx, _ in all_signals})

    return LeadResult(
        primary_sector=primary,
        strategic_score=round(total_score, 2),
        strategic_fit=strategic_fit,
        confidence=conf,
        key_signals=key_signals,
        why_call_next=why,
        recommended_action=action,
        time_saved_min_est=time_saved,
        high_signal_count=high_signal_count,
    )