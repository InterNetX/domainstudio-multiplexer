"""establishes the multiplexed connection to the websocket-gate
   and returns messages to the redis queues"""
import asyncio
import os
import time
import unicodedata
import logging
from tornado.escape import json_decode, json_encode
import websockets
from nicelog import setup_logging
import redisqueue


async def connect_to_gate():
    """establishes the multiplexed connection to the websocket-gate"""
    url = str("wss://"+os.getenv('USER')+":"+os.getenv('PASSWORD') +
              "@"+((os.getenv('WS_GATE_URL').strip("wss://")).strip("ws://")))
    logging.info(url)
    websocket = await asyncio.wait_for(websockets.connect(url,
        extra_headers={"X-Domainrobot-Context": 1}), 2)
    auto_ws = websocket
    await asyncio.wait_for(websocket.send("CONNECT\naccept-version:1.0,1.1,2.0\n\n\0"), 1)
    response = await asyncio.wait_for(websocket.recv(), 1)
    print(response)
    await websocket.send("SUBSCRIBE\nid:0\ndestination:/\nack:auto\n\n\0")
    return auto_ws

# iterate through messages and write them to their ctid redis queues


async def main():
    """main loop of the gate connector"""
    logging.info("Trying to establish the Connection to the WS-Gate!")
    auto_ws = await connect_to_gate()
    logging.info("Ws-Gate-Connection established starting Message-Listening!")
    while True:
        try:
            response = await asyncio.wait_for(auto_ws.recv(), 1)
            response = response.split("\n\n")[-1]
            response = ''.join(
                c for c in response if unicodedata.category(c) != 'Cc')
            try:
                rsp = json_decode(response)
                ctid = rsp.get("ctid")
            except:
                continue
            if ctid:
                redis = redisqueue.RedisQueue(ctid)
                await redis.init()
                await redis.put(json_encode(rsp))
                redis = None
            else:
                continue
        except asyncio.TimeoutError:
            pass
        except KeyError:
            pass
        except ValueError:
            pass

if __name__ == "__main__":
    """start message handling loop and restart if it fails"""
    setup_logging()
    error_count = 0
    while True:
        try:
            LOOP = asyncio.get_event_loop()
            LOOP.run_until_complete(main())
        except websockets.WebSocketException:
            error_count += 1
            logging.debug("WS-GATE-Connection Crashed! Restarting it!")
            if error_count % 5 == 0:
                error_count = 0
                logging.info("Waiting 10s before trying again.")
                time.sleep(10)
            pass
        except Exception as exception:
            try:
                logging.error("%s", str(exception) +
                              str(exception.with_traceback()))
            except TypeError:
                logging.error(str(exception))
            logging.warning("WS-GATE-HANDLER Crashed! Restarting it!")
