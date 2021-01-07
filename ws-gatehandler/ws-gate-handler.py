import asyncio
import os
import unicodedata
import logging
from tornado.escape import json_decode, json_encode
import websockets
from nicelog import setup_logging
import redisqueue

#establish the multiplexed connection to the websocket-gate
async def connect_to_gate():
    url = str("wss://"+os.getenv('USER')+":"+os.getenv('PASSWORD')+"@"+((os.getenv('WS_GATE_URL').strip("wss://")).strip("ws://")))
    logging.info(url)
    websocket = await asyncio.wait_for(websockets.connect(url,extra_headers={"X-Domainrobot-Context":1}), 2)
    auto_ws = websocket
    await asyncio.wait_for(websocket.send("CONNECT\naccept-version:1.0,1.1,2.0\n\n\0"), 1)
    response = await asyncio.wait_for(websocket.recv(), 1)
    print(response)
    await websocket.send("SUBSCRIBE\nid:0\ndestination:/\nack:auto\n\n\0")
    return auto_ws

#iterate through messages and write them to their ctid redis queues
async def main():
    logging.info("Trying to establish the Connection to the WS-Gate!")
    auto_ws = await connect_to_gate()
    logging.info("Ws-Gate-Connection established starting Message-Listening!")
    while True:
        try:
            response = await asyncio.wait_for(auto_ws.recv(), 1)
            response = response.split("\n\n")[-1]
            response = ''.join(
                c for c in response if unicodedata.category(c) != 'Cc')
            rsp = json_decode(response)
            ctid = rsp.get("ctid")
            redis = redisqueue.RedisQueue(ctid)
            await redis.init()
            await redis.put(json_encode(rsp))
            redis = None
        except asyncio.TimeoutError:
            pass
        except KeyError:
            pass
        except ValueError:
            pass

#start message handling loop and restart if it fails       
if __name__ == "__main__":
    setup_logging()
    while True:
        try:
            asyncio.run(main())
        except websockets.WebSocketException:
            logging.debug("WS-GATE-Connection Crashed! Restarting It!")
            pass
        except Exception as e:
            try:
                logging.error(str(e), str(e.with_traceback()))
            except TypeError:
                logging.error(str(e))
            logging.warning("WS-GATE-HANDLER Crashed! Restarting It!")