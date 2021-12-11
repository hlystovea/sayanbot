import asyncio
from os import environ
from typing import Dict, Optional

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# from ..schema.resort import Resort

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
            print("Unable to connect to the server.")
        return mongo

    def resort_collection(self):
        return self.client.sayanbot.ski_resort

    """async def get_resort_by_slug(self, slug: str) -> Optional[Resort]:
        resort = await self.resort_collection().find_one({'slug': slug})
        if not resort:
            return None
        return Resort(resort)"""

    async def get_all_resorts(self) -> Optional[list[Dict]]:
        cursor = self.resort_collection().find()
        resorts = await cursor.to_list(length=10)
        return resorts


async def main():
    mongo = await MongoDB.create()
    print(await mongo.get_all_resorts())

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
