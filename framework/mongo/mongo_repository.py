from typing import Any, List
from motor.core import AgnosticCollection, AgnosticDatabase
from pymongo.results import DeleteResult, InsertOneResult, UpdateResult


class MongoRepositoryAsync:
    def __init__(
        self,
        client,
        database: str,
        collection: str,
    ) -> None:
        self.client = client
        self.database: AgnosticDatabase = self.client.get_database(
            database)
        self.collection: AgnosticCollection = self.database.get_collection(
            collection)

    async def insert(self, document) -> InsertOneResult:
        result = await self.collection.insert_one(document)
        return result

    async def update(self, selector: dict, values: dict) -> UpdateResult:
        result = await self.collection.update_one(
            filter=selector,
            update={'$set': values})
        return result

    async def replace(self, selector, document) -> UpdateResult:
        result = await self.collection.replace_one(
            filter=selector,
            replacement=document)
        return result

    async def delete(self, selector: dict) -> DeleteResult:
        result = await self.collection.delete_one(
            filter=selector)
        return result

    async def get(self, selector: dict) -> Any:
        result = await self.collection.find_one(
            filter=selector)
        return result

    async def get_all(self) -> List[Any]:
        result = self.collection.find({})

        docs = []
        async for doc in result:
            docs.append(doc)
        return docs

    async def query(self, filter):
        return list(await self.collection.find(filter))
