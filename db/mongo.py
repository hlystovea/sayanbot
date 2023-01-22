from os import environ
from typing import Dict, List, Optional

from bson import ObjectId

from motor.motor_asyncio import AsyncIOMotorClient
from pydantic.tools import parse_obj_as

from logger import logger
from schemes.resort import Resort
from schemes.track import Track


class MongoDB:
    def __init__(self):
        self.client = AsyncIOMotorClient(
            environ['MONGO_URL'],
            serverSelectionTimeoutMS=5000,
        )

    @classmethod
    async def create(cls) -> 'MongoDB':
        mongo = cls()

        try:
            info = await mongo.client.server_info()
            logger.info(
                f'Started server MongoDB ({info.get("version")} version)')
        except Exception as error:
            logger.error('Unable to connect to the server')
            raise error

        return mongo

    def resort_collection(self):
        return self.client.sayanbot.resorts

    def tracks_collection(self):
        return self.client.sayanbot.tracks

    async def find_one_resort(self, kwargs: Dict | None = None) -> Optional[Resort]:  # noqa (E501)
        document = await self.resort_collection().find_one(kwargs or {})

        if not document:
            return None

        return Resort(**document)

    async def find_many_resorts(
        self, kwargs: Dict | None = None, length: int | None = None
    ) -> List[Resort]:
        cursor = self.resort_collection().find(kwargs or {})
        documents = await cursor.to_list(length=length)
        return parse_obj_as(List[Resort], documents)

    async def insert_track(self, track: Track) -> ObjectId:
        document = track.dict()
        result = await self.tracks_collection().insert_one(document)
        return result.inserted_id

    async def find_one_track(self, kwargs: Dict | None = None) -> Optional[Track]:  # noqa (E501)
        document = await self.tracks_collection().find_one(kwargs or {})

        if not document:
            return None

        return Track(**document)

    async def update_track_by_unique_id(
        self, unique_id: str, kwargs: Dict | None = None) -> int: # noqa (E501)
        result = await self.tracks_collection().update_one(
            {'unique_id': unique_id},
            {'$set': kwargs or {}}
        )
        return result.modified_count

    async def delete_track_by_unique_id(self, unique_id: str) -> int:
        result = await self.tracks_collection().delete_one(
            {'unique_id': unique_id}
        )
        return result.deleted_count

    async def find_many_tracks(self, kwargs: Dict | None = None, length: int | None = None) -> List[Track]: # noqa (E501)
        cursor = self.tracks_collection().find(kwargs or {})
        documents = await cursor.to_list(length=length)
        return parse_obj_as(List[Track], documents)


mongo = MongoDB()
