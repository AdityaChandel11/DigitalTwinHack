"""
Generates captions.srt, voiceover_script.md, and chapters.txt from storyboard.json.
"""
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
STORYBOARD_FILE = BASE_DIR / "storyboard.json"
OUT_DIR = BASE_DIR / "out"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def sec_to_srt_time(sec):
    hrs = int(sec // 3600)
    mins = int((sec % 3600) // 60)
    secs = int(sec % 60)
    millis = int(round((sec - int(sec)) * 1000))
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"

def sec_to_yt_time(sec):
    mins = int(sec // 60)
    secs = int(sec % 60)
    return f"{mins:02d}:{secs:02d}"

def main():
    with open(STORYBOARD_FILE, "r", encoding="utf-8") as f:
        sb = json.load(f)
        
    srt_lines = []
    script_lines = [
        "# Chhaya: 21-Minute Spoken Voiceover Script",
        "**Project:** Chhaya — A Type 2 Diabetes Digital Twin That Shows Its Work",
        "**Challenge:** Happiest Health Digital Twin Challenge 2026",
        "**Team:** Team SynapseX, D.B.S Kanpur",
        "**Total Duration:** 21:00 (1260.0 seconds) | **Total Cues:** 276",
        "",
        "> **Instructions for Recording:**",
        "> - Read at a steady, natural conversational pace (~2.15 words per second).",
        "> - Every cue fits comfortably within the allotted duration with a 0.5s breath pause.",
        "> - Emphasize measured numbers and scientific integrity.",
        "",
        "---",
        ""
    ]
    
    chapter_markers = []
    current_chapter = None
    curr_time = 0.0
    srt_index = 1
    
    for s in sb:
        ch = s["chapter"]
        sid = s["id"]
        sec = s["seconds"]
        cap = s["caption"]
        vis = s["visual"]
        
        start_t = curr_time
        end_t = curr_time + sec
        curr_time = end_t
        
        # New chapter check
        if ch != current_chapter:
            current_chapter = ch
            chapter_markers.append(f"{sec_to_yt_time(start_t)} {ch}")
            script_lines.extend([
                f"\n## Chapter: {ch} (starts at {sec_to_yt_time(start_t)})\n"
            ])
            
        # Add to SRT
        if cap.strip():
            srt_lines.append(str(srt_index))
            srt_lines.append(f"{sec_to_srt_time(start_t)} --> {sec_to_srt_time(end_t)}")
            srt_lines.append(cap.strip())
            srt_lines.append("")
            srt_index += 1
            
        # Add to VO Script
        time_str = f"[{sec_to_yt_time(start_t)} - {sec_to_yt_time(end_t)} | {sec:.1f}s]"
        script_lines.append(f"**{sid}** {time_str}")
        script_lines.append(f"*Visual: {vis}*")
        script_lines.append(f"> \"{cap.replace(chr(10), ' ')}\"\n")
        
    # Write captions.srt
    srt_path = OUT_DIR / "captions.srt"
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_lines))
    print(f"Generated {srt_path} ({len(srt_lines)} lines, {srt_index - 1} cues)")
    
    # Write voiceover_script.md
    script_path = OUT_DIR / "voiceover_script.md"
    with open(script_path, "w", encoding="utf-8") as f:
        f.write("\n".join(script_lines))
    print(f"Generated {script_path} ({len(script_lines)} lines)")
    
    # Write chapters.txt
    chapters_path = OUT_DIR / "chapters.txt"
    with open(chapters_path, "w", encoding="utf-8") as f:
        f.write("\n".join(chapter_markers) + "\n")
    print(f"Generated {chapters_path}:")
    for cm in chapter_markers:
        print(f"  {cm}")

if __name__ == "__main__":
    main()
