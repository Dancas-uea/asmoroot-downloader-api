import requests
from flask import Flask, request, Response
import yt_dlp
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "Servidor AsmoRoot Proxy Activo 🚀 - UEA"

@app.route('/get_video', methods=['GET'])
def get_video():
    video_url = request.args.get('url')
    if not video_url:
        return "Error: Falta la URL del video", 400

    try:
        # Configuramos yt-dlp para extraer solo el link directo
        ydl_opts = {'format': 'best', 'quiet': True, 'no_warnings': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            direct_link = info['url']
            
            # Simulamos ser un navegador para que TikTok no nos bloquee
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.tiktok.com/'
            }
            
            # Azure descarga el video por partes y las envía al celular (Streaming)
            r = requests.get(direct_link, headers=headers, stream=True, timeout=30)
            
            return Response(
                r.iter_content(chunk_size=1024*1024),
                content_type=r.headers.get('Content-Type', 'video/mp4'),
                headers={
                    "Content-Disposition": "attachment; filename=video_asmoroot.mp4",
                    "Access-Control-Allow-Origin": "*"
                }
            )
    except Exception as e:
        return f"Error en el servidor: {str(e)}", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
