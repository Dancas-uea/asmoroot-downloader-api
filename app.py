import requests
from flask import Flask, request, Response
import yt_dlp
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "AsmoRoot Proxy v3.2 Online ✅"

@app.route('/get_video', methods=['GET'])
def get_video():
    video_url = request.args.get('url')
    if not video_url:
        return "URL requerida", 400

    try:
        # 1. Extraer el link real con configuración de iPhone para evitar bloqueos
        ydl_opts = {
            'format': 'best',
            'quiet': True,
            'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1'
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            direct_link = info['url']
            
        # 2. Conectar al video de TikTok
        headers = {'User-Agent': ydl_opts['user_agent'], 'Referer': 'https://www.tiktok.com/'}
        r = requests.get(direct_link, headers=headers, stream=True, timeout=60)
        
        # 3. Transmitir con "Content-Length" para que Android no falle
        def generate():
            for chunk in r.iter_content(chunk_size=1024*1024):
                yield chunk

        return Response(
            generate(),
            content_type='video/mp4',
            headers={
                "Content-Disposition": "attachment; filename=video.mp4",
                "Content-Length": r.headers.get('Content-Length'), # ESTO EVITA LA FALLA
                "Connection": "keep-alive"
            }
        )
    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
