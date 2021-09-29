import asyncio
import logging

import asyncio_redis as redis

# prevent module from logging multiple times per message
logging.getLogger("asyncio_redis").setLevel(logging.WARNING)


class RedisQueue:
    """Simple Queue with Redis Backend"""

    # initialize object
    def __init__(self, name: str):
        """:param name: name of the queue (has to be ctid)"""
        self.key = '%s:%s' % ("queues", name)
        self.__db = None

    # initialize connection separately because of inability to use asyncio in the initializer
    async def init(self):
        """Establish redis connection."""
        self.__db = await redis.Connection.create(host='redis', port=6379)

    # put element at the tail of the list (for queuing functionality)
    async def put(self, item):
        """Put item into the queue."""
        await self.__db.rpush(self.key, [item])

    # on object delete close connection
    def __del__(self):
        self.__db.close()

    async def get(self):
        """Remove and return an item from the queue.
        If optional args block is true and timeout is None (the default), block
        if necessary until an item is available."""
        item = await self.__db.lpop(self.key)
        if str(item) == "None":
            raise asyncio.TimeoutError
        return item

    async def delete_queue_from_redis(self):
        """used at the termination of a client connection to delete that clients queue on redis """
        await self.__db.delete([self.key])
        self.__db.close()
