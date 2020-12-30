import logging
import subprocess
import os
import time

def main():
    #time.sleep(120)
    while True:
        redis_connections_open = int(subprocess.check_output("./netcommand.sh", shell=True))
        logging.info("CONNECTIONS: "+ str(redis_connections_open))
        if redis_connections_open == 0:
            logging.info("No client connected. Cleaning All Redis Message Queues!")
            os.system("redis-cli flushall")
            time.sleep(600)
        else:
            logging.debug("Currently there are {} clients connected to the Redis Message pool. Waiting for no traffic before flushing Redis!".format(redis_connections_open))
            time.sleep(1)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()