from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
import subprocess

app = Flask(__name__)
CORS(app)

OVERLAY_FILE = "overlays.json"
UPLOAD_FOLDER = "static/uploads"
STREAM_FOLDER = "static/stream"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(STREAM_FOLDER, exist_ok=True)

# ================= OVERLAY CRUD ===================

def load_overlays():
    if not os.path.exists(OVERLAY_FILE):
        return []
    with open(OVERLAY_FILE, "r") as f:
        return json.load(f)

def save_overlays(overlays):
    with open(OVERLAY_FILE, "w") as f:
        json.dump(overlays, f, indent=2)

@app.route("/api/overlays", methods=["GET"])
def get_overlays():
    return jsonify(load_overlays())

@app.route("/api/overlays", methods=["POST"])
def add_overlay():
    overlays = load_overlays()
    data = request.json
    data["_id"] = str(len(overlays) + 1)
    overlays.append(data)
    save_overlays(overlays)
    return jsonify(data)

@app.route("/api/overlays/<overlay_id>", methods=["DELETE"])
def delete_overlay(overlay_id):
    overlays = [o for o in load_overlays() if o["_id"] != overlay_id]
    save_overlays(overlays)
    return jsonify({"success": True})

@app.route("/api/overlays/<overlay_id>", methods=["PUT"])
def update_overlay(overlay_id):
    overlays = load_overlays()
    data = request.json
    for o in overlays:
        if o["_id"] == overlay_id:
            o.update(data)
    save_overlays(overlays)
    return jsonify({"success": True})

# ================= FILE UPLOAD ===================

@app.route("/api/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files["file"]
    filename = file.filename
    save_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(save_path)
    return jsonify({"url": f"/static/uploads/{filename}"})


# ================= STREAM GENERATION ===================

@app.route("/api/start-stream", methods=["POST"])
def start_stream():
    data = request.json
    rtsp_url = data.get("rtsp_url")

    if not rtsp_url:
        return jsonify({"error": "RTSP URL or video file path required"}), 400

    output_path = os.path.join(STREAM_FOLDER, "stream.m3u8")

    # Clean old stream files
    for f in os.listdir(STREAM_FOLDER):
        os.remove(os.path.join(STREAM_FOLDER, f))

    # Detect if input is RTSP or a local video file
    if rtsp_url.lower().startswith(("rtsp://", "rtmp://", "http://", "https://")):
        input_type = "rtsp"
    else:
        input_type = "file"

    # FFmpeg command
    if input_type == "rtsp":
        print(f"🎥 Starting RTSP live stream from: {rtsp_url}")
        command = [
            "ffmpeg",
            "-rtsp_transport", "tcp",
            "-i", rtsp_url,
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-tune", "zerolatency",
            "-f", "hls",
            "-hls_time", "4",
            "-hls_list_size", "3",
            "-hls_flags", "delete_segments",
            output_path
        ]
    else:
        print(f"🎬 Playing local video file: {rtsp_url}")
        command = [
            "ffmpeg",
            "-re",
            "-i", rtsp_url,
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-f", "hls",
            "-hls_time", "4",
            "-hls_list_size", "0",  # keep all segments for full playback
            "-hls_flags", "independent_segments",
            output_path
        ]

    # Start FFmpeg
    subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # ✅ Use dynamic base URL (works locally & on Render)
    base_url = request.host_url.rstrip("/")
    stream_url = f"{base_url}/static/stream/stream.m3u8"

    return jsonify({"stream_url": stream_url})


@app.route("/static/stream/<path:filename>")
def stream_file(filename):
    return send_from_directory(STREAM_FOLDER, filename)


# ================= MAIN ===================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # ✅ use Render's dynamic port
    print(f"✅ Flask backend running on port {port}")
    app.run(host="0.0.0.0", port=port)
