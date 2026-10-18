import subprocess
from pathlib import Path
import imageio_ffmpeg

ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
clips_dir = Path("video/out/clips").resolve()
concat_file = Path("video/out/concat_full_90s.txt")

with open(concat_file, "w", encoding="utf-8") as f:
    for i in range(1, 21):
        sid = f"S{i:03d}"
        p = (clips_dir / f"{sid}.mp4").as_posix()
        f.write(f"file '{p}'\n")

out_mp4 = Path("video/out/cold_open_full_90s.mp4")
cmd = [ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(out_mp4)]
res = subprocess.run(cmd, capture_output=True, text=True)
print("Return code:", res.returncode)
print(f"Generated: {out_mp4} ({out_mp4.stat().st_size} bytes)")
