"""
leaderboard.py
Saves / loads top-10 scores to  scores.json  in the same folder.
Also handles drawing the leaderboard overlay onto a cv2 frame.
"""

import json
import os
import cv2
import math
import time

SCORES_FILE = "scores.json"
MAX_ENTRIES = 10


def load_scores() -> list:
    if not os.path.exists(SCORES_FILE):
        return []
    try:
        with open(SCORES_FILE, "r") as f:
            data = json.load(f)
        # Validate structure
        return [e for e in data if "name" in e and "score" in e][:MAX_ENTRIES]
    except Exception:
        return []


def save_score(name: str, score: int) -> bool:
    """Save a new score. Returns True if it's a new high score (rank 1)."""
    entries = load_scores()
    entries.append({"name": name.strip() or "---", "score": score})
    entries.sort(key=lambda e: e["score"], reverse=True)
    entries = entries[:MAX_ENTRIES]
    try:
        with open(SCORES_FILE, "w") as f:
            json.dump(entries, f, indent=2)
    except Exception:
        pass
    return len(entries) > 0 and entries[0]["name"] == name and entries[0]["score"] == score


def is_high_score(score: int) -> bool:
    entries = load_scores()
    if len(entries) < MAX_ENTRIES:
        return True
    return score > entries[-1]["score"]


def draw_leaderboard(frame, current_score: int, pulse_t: float):
    """
    Draw a full-screen semi-transparent leaderboard panel.
    pulse_t  — pass time.time() so rank-1 row can pulse.
    """
    h, w = frame.shape[:2]
    entries = load_scores()

    # ── dark overlay ──
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, h), (5, 5, 20), -1)
    cv2.addWeighted(overlay, 0.72, frame, 0.28, 0, frame)

    # ── panel ──
    px, py, pw, ph = w // 2 - 320, 60, 640, 600
    cv2.rectangle(frame, (px, py), (px + pw, py + ph), (20, 20, 50), -1)
    cv2.rectangle(frame, (px, py), (px + pw, py + ph), (80, 160, 255), 2)

    # ── title ──
    _shadow_text(frame, "HIGH SCORES", (px + 105, py + 55),
                 1.6, (0, 230, 255), 3)

    # ── column headers ──
    _shadow_text(frame, "RANK", (px + 30,  py + 100), 0.7, (160, 160, 160), 1)
    _shadow_text(frame, "NAME", (px + 130, py + 100), 0.7, (160, 160, 160), 1)
    _shadow_text(frame, "SCORE", (px + 430, py + 100), 0.7, (160, 160, 160), 1)
    cv2.line(frame, (px + 20, py + 110), (px + pw - 20, py + 110), (80, 80, 120), 1)

    medals = ["🥇", "🥈", "🥉"]   # just labels; cv2 can't render emoji
    rank_colors = [
        (0, 215, 255),   # gold
        (180, 180, 180), # silver
        (60, 140, 210),  # bronze
    ]

    for i, entry in enumerate(entries):
        row_y = py + 150 + i * 44
        is_top = (i == 0)

        # Pulse top row
        if is_top:
            pulse = int(180 + 75 * math.sin(pulse_t * 3))
            row_color = (0, pulse, 255)
        elif i < 3:
            row_color = rank_colors[i]
        else:
            row_color = (200, 200, 200)

        # Highlight current score
        if entry["score"] == current_score:
            cv2.rectangle(frame,
                          (px + 15, row_y - 28),
                          (px + pw - 15, row_y + 8),
                          (40, 80, 40), -1)

        _shadow_text(frame, f"#{i + 1}", (px + 30, row_y),
                     0.85, row_color, 2)
        _shadow_text(frame, entry["name"][:12], (px + 130, row_y),
                     0.85, row_color, 2)
        _shadow_text(frame, str(entry["score"]), (px + 430, row_y),
                     0.85, row_color, 2)

    # ── footer ──
    _shadow_text(frame, "Press R to Play Again  |  ESC to Quit",
                 (px + 45, py + ph - 25), 0.65, (140, 140, 140), 1)


def _shadow_text(frame, text, pos, scale, color, thickness):
    cv2.putText(frame, text, (pos[0] + 2, pos[1] + 2),
                cv2.FONT_HERSHEY_SIMPLEX, scale, (0, 0, 0), thickness + 2)
    cv2.putText(frame, text, pos,
                cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness)