from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .models import Finding, Telemetry

_KEYWORD_SCORES: List[tuple[str, float]] = [
    ("race condition", 0.85),
    ("lock contention", 0.80),
    ("mutex", 0.75),
    ("atomic", 0.65),
    ("deadlock", 0.70),
    ("goroutine", 0.60),
    ("thread", 0.55),
    ("synchronization", 0.50),
    ("concurrent", 0.45),
]

_TOP_SCORE = 1.0


@dataclass
class Candidate:
    file_path: str
    symbol: str
    rationale: str
    suspicion_score: float


def _score_signal(signal: str) -> tuple[str, float]:
    low = signal.lower()
    for keyword, score in _KEYWORD_SCORES:
        if keyword in low:
            return (keyword, score)
    return ("unknown signal", 0.10)


def bisect_concurrency(
    finding: Finding,
    telemetry: Telemetry,
    max_candidates: int = 3,
) -> List[Candidate]:
    top = Candidate(
        file_path=finding.file_path,
        symbol=finding.symbol,
        rationale="Primary finding location identified by classifier",
        suspicion_score=_TOP_SCORE,
    )

    scored: List[tuple[float, str, str]] = []
    for signal in telemetry.log_signals:
        keyword, score = _score_signal(signal)
        if score < _TOP_SCORE:
            scored.append((score, signal, keyword))

    scored.sort(key=lambda t: (-t[0], t[1]))

    candidates: List[Candidate] = [top]
    seen_rationales: set[str] = {top.rationale}

    for score, signal, keyword in scored:
        if len(candidates) >= max_candidates:
            break
        rationale = f"Signal matched keyword '{keyword}': {signal}"
        if rationale in seen_rationales:
            continue
        seen_rationales.add(rationale)
        candidates.append(
            Candidate(
                file_path=finding.file_path,
                symbol=finding.symbol,
                rationale=rationale,
                suspicion_score=score,
            )
        )

    return candidates
