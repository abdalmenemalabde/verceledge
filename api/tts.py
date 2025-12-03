from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import asyncio
import tempfile
import os

import edge_tts


async def synth_to_bytes(text: str, voice: str) -> bytes:
    # Use the voice passed from the handler
    communicate = edge_tts.Communicate(text, voice)

    # Save to a temp file, then read bytes back
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        tmp_path = f.name

    try:
        await communicate.save(tmp_path)
        with open(tmp_path, "rb") as f:
            audio = f.read()
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass

    return audio


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Parse query string
            query = parse_qs(urlparse(self.path).query)

            # Text param (default if missing)
            text = query.get("text", ["Hello from edge-tts on Vercel"])[0]

            # Voice param (default to Arabic voice if missing/empty)
            voice = query.get("voice", ["ar-AE-HamdanNeural"])[0] or "ar-AE-HamdanNeural"

            # Run the async TTS code
            audio = asyncio.run(synth_to_bytes(text, voice))

            self.send_response(200)
            self.send_header("Content-Type", "audio/mpeg")
            self.send_header("Content-Length", str(len(audio)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(audio)

        except Exception as e:
            # Return the error so you can see it in the browser / logs
            err_msg = f"Error in tts function: {type(e).__name__}: {e}"
            self.send_response(500)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(err_msg.encode("utf-8"))
