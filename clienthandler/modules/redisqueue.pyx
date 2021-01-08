cdef class Redisqueue:
    cdef private String name, key, namespace
    cdef private redis.Connection __db
    cpdef init(self)
    cpdef String get(self)
    cpdef delete_queue_from_redis(self)