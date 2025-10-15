import os
import subprocess

# 🔧 Set your video source here
# Example for local video:
# rtsp_url = "sample.mp4"
# Example for camera RTSP:
# rtsp_url = "rtsp://username:password@ip_address:port/stream"
rtsp_url = "sample.mp4"  # <-- change this if needed

# ✅ Output folder for HLS segments
output_dir = "static/stream"
os.makedirs(output_dir, exist_ok=True)

# ✅ Clean up old files before starting
for f in os.listdir(output_dir):
    if f.endswith(".ts") or f.endswith(".m3u8"):
        os.remove(os.path.join(output_dir, f))

# ✅ Detect source type
is_local_file = rtsp_url.lower().endswith(".mp4") or os.path.isfile(rtsp_url)

# ✅ Base FFmpeg command
ffmpeg_cmd = ["ffmpeg"]

# ✅ Handle local file vs RTSP differently
if is_local_file:
    print("🎬 Detected local file — looping video endlessly...")
    ffmpeg_cmd += ["-stream_loop", "-1", "-re"]  # Loop infinitely, simulate realtime
else:
    print("📡 Detected RTSP stream — streaming live...")
    ffmpeg_cmd += ["-rtsp_transport", "tcp", "-re"]

# ✅ Add FFmpeg HLS output settings
ffmpeg_cmd += [
    "-i", rtsp_url,                # input
    "-c:v", "libx264",             # video codec
    "-preset", "veryfast",         # speed/quality tradeoff
    "-tune", "zerolatency",        # low latency
    "-g", "25",                    # GOP size
    "-sc_threshold", "0",
    "-f", "hls",                   # output format
    "-hls_time", "2",              # 2s segments
    "-hls_list_size", "3",         # keep 3 segments in playlist
    "-hls_flags", "delete_segments+append_list",  # rolling buffer
    os.path.join(output_dir, "stream.m3u8"),      # output playlist
]

# ✅ Show info in console
print("🚀 Starting stream generator...")
print(f"🎥 Source: {rtsp_url}")
print(f"📁 Output: {output_dir}")
print("🔧 FFmpeg command:")
print(" ".join(ffmpeg_cmd))
print("--------------------------------------------------")

# ✅ Run FFmpeg process
try:
    subprocess.run(ffmpeg_cmd)
except KeyboardInterrupt:
    print("\n🛑 Stream generator stopped manually.")
except Exception as e:
    print(f"❌ Error: {e}")
