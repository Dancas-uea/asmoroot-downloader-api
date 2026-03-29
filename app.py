import requests
from flask import Flask, request, Response, stream_with_context
import yt_dlp
import os
import random

app = Flask(__name__)

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
]

def detectar_plataforma(url: str) -> str:
    url = url.lower()
    if 'tiktok.com' in url or 'vt.tiktok' in url:
        return 'tiktok'
    if 'youtube.com' in url or 'youtu.be' in url:
        return 'youtube'
    if 'instagram.com' in url:
        return 'instagram'
    return 'generic'


@app.route('/')
def home():
    return f"AsmoRoot Proxy v4.3 | yt-dlp {yt_dlp.version.__version__} | TikTok + YouTube + Instagram"


@app.route('/get_video', methods=['GET'])
def get_video():
    video_url = request.args.get('url', '').strip()
    if not video_url:
        return "URL requerida", 400

    ua = random.choice(USER_AGENTS)
    plataforma = detectar_plataforma(video_url)

    try:
        # ── Opciones según plataforma ─────────────────────────────────────────
        if plataforma == 'tiktok':
            ydl_opts = {
                'format': 'best[ext=mp4]/best',  # 'best' combinado, sin ffmpeg
                'quiet': True,
                'no_warnings': True,
                'user_agent': ua,
                'http_headers': {
                    'User-Agent': ua,
                    'Referer': 'https://www.tiktok.com/',
                    'Accept-Language': 'en-US,en;q=0.9',
                },
                'extractor_args': {
                    'tiktok': {
                        'webpage_download': True,
                    }
                },
            }

        elif plataforma == 'youtube':
            # YouTube ahora necesita player_client android para no pedir JS runtime
            ydl_opts = {
                'format': 'best[ext=mp4]/best',
                'quiet': True,
                'no_warnings': True,
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android'],
                    }
                },
                'http_headers': {
                    'User-Agent': 'com.google.android.youtube/19.09.37 (Linux; U; Android 11) gzip',
                },
            }

        elif plataforma == 'instagram':
            ydl_opts = {
                'format': 'best[ext=mp4]/best',
                'quiet': True,
                'no_warnings': True,
                'http_headers': {
                    'User-Agent': ua,
                    'Referer': 'https://www.instagram.com/',
                    'X-IG-App-ID': '936619743392459',
                },
            }

        else:
            ydl_opts = {
                'format': 'best[ext=mp4]/best',
                'quiet': True,
                'no_warnings': True,
                'http_headers': {'User-Agent': ua},
            }

        # ── Extraer info con yt-dlp ───────────────────────────────────────────
        direct_link = None
        video_id = 'video'
        content_type = 'video/mp4'

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            video_id = info.get('id', 'video')
            direct_link = info.get('url')

            # Fallback: buscar en formats[]
            if not direct_link and info.get('formats'):
                formatos = [
                    f for f in info['formats']
                    if f.get('url') and f.get('ext') == 'mp4'
                       and f.get('vcodec', 'none') != 'none'
                ]
                if not formatos:
                    # Si no hay mp4 con video, tomar cualquiera
                    formatos = [f for f in info['formats'] if f.get('url')]
                if formatos:
                    mejor = max(formatos, key=lambda f: f.get('tbr') or 0)
                    direct_link = mejor['url']

        if not direct_link:
            return f"No se pudo extraer el link ({plataforma})", 500

        # ── Headers CDN ───────────────────────────────────────────────────────
        if plataforma == 'youtube':
            cdn_headers = {
                'User-Agent': 'com.google.android.youtube/19.09.37 (Linux; U; Android 11) gzip',
                'Accept': '*/*',
                'Accept-Encoding': 'identity',
                'Range': 'bytes=0-',
            }
        elif plataforma == 'instagram':
            cdn_headers = {
                'User-Agent': ua,
                'Referer': 'https://www.instagram.com/',
                'Accept': '*/*',
                'Accept-Encoding': 'identity',
                'Range': 'bytes=0-',
            }
        else:  # tiktok / generic
            cdn_headers = {
                'User-Agent': ua,
                'Referer': 'https://www.tiktok.com/',
                'Accept': '*/*',
                'Accept-Encoding': 'identity',
                'Range': 'bytes=0-',
                'Sec-Fetch-Dest': 'video',
                'Sec-Fetch-Mode': 'no-cors',
            }

        r = requests.Session().get(
            direct_link,
            headers=cdn_headers,
            stream=True,
            timeout=120,
            allow_redirects=True
        )

        if r.status_code not in (200, 206):
            return f"CDN rechazó la petición ({plataforma}): HTTP {r.status_code}", 502

        content_length = int(r.headers.get('Content-Length', 0))

        # Validar que no sea una página de error HTML
        if 0 < content_length < 10000:
            preview = b''.join(list(r.iter_content(1024))[:2])
            if b'<html' in preview.lower():
                return f"{plataforma.capitalize()} bloqueó el acceso. Intenta con otra URL.", 403

        @stream_with_context
        def generate():
            for chunk in r.iter_content(chunk_size=65536):
                if chunk:
                    yield chunk

        resp_headers = {
            "Content-Disposition": f"attachment; filename=asmoroot_{video_id}.mp4",
            "Accept-Ranges": "bytes",
        }
        if content_length > 0:
            resp_headers["Content-Length"] = str(content_length)

        return Response(generate(), status=200, content_type='video/mp4', headers=resp_headers)

    except yt_dlp.utils.DownloadError as e:
        msg = str(e)
        if 'Private' in msg or 'removed' in msg or 'unavailable' in msg.lower():
            return "El video es privado, fue eliminado o no está disponible", 404
        if 'Sign in' in msg or 'login' in msg.lower():
            return f"Este video requiere inicio de sesión en {plataforma}", 401
        return f"yt-dlp no pudo procesar la URL: {msg}", 422

    except Exception as e:
        return f"Error técnico: {str(e)}", 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
