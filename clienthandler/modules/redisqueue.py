import logging
import asyncio_redis as redis
import asyncio

logging.getLogger("asyncio_redis").setLevel(logging.WARNING)

class RedisQueue(object):
    """Simple Queue with Redis Backend"""
    def __init__(self, name, namespace='queues', **redis_kwargs):
        """The default connection parameters are: host='localhost', port=6379, db=0"""
        self.redis_kwargs = redis_kwargs
        self.key = '%s:%s' %(namespace, name)
    async def init(self):
        self.__db= await redis.Connection.create(host='redis', port=6379)

    async def get(self):
        """Remove and return an item from the queue. 

        If optional args block is true and timeout is None (the default), block
        if necessary until an item is available."""
        item = await self.__db.lpop(self.key)

        if str(item)=="None":
            raise asyncio.TimeoutError
        return item
    
    async def delete_queue_from_redis(self):
        await self.__db.delete([self.key])
        self.__db.close()
    