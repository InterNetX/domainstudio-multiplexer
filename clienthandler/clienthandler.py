import asyncio
import logging
import asyncio_redis
import tornado.ioloop
import tornado.web
import tornado.websocket
from tornado.escape import json_decode
import httpx
import os
from nicelog import setup_logging

import redisqueue


async def domainstudio_request(ctid, data, message=None):
    url = os.getenv('RESTURL')
    if message:
        req = message
        headers = {
            "X-Domainrobot-WS": "ASYNC",
            "User-Agent": "domainstudio-multiplexer-instance",
            "X-Domainrobot-Context": os.getenv('CONTEXT')
        }
        try:
            async with httpx.AsyncClient(auth=(os.getenv('USER'), os.getenv('PASSWORD'))) as client:
                res = await client.post(url=url+"/domainstudio?ctid="+ctid, json=req, headers=headers, timeout=5)
                logging.info(
                    "Sending REST request to {} in the name of Client: {} .".format(url, ctid))
        except Exception as e:
            logging.error(
                "Error ({}) while sending REST request to {} in the name of Client: {}".format(e, url, ctid))
            return {"AutoDNS-API": "Error"}
        return res.json()
    search_token = data.get("search_token")
    tld = data.get("tld", "")

    req = {
        "currency": "USD",
        "searchToken": search_token,
        "sources": {
            "recommended": {
                "services": ["WHOIS"]
            },
            "initial": {
                "services": ["WHOIS"],
                "tlds": tld,
            }
        }
    }
    headers = {
        "X-Domainrobot-WS": "ASYNC",
        "User-Agent": "domainstudio-multiplexer-instance",
        "X-Domainrobot-Context": os.getenv('CONTEXT')
    }
    try:
        async with httpx.AsyncClient(auth=(os.getenv('USER'), os.getenv('PASSWORD'))) as client:
            res = await client.post(url=url+"/domainstudio?ctid="+ctid, json=req, headers=headers, timeout=5)
            logging.info(
                "Sending REST request to {} in the name of Client: {} .".format(url, ctid))
    except Exception as e:
        logging.error(
            "Error ({}) while sending REST request to {} in the name of Client: {}".format(e, url, ctid))
        return {"AutoDNS-API": "Error"}
    return res.json()


class AutoDnsWebsocket(tornado.websocket.WebSocketHandler):
    async def listen_routine(self):
        while True:
            try:
                response = await asyncio.wait_for(self.redisqueue.get(), 1)
                response = str(response)
                logging.debug("FOUND MESSAGE in Queue: {}".format(response))
                self.write_message(response)
            except asyncio.TimeoutError:
                pass
            except asyncio_redis.exceptions.NotConnectedError:
                break
            except tornado.websocket.WebSocketClosedError:
                break

    async def open(self):
        remote_ip = self.request.headers.get("X-Real-IP") or \
            self.request.headers.get("X-Forwarded-For") or \
            self.request.remote_ip
        self.ctid = str(hash(str(self)))+"_"+str(remote_ip)
        self.redisqueue = redisqueue.RedisQueue(self.ctid)
        await self.redisqueue.init()
        tornado.ioloop.IOLoop.current().spawn_callback(self.listen_routine)

    def check_origin(self, origin):
        return True

    # for use with debug frontend
    async def debug_on_message(self, message):
        logging.debug("Transmitting message {}".format(message))
        message = {"searchtoken": message.split(
            ";")[0], "tlds": message.split(";")[1]}
        search = message.get("searchtoken")
        tlds = message.get("tlds").split(" ")
        rs = await domainstudio_request(self.ctid, {"search_token": search, "tld": tlds})
        try:
            self.write_message(str(rs))
        except tornado.websocket.WebSocketClosedError:
            return

    # if message is received decode it from json and pass it authorized to the Json API
    async def on_message(self, message):
        try:
            logging.debug("RECEIVED {} from Client!".format(message))
            message = json_decode(message)
        except:
            self.write_message({"type": "MultiplexerParsingError"})
            return
        rs = await domainstudio_request(self.ctid, {}, message=message)
        self.write_message(str(rs))

    def on_close(self):
        asyncio.ensure_future(self.redisqueue.delete_queue_from_redis())
        logging.debug("WebSocket closed")


def make_app():
    return tornado.web.Application([
        (r"/dsws", AutoDnsWebsocket),
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
