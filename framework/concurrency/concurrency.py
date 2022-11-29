import asyncio


class DeferredTasks:
    def __init__(self, *args):
        self._tasks = args or []

    def add_task(self, coroutine):
        self._tasks.append(coroutine)
        return self

    def add_tasks(self, *args):
        self._tasks.extend(args)
        return self

    async def run(self):
        if any(self._tasks):
            return await asyncio.gather(*self._tasks)


class TaskCollection:
    def __init__(self, *args):
        self._tasks = args or []

    def add_task(self, coroutine):
        self._tasks.append(coroutine)
        return self

    def add_tasks(self, *args):
        self._tasks.extend(args)
        return self

    async def run(self):
        if any(self._tasks):
            return await asyncio.gather(*self._tasks)
