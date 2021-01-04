import logging
import subprocess
import os
import time

def main():
    time.sleep(120)
    connections_since_last_clean = False
    while True:
        redis_connections_open = int(subprocess.check_output("netstat -anp | grep :6379 | grep ESTABLISHED | wc -l", shell=True))
        logging.debug("CONNECTIONS: "+ str(redis_connections_open))
        if redis_connections_open == 0 and connections_since_last_clean:
            logging.info("No client connected. Cleaning All Redis Message Queues!")
            os.system("redis-cli flushall")
            time.sleep(600)
        elif redis_connections_open > 0 and not connections_since_last_clean:
            logging.debug("Currently there are {} clients connected to the Redis Message pool. Waiting for no traffic before flushing Redis!".format(redis_connections_open))
            connections_since_last_clean = True
            time.sleep(1)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()