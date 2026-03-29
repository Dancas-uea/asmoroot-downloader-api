import requests
from flask import Flask, request, Response, stream_with_context
import yt_dlp
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "AsmoRoot Proxy v3.4 - Fixed Support ✅"

@app.route('/get_video', methods=['GET'])
def get_video():
    video_url = request.args.get('url')
    if not video_url:
        return "URL requerida", 400

    try:
        # Configuración Pro para extraer el link real sin marcas de agua
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            # Intentamos obtener el link sin marca de agua si está disponible
            direct_link = info.get('url') or info.get('formats')[0].get('url')
            
        # CABECERAS CRÍTICAS: Sin esto, el video sale 'sin soporte' o corrupto
        headers = {
            'User-Agent': ydl_opts['user_agent'],
            'Referer': 'https://www.tiktok.com/',
            'Range': 'bytes=0-' # Esto ayuda a que el flujo inicie correctamente
        }
        
        r = requests.get(direct_link, headers=headers, stream=True, timeout=120)
        
        @stream_with_context
        def generate():
            for chunk in r.iter_content(chunk_size=8192): # Chunk balanceado
                if chunk:
                    yield chunk

        # Construimos la respuesta forzando el tipo de video
        response = Response(
            generate(),
            content_type='video/mp4',
            headers={
                "Content-Disposition": "attachment; filename=asmoroot_video.mp4",
                "Content-Length": r.headers.get('Content-Length'),
                "Connection": "keep-alive",
                "Accept-Ranges": "bytes"
            }
        )
        return response

    except Exception as e:
        return f"Error en el servidor: {str(e)}", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
