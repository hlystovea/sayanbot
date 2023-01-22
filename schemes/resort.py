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
    coordinates: tuple[float, float]
    weather: bool
    phone: str | None
    url: AnyHttpUrl | None
    webcam: AnyHttpUrl | None
    trail_map: str | None
    info: ResortInfo | None

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
