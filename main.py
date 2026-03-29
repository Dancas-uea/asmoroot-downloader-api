from flask import Flask, request, send_file
import yt_dlp
import io
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "Servidor AsmoRoot Activo 🚀 - UEA"

@app.route('/get_video', methods=['GET'])
def get_video():
    video_url = request.args.get('url')
    if not video_url:
        return "Falta la URL", 400

    # Configuración para descargar el video en memoria (RAM)
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'outtmpl': '-', # Esto le dice que lo mande a la salida estándar
        'logtostderr': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Obtenemos la info primero
            info = ydl.extract_info(video_url, download=False)
            video_title = info.get('title', 'video_asmoroot')
            
            # Ahora forzamos la descarga al buffer de memoria
            buffer = io.BytesIO()
            with yt_dlp.YoutubeDL(ydl_opts) as ydl_stream:
                # Extraemos y enviamos el archivo directamente
                return send_file(
                    io.BytesIO(ydl_stream.extract_info(video_url, download=True)['url']), # Esto es un truco para streaming
                    mimetype='video/mp4',
                    as_attachment=True,
                    download_name=f"{video_title}.mp4"
                )
    except Exception as e:
        # Plan B: Si el streaming falla, mandamos el link directo pero con headers de descarga
        try:
             with yt_dlp.YoutubeDL({'format': 'best'}) as ydl:
                info = ydl.extract_info(video_url, download=False)
                return info['url'] # Enviamos solo el link si el buffer falla
        except:
            return str(e), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
