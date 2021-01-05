import logging
import asyncio_redis as redis

# prevent module from logging multiple times per message
logging.getLogger("asyncio_redis").setLevel(logging.WARNING)


class RedisQueue(object):
    """Simple Queue with Redis Backend"""

    # initialize object
    def __init__(self, name, namespace='queues', **redis_kwargs):
        self.redis_kwargs = redis_kwargs
        self.key = '%s:%s' % (namespace, name)

    # initialize connection seperately because of inability to use asyncio in the initializer
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
