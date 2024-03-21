import asyncio
from typing import Any


class TaskCollection:
    def __init__(
        self,
        *args
    ):
        self._tasks = args or []

    def add_task(
        self,
        coroutine
    ) -> 'TaskCollection':
        '''
        Adds a coroutine task to the list of tasks.

        `coroutine`: The coroutine task to be added.
        '''

        self._tasks.append(coroutine)
        return self

    def add_tasks(
        self,
        *args
    ) -> 'TaskCollection':
        '''
        Add one or more tasks to the list of tasks.

        `*args`: Tasks to be added.


        '''

        self._tasks.extend(args)
        return self

    async def run(
        self
    ) -> list[Any]:
        '''
        Run the tasks concurrently.

        This method runs the stored tasks list concurrently using
        asyncio.gather.

        Returns a list of results from the completed tasks.
        '''

        if any(self._tasks):
            return await asyncio.gather(*self._tasks)
