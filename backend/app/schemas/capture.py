from typing import Literal

from pydantic import BaseModel


class CaptureRequest(BaseModel):
    text: str
    # Whitelisted origins a caller may claim; everything else on TaskOrigin
    # (user/ai/telegram/google) is assigned server-side, never by the client.
    origin: Literal["web", "braindump"] = "web"
