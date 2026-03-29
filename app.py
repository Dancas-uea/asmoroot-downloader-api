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
    print("[AsmoRoot] yt-dlp actualizado")
except Exception as e:
    print(f"[AsmoRoot] No se pudo actualizar yt-dlp: {e}")

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
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

def construir_opts(plataforma: str, ua: str) -> dict:
    """Opciones de yt-dlp adaptadas por plataforma."""

    base = {
        'quiet': True,
        'no_warnings': True,
        'user_agent': ua,
    }

    if plataforma == 'youtube':
        base.update({
            # mp4 progresivo preferido; fallback a webm si no hay mp4
            'format': 'bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            # Evitar restricciones geográficas y de edad
            'age_limit': 99,
            # YouTube necesita que parezca un cliente Android para no pedir po_token
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],
                    'player_skip': ['webpage', 'configs'],
                }
            },
            'http_headers': {
                'User-Agent': 'com.google.android.youtube/19.09.37 (Linux; U; Android 11) gzip',
                'Accept-Language': 'en-US,en;q=0.9',
            },
        })

    elif plataforma == 'tiktok':
        base.update({
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'extractor_args': {
                'tiktok': {
                    'webpage_download': True,
                    'api_hostname': 'api22-normal-c-useast2a.tiktokv.com',
                }
            },
            'http_headers': {
                'User-Agent': ua,
                'Referer': 'https://www.tiktok.com/',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'DNT': '1',
            },
        })

    elif plataforma == 'instagram':
        base.update({
            'format': 'best[ext=mp4]/best',
            'http_headers': {
                'User-Agent': ua,
                'Referer': 'https://www.instagram.com/',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'X-IG-App-ID': '936619743392459',
            },
        })

    else:
        base.update({
            'format': 'best[ext=mp4]/best',
            'http_headers': {'User-Agent': ua},
        })

    return base


@app.route('/')
def home():
    return f"AsmoRoot Proxy v4.2 | yt-dlp {yt_dlp.version.__version__} | TikTok + YouTube + Instagram ✅"


@app.route('/get_video', methods=['GET'])
def get_video():
    video_url = request.args.get('url', '').strip()
    if not video_url:
        return "URL requerida", 400

    ua = random.choice(USER_AGENTS)
    plataforma = detectar_plataforma(video_url)
    ydl_opts = construir_opts(plataforma, ua)

    try:
        direct_link = None
        video_id = 'video'
        content_type = 'video/mp4'

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            video_id = info.get('id', 'video')

            # Buscar URL directa
            direct_link = info.get('url')

            # Si viene con streams separados (video+audio), usar el de video
            # (en Android descargamos solo el video mp4 combinado)
            if not direct_link and info.get('requested_formats'):
                for fmt in info['requested_formats']:
                    if fmt.get('url') and fmt.get('vcodec', 'none') != 'none':
                        direct_link = fmt['url']
                        break

            # Último fallback: buscar en formats[]
            if not direct_link and info.get('formats'):
                formatos_mp4 = [
                    f for f in info['formats']
                    if f.get('url') and f.get('ext') == 'mp4'
                       and f.get('vcodec', 'none') != 'none'
                ]
                if formatos_mp4:
                    mejor = max(formatos_mp4, key=lambda f: f.get('tbr') or 0)
                    direct_link = mejor['url']
                    content_type = mejor.get('mimetype', 'video/mp4')

        if not direct_link:
            return f"No se pudo extraer el link del video ({plataforma})", 500

        # ── Headers para el CDN según plataforma ─────────────────────────────
        if plataforma == 'youtube':
            cdn_headers = {
                'User-Agent': 'com.google.android.youtube/19.09.37 (Linux; U; Android 11) gzip',
                'Accept': '*/*',
                'Accept-Encoding': 'identity',
                'Connection': 'keep-alive',
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
                'Accept-Language': 'en-US,en;q=0.9',
                'Connection': 'keep-alive',
                'Range': 'bytes=0-',
                'Sec-Fetch-Dest': 'video',
                'Sec-Fetch-Mode': 'no-cors',
                'Sec-Fetch-Site': 'cross-site',
            }

        session = requests.Session()
        r = session.get(
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
            if b'<html' in preview.lower() or b'error' in preview.lower():
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

        return Response(generate(), status=200, content_type=content_type, headers=resp_headers)

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
