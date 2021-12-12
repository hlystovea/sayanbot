import asyncio
from os import environ
from typing import Dict, List, Optional

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic.tools import parse_obj_as

from schema.resort import Resort

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
        return self.client.sayanbot.ski_resort

    async def find_one_resort(self, kwargs: Dict = None) -> Optional[Resort]:
        document = await self.resort_collection().find_one(kwargs or {})
        if not document:
            return None
        return Resort(**document)

    async def find_many_resorts(self, kwargs: Dict = None, length: int = None) -> List[Resort]: # noqa
        cursor = self.resort_collection().find(kwargs or {})
        documents = await cursor.to_list(length=length)
        return parse_obj_as(List[Resort], documents)


async def main():
    mongo = await MongoDB.create()
    print(await mongo.get_all_resorts())

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
