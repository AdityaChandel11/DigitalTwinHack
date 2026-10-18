"""
Assembles the 60-second Cold Open sample MP4 with burned-in captions.
Concatenates S001 through S013 (or exact 60.0s) into video/out/sample_cold_open.mp4.
"""
import os
import json
import subprocess
from pathlib import Path
import imageio_ffmpeg

FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
BASE_DIR = Path(__file__).resolve().parent
CLIPS_DIR = BASE_DIR / "out" / "clips"
OUT_DIR = BASE_DIR / "out"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def assemble(target_duration=60.0):
    with open(BASE_DIR / "storyboard.json", "r", encoding="utf-8") as f:
        sb = json.load(f)
        
    cold_open = [s for s in sb if s["chapter"] == "Cold Open"]
    
    # We select segments up to ~60s
    selected = []
    total_time = 0.0
    for s in cold_open:
        selected.append(s)
        total_time += s["seconds"]
        if total_time >= target_duration:
            break
            
    print(f"Selected {len(selected)} segments totaling {total_time:.1f}s for Cold Open sample:")
    for s in selected:
        print(f"  [{s['id']}] {s['seconds']}s: {s['caption'][:30]}...")
        
    concat_list = OUT_DIR / "concat_list.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        for s in selected:
            clip_path = (CLIPS_DIR / f"{s['id']}.mp4").resolve()
            if not clip_path.exists():
                raise FileNotFoundError(f"Clip not found: {clip_path}")
            # Format for ffmpeg concat demuxer (escaped for windows)
            p_str = str(clip_path).replace("\\", "/")
            f.write(f"file '{p_str}'\n")
            
    output_mp4 = OUT_DIR / "sample_cold_open.mp4"
    
    cmd = [
        FFMPEG_EXE, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_list),
        "-c", "copy",
        str(output_mp4)
    ]
    
    print("Running concatenation:", " ".join(cmd))
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("Concat error:", res.stderr)
        raise RuntimeError("Concat failed")
        
    print(f"\nSuccessfully generated Cold Open sample: {output_mp4}")
    print(f"Size: {output_mp4.stat().st_size} bytes")

if __name__ == "__main__":
    assemble(60.0)
