"""
Assembles the complete 21-minute films and generates the 24-frame contact sheet:
1. video/out/chhaya_silent_captioned.mp4 (21:00 with burned-in captions)
2. video/out/chhaya_silent_nocaptions.mp4 (21:00 without captions)
3. video/out/contact_sheet.png (24 evenly-spaced frames in a 6x4 grid)
"""
import os
import sys
import json
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

BASE_DIR = Path(__file__).resolve().parent
STORYBOARD_FILE = BASE_DIR / "storyboard.json"
OUT_DIR = BASE_DIR / "out"
CLIPS_CAP_DIR = OUT_DIR / "clips"
CLIPS_NOCAP_DIR = OUT_DIR / "clips_nocap"

def get_video_info(video_path):
    cmd = [
        FFMPEG_EXE, "-i", str(video_path)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    duration = None
    for line in res.stderr.splitlines():
        if "Duration:" in line:
            # Duration: 00:21:00.00, start: ...
            parts = line.split("Duration:")[1].split(",")[0].strip().split(":")
            h, m, s = float(parts[0]), float(parts[1]), float(parts[2])
            duration = h * 3600 + m * 60 + s
            break
    return duration

def assemble_film(concat_txt, output_mp4, clips_dir, storyboard):
    print(f"\nBuilding concat list: {concat_txt.name} ({len(storyboard)} clips)...")
    lines = []
    total_expected = 0.0
    for s in storyboard:
        sid = s["id"]
        sec = s["seconds"]
        total_expected += sec
        clip_file = clips_dir / f"{sid}.mp4"
        if not clip_file.exists():
            raise FileNotFoundError(f"Missing clip: {clip_file}")
        # FFmpeg concat requires forward slashes or escaped backslashes
        posix_path = clip_file.resolve().as_posix()
        lines.append(f"file '{posix_path}'")
        
    with open(concat_txt, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
        
    print(f"Total expected duration: {total_expected:.2f}s ({total_expected/60:.2f} min)")
    print(f"Assembling {output_mp4.name} via FFmpeg concat demuxer...")
    
    music_file = OUT_DIR / "music.mp3"
    if music_file.exists():
        print(f"Mixing background music ({music_file.name}) at ambient volume 0.45 with fades...")
        fade_out_start = max(0.0, total_expected - 5.0)
        filter_str = f"[1:a]volume=0.45,afade=t=in:st=0:d=2,afade=t=out:st={fade_out_start:.1f}:d=5[a]"
        cmd = [
            FFMPEG_EXE, "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_txt),
            "-stream_loop", "-1",
            "-i", str(music_file),
            "-filter_complex", filter_str,
            "-map", "0:v",
            "-map", "[a]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-t", f"{total_expected:.2f}",
            str(output_mp4)
        ]
    else:
        cmd = [
            FFMPEG_EXE, "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_txt),
            "-c", "copy",
            str(output_mp4)
        ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("FFmpeg error:", res.stderr)
        raise RuntimeError(f"FFmpeg concat failed for {output_mp4}")
        
    size_mb = output_mp4.stat().st_size / (1024 * 1024)
    dur = get_video_info(output_mp4)
    print(f"  --> Successfully generated: {output_mp4.name}")
    print(f"      Size: {size_mb:.2f} MB | Measured Duration: {dur:.2f}s ({dur/60:.2f} min)")
    return dur

def generate_contact_sheet(video_path, output_png):
    print(f"\nGenerating 24-frame contact sheet from {video_path.name}...")
    temp_dir = OUT_DIR / "cs_temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract 24 frames across 1260 seconds
    num_frames = 24
    dur = 1260.0
    step = dur / (num_frames + 1)
    
    frame_files = []
    for i in range(1, num_frames + 1):
        t_sec = i * step
        mins = int(t_sec // 60)
        secs = int(t_sec % 60)
        time_str = f"{mins:02d}:{secs:02d}"
        
        frame_out = temp_dir / f"frame_{i:02d}.png"
        cmd = [
            FFMPEG_EXE, "-y",
            "-ss", f"{t_sec:.2f}",
            "-i", str(video_path),
            "-vframes", "1",
            "-q:v", "2",
            str(frame_out)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0 or not frame_out.exists():
            raise RuntimeError(f"Failed to extract frame at {t_sec}s")
        frame_files.append((frame_out, time_str))
        
    # Create contact sheet image: 6 columns x 4 rows
    cols, rows = 6, 4
    thumb_w, thumb_h = 320, 180
    pad = 12
    margin_top = 80
    margin_side = 20
    margin_bottom = 20
    
    sheet_w = margin_side * 2 + cols * thumb_w + (cols - 1) * pad
    sheet_h = margin_top + rows * thumb_h + (rows - 1) * pad + margin_bottom
    
    sheet = Image.new("RGB", (sheet_w, sheet_h), color="#FAFAF8")
    draw = ImageDraw.Draw(sheet)
    
    # Header title
    draw.text((margin_side, 20), "Chhaya Film Contact Sheet — 21:00 Feature (24-Frame Timeline Overview)", fill="#1A1915")
    draw.text((margin_side, 46), "Team SynapseX, D.B.S Kanpur · Happiest Health Digital Twin Challenge 2026", fill="#66645E")
    
    for idx, (f_path, time_str) in enumerate(frame_files):
        c = idx % cols
        r = idx // cols
        x = margin_side + c * (thumb_w + pad)
        y = margin_top + r * (thumb_h + pad)
        
        im = Image.open(f_path).resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        sheet.paste(im, (x, y))
        
        # Draw frame border
        draw.rectangle([x, y, x + thumb_w - 1, y + thumb_h - 1], outline="#E8E6E1", width=1)
        
        # Timestamp pill
        pill_w, pill_h = 64, 22
        draw.rectangle([x + 6, y + thumb_h - pill_h - 6, x + 6 + pill_w, y + thumb_h - 6], fill="#1A1915ee")
        draw.text((x + 14, y + thumb_h - pill_h - 4), time_str, fill="#FFFFFF")
        
    sheet.save(output_png, quality=95)
    print(f"  --> Saved contact sheet: {output_png.name} ({sheet_w}x{sheet_h}, {output_png.stat().st_size} bytes)")
    
    # Cleanup temp
    for f_path, _ in frame_files:
        if f_path.exists():
            f_path.unlink()
    if temp_dir.exists():
        temp_dir.rmdir()

def main():
    with open(STORYBOARD_FILE, "r", encoding="utf-8") as f:
        sb = json.load(f)
        
    # 1. Assembled Captioned Film
    concat_cap = OUT_DIR / "concat_captioned.txt"
    film_cap = OUT_DIR / "chhaya_silent_captioned.mp4"
    dur_cap = assemble_film(concat_cap, film_cap, CLIPS_CAP_DIR, sb)
    
    # 2. Assembled Non-Captioned Film
    concat_nocap = OUT_DIR / "concat_nocaptions.txt"
    film_nocap = OUT_DIR / "chhaya_silent_nocaptions.mp4"
    dur_nocap = assemble_film(concat_nocap, film_nocap, CLIPS_NOCAP_DIR, sb)
    
    # 3. 24-frame contact sheet
    contact_sheet_png = OUT_DIR / "contact_sheet.png"
    generate_contact_sheet(film_cap, contact_sheet_png)
    
    print("\n=======================================================")
    print("ASSEMBLY COMPLETE:")
    print(f"  1. Captioned Film:    {film_cap.name} ({dur_cap:.1f}s)")
    print(f"  2. Non-Captioned:     {film_nocap.name} ({dur_nocap:.1f}s)")
    print(f"  3. Contact Sheet:     {contact_sheet_png.name}")
    print("=======================================================\n")

if __name__ == "__main__":
    main()
