import requests
from flask import Flask, request, Response, stream_with_context
import yt_dlp
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "AsmoRoot Proxy v3.6 - Bypass Mode ✅"

@app.route('/get_video', methods=['GET'])
def get_video():
    video_url = request.args.get('url')
    if not video_url:
        return "URL requerida", 400

    try:
        # 1. Configuración de extracción profunda
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'quiet': True,
            'no_warnings': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            # Buscamos el link más directo posible
            direct_link = info.get('url')
            
        if not direct_link:
            return "No se pudo extraer el link del video", 500

        # 2. Petición al CDN de TikTok con cabeceras de simulación humana
        headers = {
            'User-Agent': ydl_opts['user_agent'],
            'Referer': 'https://www.tiktok.com/',
            'Range': 'bytes=0-'
        }
        
        # Usamos un timeout largo y permitimos redirecciones
        r = requests.get(direct_link, headers=headers, stream=True, timeout=120, allow_redirects=True)
        
        # VALIDACIÓN CLAVE: Si el contenido es muy pequeño o es texto, es un error
        content_length = int(r.headers.get('Content-Length', 0))
        if content_length < 50000: # Menos de 50KB no es un video
            return "Error: TikTok bloqueó el acceso. Intenta de nuevo en unos minutos.", 403

        @stream_with_context
        def generate():
            for chunk in r.iter_content(chunk_size=65536): # Chunks grandes para flujo estable
                if chunk:
                    yield chunk

        return Response(
            generate(),
            content_type='video/mp4',
            headers={
                "Content-Disposition": f"attachment; filename=asmoroot_{info.get('id', 'video')}.mp4",
                "Content-Length": str(content_length),
                "Accept-Ranges": "bytes"
            }
        )

    except Exception as e:
        return f"Error técnico: {str(e)}", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
