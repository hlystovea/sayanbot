from typing import Optional, Tuple

from pydantic import AnyHttpUrl, BaseModel
from pydantic.types import FilePath


class ResortInfo(BaseModel):
    trails: int
    max_length: float
    total_length: float
    vertical_drop: int
    max_elevation: int
    lifts: int
    type_lift: str


class Resort(BaseModel):
    name: str
    slug: str
    coordinates: Tuple[int]
    show_weather: bool
    phone: Optional[str]
    url: Optional[AnyHttpUrl]
    webcam: Optional[AnyHttpUrl]
    trail_map: Optional[FilePath]
    info: Optional[ResortInfo]
