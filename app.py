import requests
from flask import Flask, request, Response
import yt_dlp
import os

app = Flask(__name__)

# Ruta para probar si el servidor funciona (Evita el 404)
@app.route('/')
def home():
    return "<h1>AsmoRoot Proxy v3.1</h1><p>Estado: Online ✅</p>"

@app.route('/get_video', methods=['GET'])
def get_video():
    video_url = request.args.get('url')
    if not video_url:
        return "Error: URL de video requerida", 400

    try:
        # Configuración Pro para evitar bloqueos de TikTok
        ydl_opts = {
            'format': 'best',
            'quiet': True,
            'no_warnings': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            direct_link = info['url']
            
        # Headers para que TikTok crea que somos un navegador real
        headers = {
            'User-Agent': ydl_opts['user_agent'],
            'Referer': 'https://www.tiktok.com/'
        }
        
        # Hacemos el tunel (Proxy)
        r = requests.get(direct_link, headers=headers, stream=True, timeout=60)
        
        # Si lo que viene no es video (es HTML de error), avisamos
        if 'text/html' in r.headers.get('Content-Type', ''):
            return "Error: TikTok envio un bloqueo (HTML). Intenta otro link.", 403

        # Transmitimos el video bit a bit
        def generate():
            for chunk in r.iter_content(chunk_size=1024*1024):
                if chunk:
                    yield chunk

        return Response(
            generate(),
            content_type='video/mp4',
            headers={
                "Content-Disposition": "attachment; filename=video_asmoroot.mp4",
                "Content-Length": r.headers.get('Content-Length')
            }
        )
        
    except Exception as e:
        return f"Error en el tunel: {str(e)}", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
