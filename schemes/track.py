from pydantic import BaseModel


class Track(BaseModel):
    file_id: str
    unique_id: str
    name: str
    description: str
    size: int
    region: str
    chat_id: int
