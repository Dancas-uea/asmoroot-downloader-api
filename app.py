import requests
from flask import Flask, request, Response, stream_with_context
import yt_dlp
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "AsmoRoot Proxy v3.3 - Streaming Mode ✅"

@app.route('/get_video', methods=['GET'])
def get_video():
    video_url = request.args.get('url')
    if not video_url:
        return "URL requerida", 400

    try:
        ydl_opts = {
            'format': 'best',
            'quiet': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            direct_link = info['url']
            
        r = requests.get(direct_link, stream=True, timeout=120) # Aumentamos el timeout
        
        # Función generadora con contexto de flujo
        @stream_with_context
        def generate():
            for chunk in r.iter_content(chunk_size=4096): # Chunks más pequeños para flujo constante
                if chunk:
                    yield chunk

        return Response(
            generate(),
            content_type='video/mp4',
            headers={
                "Content-Disposition": "attachment; filename=video.mp4",
                "Content-Length": r.headers.get('Content-Length'),
                "Connection": "keep-alive" # Mantiene el túnel abierto
            }
        )
    except Exception as e:
        return str(e), 500
