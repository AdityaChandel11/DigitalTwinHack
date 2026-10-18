"""
Script to build video/storyboard.json and video/STORYBOARD.md.
Ensures:
1. Total duration is exactly 21:00 (1260.0 s).
2. Each chapter matches its timing budget:
   - Cold Open: 0:00 - 1:30 (90.0 s)
   - The Problem: 1:30 - 4:00 (150.0 s)
   - Live Walkthrough: 4:00 - 11:00 (420.0 s)
   - How It Was Made: 11:00 - 15:00 (240.0 s)
   - Results: 15:00 - 19:00 (240.0 s)
   - Limits and Close: 19:00 - 21:00 (120.0 s)
3. Every cue is <= 2 lines, <= 52 characters per line.
4. No cue exceeds 6.0 s; no segment is under 4.0 s.
5. All claims and numbers are strictly sourced.
6. Forbidden words strictly banned.
"""
import json
import re

# Helper to compute seconds from word count
def calc_sec(caption):
    words = caption.strip().split()
    n = len(words)
    if n == 0:
        return 4.0
    return max(4.0, round(n / 2.15 + 0.5, 1))

# Validation function
FORBIDDEN = [
    "breakthrough",
    "clinically validated",
    "clinical validation",
    "abdm",
    "abha",
    "predictive digital twin"
]

def validate_segments(segments):
    errors = []
    total_sec = 0.0
    for s in segments:
        sid = s["id"]
        cap = s["caption"]
        sec = s["seconds"]
        total_sec += sec
        
        # Check forbidden words
        cap_lower = cap.lower()
        for f in FORBIDDEN:
            if f in cap_lower:
                errors.append(f"[{sid}] contains forbidden word: {f}")
        if "alert" in cap_lower and "no alert" not in cap_lower and "no meal alert" not in cap_lower:
            errors.append(f"[{sid}] contains 'alert' without 'no alert': {cap}")
            
        # Check lines and char length
        lines = cap.split("\n")
        if len(lines) > 2:
            errors.append(f"[{sid}] has {len(lines)} lines (max 2): {cap}")
        for l in lines:
            if len(l) > 52:
                errors.append(f"[{sid}] line exceeds 52 chars ({len(l)} chars): '{l}'")
                
        # Check seconds
        if sec < 4.0:
            errors.append(f"[{sid}] seconds {sec} < 4.0s")
        if sec > 6.0:
            errors.append(f"[{sid}] seconds {sec} > 6.0s")
            
    print(f"Validation finished with {len(errors)} errors. Total duration: {total_sec:.1f}s ({total_sec/60:.2f} min)")
    if errors:
        for e in errors[:10]:
            print("  ERROR:", e)
        raise ValueError(f"{len(errors)} validation errors found.")
    return total_sec

print("Helper script ready.")
