import base64
import json
import urllib.request
import uuid
from .base import AIImageResult

class RemoteAIProvider:
    name = "remote"
    def __init__(self, endpoint: str, token: str = "", timeout: int = 60):
        self.endpoint=endpoint; self.token=token; self.timeout=timeout
    def generate(self, *, image_bytes: bytes, filename: str, mime_type: str, prompt: str, style: str, intensity: int) -> AIImageResult:
        boundary=f"----AvatarForge{uuid.uuid4().hex}"
        parts=[]
        def field(name,val):
            parts.extend([f"--{boundary}\r\n".encode(),f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),str(val).encode(),b"\r\n"])
        field("prompt",prompt); field("style",style); field("intensity",intensity)
        parts.extend([f"--{boundary}\r\n".encode(),f'Content-Disposition: form-data; name="image"; filename="{filename}"\r\n'.encode(),f"Content-Type: {mime_type}\r\n\r\n".encode(),image_bytes,b"\r\n",f"--{boundary}--\r\n".encode()])
        req=urllib.request.Request(self.endpoint,data=b"".join(parts),method="POST",headers={"Content-Type":f"multipart/form-data; boundary={boundary}","Accept":"application/json"})
        if self.token: req.add_header("Authorization",f"Bearer {self.token}")
        with urllib.request.urlopen(req,timeout=self.timeout) as resp:
            payload=json.loads(resp.read().decode("utf-8"))
        encoded=payload.get("image_base64") or payload.get("data",{}).get("image_base64")
        if not encoded: raise ValueError("AI provider response did not include image_base64.")
        return AIImageResult(base64.b64decode(encoded),payload.get("mime_type","image/png"),self.name)
