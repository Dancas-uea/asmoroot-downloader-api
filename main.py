import requests
from flask import Flask, request, Response
import yt_dlp
import os

app = Flask(__name__)

@app.route('/get_video', methods=['GET'])
def get_video():
    video_url = request.args.get('url')
    if not video_url:
        return "Error: URL vacía", 400

    try:
        # 1. Configuración de yt-dlp con User-Agent de iPhone
        # Esto evita que TikTok mande el HTML de bloqueo
        ydl_opts = {
            'format': 'best',
            'quiet': True,
            'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1'
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            direct_link = info['url']
            
        # 2. Petición al link de video
        headers = {
            'User-Agent': ydl_opts['user_agent'],
            'Referer': 'https://www.tiktok.com/'
        }
        
        r = requests.get(direct_link, headers=headers, stream=True, timeout=60)
        
        # VALIDACIÓN CRÍTICA: Si no es video, no lo mandamos
        content_type = r.headers.get('Content-Type', '')
        if 'text/html' in content_type or r.status_code != 200:
            return f"TikTok bloqueó la petición (Error {r.status_code})", 403

        # 3. Transmisión limpia de datos
        def stream_video():
            for chunk in r.iter_content(chunk_size=1024*1024):
                if chunk:
                    yield chunk

        return Response(
            stream_video(),
            content_type='video/mp4',
            headers={
                "Content-Disposition": "attachment; filename=video.mp4",
                "Content-Length": r.headers.get('Content-Length')
            }
        )
        
    except Exception as e:
        return f"Error técnico: {str(e)}", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
