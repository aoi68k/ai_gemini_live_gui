import json
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import uuid
import wave
import io
import asyncio
from core import config

class ApiHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        if parsed_path.path == '/speakers':
            self.handle_speakers()
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed_path = urllib.parse.urlparse(self.path)
        if parsed_path.path == '/audio_query':
            self.handle_audio_query(parsed_path)
        elif parsed_path.path == '/synthesis':
            self.handle_synthesis(parsed_path)
        else:
            self.send_response(404)
            self.end_headers()

    def get_speakers_data(self):
        chars = config.load_characters()
        speakers = []
        for idx, (char_key, char_data) in enumerate(chars.items()):
            speaker = {
                "supported_features": {
                    "permitted_synthesis_morphing": "ALL"
                },
                "name": char_data.get("name", char_key),
                "speaker_uuid": str(uuid.uuid5(uuid.NAMESPACE_OID, char_key)),
                "styles": [
                    {
                        "name": "ノーマル",
                        "id": idx
                    }
                ],
                "version": "1.0"
            }
            speakers.append(speaker)
        return speakers, chars

    def handle_speakers(self):
        speakers, _ = self.get_speakers_data()
        body = json.dumps(speakers, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)


    def handle_audio_query(self, parsed_path):
        query = urllib.parse.parse_qs(parsed_path.query)
        text = query.get('text', [''])[0]
        
        if hasattr(self.server, 'on_log') and self.server.on_log:
            self.server.on_log(f"API AudioQuery: {text}")
        
        # ダミーのaudio_queryを返す。Gemini APIでは細かい調整は不要なため、最低限のフォーマットにテキストを埋め込む
        dummy_query = {
            "accent_phrases": [],
            "speedScale": 1.0,
            "pitchScale": 0.0,
            "intonationScale": 1.0,
            "volumeScale": 1.0,
            "prePhonemeLength": 0.1,
            "postPhonemeLength": 0.1,
            "outputSamplingRate": 24000,
            "outputStereo": False,
            "kana": text, # textをそのまま保存しておく
        }
        
        body = json.dumps(dummy_query, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def handle_synthesis(self, parsed_path):
        query = urllib.parse.parse_qs(parsed_path.query)
        speaker_id = int(query.get('speaker', ['0'])[0])
        
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        query_data = json.loads(post_data.decode('utf-8'))
        
        text = query_data.get("kana", "")
        
        _, chars = self.get_speakers_data()
        char_keys = list(chars.keys())
        if speaker_id >= len(char_keys):
            speaker_id = 0
            
        char_key = char_keys[speaker_id]
        char_data = chars[char_key]
        
        if hasattr(self.server, 'on_log') and self.server.on_log:
            self.server.on_log(f"API Synthesis Request: {char_data.get('name', 'Unknown')} - {text}")
            
        try:
            # タイムアウト回避のため、生成完了を待たずにHTTPヘッダーを先に返してストリーミング開始
            self.send_response(200)
            self.send_header('Content-Type', 'audio/wav')
            self.end_headers()
            
            # ストリーミング用にダミーのWAVヘッダー（サイズ未定: 0xFFFFFFFF）を送信
            self._write_dummy_wav_header(self.wfile)
            
            # Geminiから受信したオーディオチャンクを即座にwfileに書き込む
            self.generate_audio_with_gemini_streaming(text, char_data, self.wfile)
            
            if hasattr(self.server, 'on_log') and self.server.on_log:
                self.server.on_log(f"API Synthesis Success")
        except Exception as e:
            print(f"API Error: {e}")
            if hasattr(self.server, 'on_log') and self.server.on_log:
                self.server.on_log(f"API Synthesis Error: {e}")

    def _write_dummy_wav_header(self, wfile, channels=1, sampwidth=2, framerate=24000):
        """全体のファイルサイズが未確定の状態でストリーミングするためのダミーWAVヘッダー"""
        wfile.write(b'RIFF')
        wfile.write(b'\xff\xff\xff\xff') # ChunkSize (Unknown)
        wfile.write(b'WAVEfmt ')
        wfile.write((16).to_bytes(4, 'little')) # Subchunk1Size
        wfile.write((1).to_bytes(2, 'little')) # AudioFormat (PCM)
        wfile.write((channels).to_bytes(2, 'little'))
        wfile.write((framerate).to_bytes(4, 'little'))
        wfile.write((framerate * channels * sampwidth).to_bytes(4, 'little')) # ByteRate
        wfile.write((channels * sampwidth).to_bytes(2, 'little')) # BlockAlign
        wfile.write((sampwidth * 8).to_bytes(2, 'little')) # BitsPerSample
        wfile.write(b'data')
        wfile.write(b'\xff\xff\xff\xff') # Subchunk2Size (Unknown)
        wfile.flush()

    def generate_audio_with_gemini_streaming(self, text, char_data, wfile):
        from google import genai
        from google.genai import types
        
        api_key = config.get_api_key()
        client = genai.Client(api_key=api_key)
        
        system_instruction = char_data.get("system_instruction", "")
        voice_name = char_data.get("voice_name", "Aoede")
        
        async def _do_live_connect():
            connect_config = types.LiveConnectConfig(
                response_modalities=["AUDIO"],
                system_instruction=types.Content(parts=[types.Part.from_text(text=system_instruction)]),
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=voice_name
                        )
                    )
                )
            )
            async with client.aio.live.connect(model="gemini-3.1-flash-live-preview", config=connect_config) as session:
                await session.send(input=text, end_of_turn=True)
                
                import asyncio
                receive_iter = session.receive().__aiter__()
                while True:
                    try:
                        # 定期的にチャンクが返ってくるので、タイムアウトは15秒で問題なし
                        response = await asyncio.wait_for(receive_iter.__anext__(), timeout=15.0)
                        server_content = response.server_content
                        if server_content is not None:
                            model_turn = server_content.model_turn
                            if model_turn is not None:
                                for part in model_turn.parts:
                                    if part.inline_data:
                                        wfile.write(part.inline_data.data)
                                        wfile.flush()
                            if server_content.turn_complete:
                                break
                    except asyncio.TimeoutError:
                        break
                    except StopAsyncIteration:
                        break
                    except Exception as e:
                        print(f"API receive error: {e}")
                        break
                        
                if hasattr(session, 'close'):
                    try:
                        await session.close()
                    except Exception:
                        pass
                        
        import asyncio
        asyncio.run(_do_live_connect())


class ApiServer:
    def __init__(self, port=50021, on_log=None):
        self.port = port
        self.server = None
        self.thread = None
        self.on_log = on_log

    def start(self):
        if self.server:
            return False
        try:
            self.server = HTTPServer(('127.0.0.1', self.port), ApiHandler)
            self.server.on_log = self.on_log
            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()
            return True
        except OSError:
            # Port might be in use
            return False

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server = None
        if self.thread:
            self.thread.join(timeout=1.0)
            self.thread = None

    def is_running(self):
        return self.server is not None
