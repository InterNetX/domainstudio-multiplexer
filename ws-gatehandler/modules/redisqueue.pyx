cdef class Redisqueue:
    cdef private String name, key, namespace
    cdef private redis.Connection __db
    cpdef init(self)
    cpdef put(self, String item)