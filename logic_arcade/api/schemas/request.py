from pydantic import BaseModel


class SubmitRequest(BaseModel):
    image_url: str
    prompt: str
