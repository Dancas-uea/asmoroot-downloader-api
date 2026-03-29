from flask import Flask, request, jsonify
import yt_dlp
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "Servidor AsmoRoot Activo 🚀"

@app.route('/get_video', methods=['GET'])
def get_video():
    video_url = request.args.get('url')
    if not video_url:
        return jsonify({"error": "Falta la URL"}), 400

    ydl_opts = {'format': 'best', 'quiet': True}

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            return jsonify({
                "direct_url": info.get('url'),
                "title": info.get('title', 'Video_AsmoRoot')
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)