import asyncio
from os import environ
from typing import Dict, List, Optional

from bson import ObjectId

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic.tools import parse_obj_as

from schema.resort import Resort
from schema.track import Track

load_dotenv()


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
            print(f'Started server MongoDB ({info.get("version")} version)')
        except Exception:
            print('Unable to connect to the server.')
        return mongo

    def resort_collection(self):
        return self.client.sayanbot.resorts

    def tracks_collection(self):
        return self.client.sayanbot.tracks

    async def find_one_resort(self, kwargs: Dict = None) -> Optional[Resort]:
        document = await self.resort_collection().find_one(kwargs or {})
        if not document:
            return None
        return Resort(**document)

    async def find_many_resorts(self, kwargs: Dict = None, length: int = None) -> List[Resort]: # noqa (E501)
        cursor = self.resort_collection().find(kwargs or {})
        documents = await cursor.to_list(length=length)
        return parse_obj_as(List[Resort], documents)

    async def insert_track(self, track: Track) -> ObjectId:
        document = track.dict()
        result = await self.tracks_collection().insert_one(document)
        return result.inserted_id

    async def find_one_track(self, kwargs: Dict = None) -> Optional[Track]:
        document = await self.tracks_collection().find_one(kwargs or {})
        if not document:
            return None
        return Track(**document)

    async def update_track_by_unique_id(self, unique_id: str, kwargs: Dict = {}) -> int: # noqa (E501)
        result = await self.tracks_collection().update_one(
            {'unique_id': unique_id},
            {'$set': kwargs}
        )
        return result.modified_count

    async def delete_track_by_unique_id(self, unique_id: str) -> int:
        result = await self.tracks_collection().delete_one(
            {'unique_id': unique_id}
        )
        return result.deleted_count

    async def find_many_tracks(self, kwargs: Dict = None, length: int = None) -> List[Track]: # noqa (E501)
        cursor = self.tracks_collection().find(kwargs or {})
        documents = await cursor.to_list(length=length)
        return parse_obj_as(List[Track], documents)


async def main():
    mongo = await MongoDB.create()
    print(await mongo.get_all_resorts())

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
