from typing import Any, List

import pymongo
from framework.configuration.configuration import Configuration
from motor.core import AgnosticClient, AgnosticCollection, AgnosticDatabase
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.results import DeleteResult, InsertOneResult, UpdateResult


class MongoRepository:
    def initialize(self, container, database: str, collection: str) -> None:
        configuration = container.resolve(Configuration)
        connection_string = configuration.mongo.get('connection_string')

        self.client = pymongo.MongoClient(connection_string)
        self.database = self.client.get_database(database)
        self.collection = self.database.get_collection(collection)

    def insert(self, document) -> InsertOneResult:
        result = self.collection.insert_one(document)
        return result

    def update(self, selector: dict, values: dict) -> UpdateResult:
        result = self.collection.update_one(
            filter=selector,
            update={'$set': values})
        return result

    def replace(self, selector, document) -> UpdateResult:
        result = self.collection.replace_one(
            filter=selector,
            replacement=document)
        return result

    def delete(self, selector: dict) -> DeleteResult:
        result = self.collection.delete_one(
            filter=selector)
        return result

    def get(self, selector: dict) -> Any:
        result = self.collection.find_one(
            filter=selector)
        return result

    def get_all(self) -> List[Any]:
        result = self.collection.find({})
        return list(result)

    def query(self, filter):
        return list(self.collection.find(filter))


class MongoRepositoryAsync:
    def initialize(self, container, database: str, collection: str, selector: dict = None) -> None:
        configuration = container.resolve(Configuration)
        connection_string = configuration.mongo.get('connection_string')
        self.selector = selector

        self.client: AgnosticClient = AsyncIOMotorClient(
            connection_string)
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
