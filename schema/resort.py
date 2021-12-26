from typing import List, Optional

from pydantic import AnyHttpUrl, BaseModel


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
    coordinates: List[float]
    weather: bool
    phone: Optional[str]
    url: Optional[AnyHttpUrl]
    webcam: Optional[AnyHttpUrl]
    trail_map: Optional[str]
    info: Optional[ResortInfo]

    def get_info(self):
        return (
            f'*{self.name}\n*'
            f'Телефон: {self.phone}\n'
            f'Сайт: {self.url}\n'
            f'Количество трасс: {self.info.trails}\n'
            f'Самая длинная трасса: {self.info.max_length} км\n'
            f'Общая протяженность трасс: {self.info.total_length} км\n'
            f'Перепад высот: {self.info.vertical_drop} м\n'
            f'Максимальная высота: {self.info.max_elevation} м\n'
            f'Количество подъемников: {self.info.lifts}\n'
            f'Тип подъемников: {self.info.type_lift}\n'
        )
