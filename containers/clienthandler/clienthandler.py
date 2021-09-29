import asyncio
import logging
import os
from abc import ABC
from json import JSONDecodeError

import asyncio_redis
import httpx
import redisqueue
import tornado.ioloop
import tornado.web
import tornado.websocket
from nicelog import setup_logging
from tornado.escape import json_decode


async def domainstudio_request(ctid, message=None):
    """request the client-request with the proxies authorization while adding ctid for later"""
    url = os.getenv('RESTURL')
    req = message
    headers = {
        "X-Domainrobot-WS": "ASYNC",
        "User-Agent": "websocket-multiplexer",
        "X-Domainrobot-Context": os.getenv('CONTEXT')
    }
    try:
        async with httpx.AsyncClient(auth=(os.getenv('USER'), os.getenv('PASSWORD'))) as client:
            res = await client.post(url=url + "/domainstudio?ctid=" + ctid, json=req, headers=headers, timeout=5)
            logging.info(
                "Sending REST request to {} in the name of Client: {} .".format(url, ctid))
    except Exception as e:
        logging.error(
            "Error ({}) while sending REST request to {} in the name of Client: {}".format(e, url, ctid))
        return {"AutoDNS-API": "Error"}
    return res.json()


class AutoDNSWebsocketClientHandler(tornado.websocket.WebSocketHandler, ABC):
    """WebsocketHandler for Clients
    one object of this class per client listening for the queue that is created with the ctid of the client"""

    async def listen_routine(self):
        while True:
            try:
                response = await asyncio.wait_for(self.redisqueue.get(), 1)
                response = str(response)
                logging.debug("FOUND MESSAGE in Queue: {}".format(response))
                await self.write_message(response)
            except asyncio.TimeoutError:
                pass
            except asyncio_redis.exceptions.NotConnectedError:
                break
            except tornado.websocket.WebSocketClosedError:
                break

    # on connection generate unique ctid and redis-message-queue with it (the ctid) as name
    # allows the socket handler to sort messages into the addressees queue
    async def open(self):
        remote_ip = self.request.headers.get("X-Real-IP") or \
                    self.request.headers.get("X-Forwarded-For") or \
                    self.request.remote_ip
        self.ctid = str(hash(str(self))) + "_" + str(remote_ip)
        self.redisqueue = redisqueue.RedisQueue(self.ctid)
        await self.redisqueue.init()
        tornado.ioloop.IOLoop.current().spawn_callback(self.listen_routine)

    def check_origin(self, origin):
        return True

    # if message is received, decode it from json and pass it authorized to the Json API
    async def on_message(self, message):
        try:
            logging.debug("RECEIVED {} from Client: {}!".format(message, self.ctid))
            message = json_decode(message)
        except JSONDecodeError:
            await self.write_message({"type": "MultiplexerParsingError"})
            return
        rs = await domainstudio_request(self.ctid, message=message)
        await self.write_message(str(rs))

    # on close delete queue and disconnect from redis before closing the socket successfully
    def on_close(self):
        logging.info(
            "Client-Websocket:{} deleting redis-messagequeue!".format(self.ctid))
        asyncio.ensure_future(self.redisqueue.delete_queue_from_redis())
        logging.info("Client-WebSocket:{} closed!".format(self.ctid))


def make_app():
    return tornado.web.Application([
        (r"/dsws", AutoDNSWebsocketClientHandler),
    ])


if __name__ == "__main__":
    setup_logging()
    port = int(os.getenv('PROXYPORT'))
    processes = int(os.getenv('PROXY_PROCESS_COUNT'))
    logging.info(
        "Starting Proxy on {} with {} processes!".format(port, processes))
    app = make_app()
    clienthandler = tornado.httpserver.HTTPServer(app)
    clienthandler.bind(port)
    clienthandler.start(processes)
    tornado.ioloop.IOLoop.current().start()
