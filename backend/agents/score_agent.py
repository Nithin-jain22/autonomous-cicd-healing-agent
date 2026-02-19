from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ScoreBreakdown:
    base_score: int
    time_bonus: int
    commit_penalty: int
    final_score: int


class ScoreAgent:
    def calculate_score(self, execution_time_seconds: int, commits: int) -> ScoreBreakdown:
        base_score = 100
        time_bonus = 10 if execution_time_seconds < 300 else 0
        commit_penalty = (commits - 20) * 2 if commits > 20 else 0
        final_score = max(base_score + time_bonus - commit_penalty, 0)
        return ScoreBreakdown(
            base_score=base_score,
            time_bonus=time_bonus,
            commit_penalty=commit_penalty,
            final_score=final_score,
        )
