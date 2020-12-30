python3 redis_cleaner.py &
redis-server /etc/redis/redis.conf &
sleep 2
redis-cli CONFIG SET protected-mode no
wait
