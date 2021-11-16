"""establishes the multiplexed connection to the websocket-gate
   and returns messages to the redis queues"""
from random import randint

import asyncio
import json
import logging
import os
import time
import unicodedata
from json import JSONDecodeError

import redisqueue
import requests
import websockets
import websockets.client
from nicelog import setup_logging
from tornado.escape import json_decode, json_encode


class WsGateHandler:
    def __init__(self) -> None:
        """objects of this class can connect to the ws-gate and sort messages by their ctid"""
        self._auth_cookie_header = self.get_authorization_token()

    @staticmethod
    def get_authorization_token() -> dict:
        """to authorize the UPGRADE and SUBSCRIBE this returns the cookie necessary to send these requests"""
        url = "https://api.autodns.com/v1/login?acl=true&profile=true&customer=true&timeout=60"

        payload = json.dumps({
            "context": os.getenv("CONTEXT"),
            "user": os.getenv("USER"),
            "password": os.getenv("PASSWORD")
        })
        headers = {
            'User-Agent': 'websocket-multiplexer',
        }
        auth_response = requests.request("POST", url, headers=headers, data=payload, timeout=100000)
        auth_header = auth_response.headers.get("Set-Cookie")
        # adding headers because session_id requires matching user-agent
        return_header = {"Cookie": auth_header}
        return_header.update(headers)
        return return_header

    async def connect_to_gate(self) -> websockets.client.WebSocketClientProtocol:
        """establishes the multiplexed connection to the websocket-gate"""
        url = os.getenv("WS_GATE_URL")
        logging.info(url)
        extra_headers = {"X-Domainrobot-Context": os.getenv("CONTEXT")}
        extra_headers.update(self._auth_cookie_header)
        websocket = await asyncio.wait_for(websockets.connect(url, extra_headers=extra_headers, ping_interval=0), 2)
        await websocket.send("CONNECT\nheart-beat:0,10000\naccept-version:1.0,1.1,2.0\n\n\0")
        logging.info(await websocket.recv())
        await websocket.send(
            "SUBSCRIBE\nid:{randint}\ndestination:/\nack:auto\n\n\0".format(randint=randint(0, 1000000000)))
        return websocket

    # iterate through messages and write them to their ctid redis queues
    async def main(self) -> None:
        """main loop of the gate connector"""
        logging.info("Trying to establish the Connection to the WS-Gate!")
        ws = await self.connect_to_gate()
        logging.info("Ws-Gate-Connection established starting Message-Listening!")
        response = ""
        while True:
            try:
                response = await ws.recv()
                response = response.split("\n\n")[-1]
                response = ''.join(
                    c for c in response if unicodedata.category(c) != 'Cc')
                try:
                    rsp = json_decode(response)
                    ctid = rsp.get("ctid")
                except JSONDecodeError:
                    continue
                except TypeError:
                    continue
                if ctid:
                    redis = redisqueue.RedisQueue(ctid)
                    await redis.init()
                    await redis.put(json_encode(rsp))
                else:
                    continue
            except asyncio.TimeoutError:
                pass
            except KeyError:
                pass
            except ValueError:
                pass
            except websockets.WebSocketException as e:
                logging.warning(response)
                raise e


if __name__ == "__main__":
    """start message handling loop and restart if it fails"""
    setup_logging()
    error_count = 0
    ws_handler = WsGateHandler()
    LOOP = asyncio.get_event_loop()
    LOOP.run_until_complete(ws_handler.main())
    while True:
        try:
            ws_handler = WsGateHandler()
            LOOP = asyncio.get_event_loop()
            LOOP.run_until_complete(ws_handler.main())
        except websockets.WebSocketException as e:
            error_count += 1
            logging.exception("WS-GATE-Connection Crashed! Restarting it!")
            logging.exception(e)
            # not likely to solve any problems by DOS attacking the gate which is why this sleeps every 5 attempts
            if error_count % 5 == 0:
                error_count = 0
                logging.info("Waiting 10s before trying again.")
                time.sleep(10)
            pass
        except Exception as exception:
            logging.exception("ERROR: {e}".format(e=exception))
            logging.exception("{e_traceback}".format(e_traceback=exception.with_traceback()))
