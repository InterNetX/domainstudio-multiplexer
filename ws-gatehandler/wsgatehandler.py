"""establishes the multiplexed connection to the websocket-gate
   and returns messages to the redis queues"""
import asyncio
import json
import os
import time
import unicodedata
import logging
from tornado.escape import json_decode, json_encode
import websockets
from nicelog import setup_logging
import requests
import redisqueue


def get_authorization_token():
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


async def connect_to_gate(auth_cookie_header: dict):
    """establishes the multiplexed connection to the websocket-gate"""
    url = str("wss://" +((os.getenv('WS_GATE_URL').strip("wss://")).strip("ws://")))
    logging.info(url)
    extra_headers = {"X-Domainrobot-Context": os.getenv("CONTEXT")}
    extra_headers.update(auth_cookie_header)
    print(extra_headers)
    websocket = await asyncio.wait_for(websockets.connect(url, extra_headers=extra_headers), 2)
    auto_ws = websocket
    await asyncio.wait_for(websocket.send("CONNECT\naccept-version:1.0,1.1,2.0\n\n\0"), 1)
    response = await asyncio.wait_for(websocket.recv(), 1)
    print(response)
    await websocket.send("SUBSCRIBE\nid:0\ndestination:/\nack:auto\n\n\0")
    return auto_ws


# iterate through messages and write them to their ctid redis queues


async def main(auth_cookie_header: dict):
    """main loop of the gate connector"""
    logging.info("Trying to establish the Connection to the WS-Gate!")
    auto_ws = await connect_to_gate(auth_cookie_header)
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
            _auth_cookie_header = get_authorization_token()
            LOOP = asyncio.get_event_loop()
            LOOP.run_until_complete(main(_auth_cookie_header))
        except websockets.WebSocketException as e:
            error_count += 1
            logging.debug("WS-GATE-Connection Crashed! Restarting it!")
            if error_count % 5 == 0:
                error_count = 0
                logging.info("Waiting 10s before trying again.")
                time.sleep(10)
            pass
        except Exception as exception:
            raise exception
