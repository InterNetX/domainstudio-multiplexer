import asyncio
import logging
import os
from abc import ABC
from json import JSONDecodeError
from typing import Any
from urllib.parse import urlparse

import asyncio_redis
import httpx
import redisqueue
import tornado.ioloop
import tornado.web
import tornado.websocket
from nicelog import setup_logging
from tornado import httputil
from tornado.escape import json_decode


class AutoDNSWebsocketClientHandler(tornado.websocket.WebSocketHandler, ABC):
    """WebsocketHandler for clients
    one object of this class per client listening for the queue that is created with the ctid of the client"""

    def __init__(self, application: tornado.web.Application, request: httputil.HTTPServerRequest,
                 **kwargs: Any) -> None:
        super().__init__(application, request, **kwargs)
        self.ctid = None
        self.redisqueue = None
        try:
            self.allowed_origins = [origin for origin in os.getenv("ALLOWED_ORIGINS").split(";")]
            try:
                self.allowed_origins.remove("")
            except ValueError:
                # if there is no ; at the end of last hostname then there will be no empty string
                pass
            logging.debug("Setting {allowed_origins} as allowed origins".format(allowed_origins=self.allowed_origins))
        except AttributeError:
            # in case allowed_origins env is not set allow every connection
            self.allowed_origins = []
            logging.debug("Disabling the check for allowed origin".format(allowed_origins=self.allowed_origins))

    def check_origin(self, origin: str) -> bool:
        """checks the origin header if allowed_origin is set"""
        if len(self.allowed_origins) == 0:
            return True
        elif urlparse(origin).hostname in self.allowed_origins:
            return True
        else:
            return False

    @staticmethod
    async def domainstudio_request(ctid: str, message: str) -> dict:
        """request the client-request with the proxies authorization while adding ctid for later"""
        url = os.getenv('REST_URL')
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

    async def listen_routine(self) -> None:
        """coroutine to keep polling the special redis queue for the connected client"""
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

    async def open(self) -> None:
        """readying to serve a client once a connection is established over websocket"""
        remote_ip = self.request.headers.get("X-Real-IP") or self.request.headers.get(
            "X-Forwarded-For") or self.request.remote_ip
        # on connection generate unique ctid and a redis-message-queue with it (the ctid) as name
        # allows the socket handler to sort messages into the addressees queue
        self.ctid = str(hash(str(self))) + "_" + str(remote_ip)
        self.redisqueue = redisqueue.RedisQueue(self.ctid)
        await self.redisqueue.init()
        tornado.ioloop.IOLoop.current().spawn_callback(self.listen_routine)

    async def on_message(self, message: str) -> None:
        """if message is received, parse it as json and pass it authorized to the Json API
            :param message: message string from client (checked to be a valid json doc"""
        try:
            logging.debug("RECEIVED {} from Client: {}!".format(message, self.ctid))
            message = json_decode(message)
        except JSONDecodeError as e:
            logging.error("JSONDecodeError {e}".format(e=e))
            await self.write_message({"type": "MultiplexerParsingError"})
            return
        rs = await self.domainstudio_request(self.ctid, message=message)
        await self.write_message(str(rs))

    def on_close(self) -> None:
        """on close delete queue and disconnect from redis before closing the socket successfully"""
        logging.info(
            "Client-Websocket:{} deleting redis-message-queue!".format(self.ctid))
        asyncio.ensure_future(self.redisqueue.delete_queue_from_redis())
        logging.info("Client-WebSocket:{} closed!".format(self.ctid))


def make_app():
    return tornado.web.Application([
        (r"/dsws", AutoDNSWebsocketClientHandler),
    ])


if __name__ == "__main__":
    setup_logging()
    port = int(os.getenv('PROXY_PORT'))
    processes = int(os.getenv('PROXY_PROCESS_COUNT'))
    logging.info(
        "Starting Proxy on {} with {} processes!".format(port, processes))
    app = make_app()
    clienthandler = tornado.httpserver.HTTPServer(app)
    clienthandler.bind(port)
    clienthandler.start(processes)
    tornado.ioloop.IOLoop.current().start()
