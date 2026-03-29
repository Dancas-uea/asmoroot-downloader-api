import requests
from flask import Flask, request, Response, stream_with_context
import yt_dlp
import os
import random
import subprocess
import sys

app = Flask(__name__)

# ── Auto-actualizar yt-dlp al arrancar ────────────────────────────────────────
try:
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp", "-q"],
        check=True, timeout=60
    )
    print("[AsmoRoot] yt-dlp actualizado correctamente")
except Exception as e:
    print(f"[AsmoRoot] No se pudo actualizar yt-dlp: {e}")

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
]


@app.route('/')
def home():
    return f"AsmoRoot Proxy v4.1 | yt-dlp {yt_dlp.version.__version__} ✅"


@app.route('/get_video', methods=['GET'])
def get_video():
    video_url = request.args.get('url')
    if not video_url:
        return "URL requerida", 400

    ua = random.choice(USER_AGENTS)

    try:
        ydl_opts = {
            'format': 'bestvideo[ext=mp4][vcodec^=h264]+bestaudio[ext=m4a]/bestvideo[ext=mp4]+bestaudio/best[ext=mp4]/best',
            'quiet': True,
            'no_warnings': True,
            'user_agent': ua,
            'http_headers': {
                'User-Agent': ua,
                'Referer': 'https://www.tiktok.com/',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            },
            'extractor_args': {
                'tiktok': {
                    'webpage_download': True,
                    'api_hostname': 'api22-normal-c-useast2a.tiktokv.com',
                }
            },
        }

        direct_link = None
        video_id = 'video'
        content_type = 'video/mp4'

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            video_id = info.get('id', 'video')
            direct_link = info.get('url')

            if not direct_link and info.get('formats'):
                formatos = [f for f in info['formats'] if f.get('url') and f.get('ext') == 'mp4']
                if formatos:
                    mejor = max(formatos, key=lambda f: f.get('tbr') or 0)
                    direct_link = mejor.get('url')
                    content_type = mejor.get('mimetype', 'video/mp4')

        if not direct_link:
            return "No se pudo extraer el link del video", 500

        cdn_headers = {
            'User-Agent': ua,
            'Referer': 'https://www.tiktok.com/',
            'Accept': '*/*',
            'Accept-Encoding': 'identity',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Range': 'bytes=0-',
            'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Sec-Fetch-Dest': 'video',
            'Sec-Fetch-Mode': 'no-cors',
            'Sec-Fetch-Site': 'cross-site',
        }

        session = requests.Session()
        r = session.get(direct_link, headers=cdn_headers, stream=True, timeout=120, allow_redirects=True)

        if r.status_code not in (200, 206):
            return f"CDN rechazó la petición: HTTP {r.status_code}", 502

        content_length = int(r.headers.get('Content-Length', 0))

        if content_length > 0 and content_length < 10000:
            body_preview = b''.join(list(r.iter_content(1024))[:2])
            if b'<html' in body_preview.lower() or b'error' in body_preview.lower():
                return "TikTok bloqueó el acceso al CDN.", 403

        @stream_with_context
        def generate():
            for chunk in r.iter_content(chunk_size=65536):
                if chunk:
                    yield chunk

        response_headers = {
            "Content-Disposition": f"attachment; filename=asmoroot_{video_id}.mp4",
            "Accept-Ranges": "bytes",
        }
        if content_length > 0:
            response_headers["Content-Length"] = str(content_length)

        return Response(generate(), status=200, content_type=content_type, headers=response_headers)

    except yt_dlp.utils.DownloadError as e:
        msg = str(e)
        if 'Private' in msg or 'removed' in msg:
            return "El video es privado o fue eliminado", 404
        return f"yt-dlp no pudo procesar la URL: {msg}", 422

    except Exception as e:
        return f"Error técnico: {str(e)}", 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
