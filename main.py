import requests
from flask import Flask, request, Response
import yt_dlp
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "Servidor AsmoRoot Proxy v3.1 🚀"

@app.route('/get_video', methods=['GET'])
def get_video():
    video_url = request.args.get('url')
    if not video_url:
        return "Error: URL requerida", 400

    try:
        # 1. Extraer el link real con yt-dlp
        ydl_opts = {'format': 'best', 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            direct_link = info['url']
            
        # 2. Pedir el video a TikTok con un User-Agent real
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.tiktok.com/'
        }
        
        # Usamos stream=True para no llenar la RAM de Azure
        response = requests.get(direct_link, headers=headers, stream=True, timeout=60)
        
        # 3. Enviar los datos conforme llegan (Chunked Transfer)
        def generate():
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk

        return Response(
            generate(),
            content_type=response.headers.get('Content-Type', 'video/mp4'),
            headers={
                "Content-Disposition": "attachment; filename=video_asmoroot.mp4",
                "Content-Length": response.headers.get('Content-Length') # MUY IMPORTANTE
            }
        )
    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
