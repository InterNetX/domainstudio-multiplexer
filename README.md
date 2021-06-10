<p align="center">
  <a href="" rel="noopener">
 <img width=200px height=200px src="https://login.autodns.com/resources/img/autodns_new_logo_4c.svg" alt="Project logo"></a>
</p>

<h3 align="center">domainstudio-multiplexer BETA</h3>

<div align="center">

[![Status](https://img.shields.io/badge/status-active-success.svg)](https://github.com/InterNetX/domainstudio-multiplexer/graphs/contributors)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](/LICENSE)

</div>

---

<p align="center"> A Multiplexing-Proxy used for async DomainStudio-Operations. It communicates over a single WebSocket with the DomainStudio and uses each frontend/client connection to redistribute the results so that each client only receives messages that were caused by one of its own requests. The client can send unauthorized messages in JSON parsable format as ws-message to the proxy which will send them to the normal AutoDNS JSON API (authorized via the ProxyUser). These results are then fetched from the WS-Gate and transmitted to the client.
    <br> 
</p>

## 📝 Table of Contents

- [About](#about)
- [Getting Started](#getting_started)
- [Deployment](#deployment)
- [Usage](#usage)
- [Built Using](#built_using)
- [Authors](#authors)
- [Acknowledgments](#acknowledgement)

## 🧐 About <a name = "about"></a>
![Structure](https://github.com/InterNetX/domainstudio-multiplexer/blob/main/images/structure.jpg)

This Proxy can be used to authorize DomainStudio requests without sharing any credentials with the client. 

## 🏁 Getting Started <a name = "getting_started"></a>

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See [deployment](#deployment) for notes on how to deploy the project on a live system.

### Prerequisites

You'll need working Docker and Docker-compose.

```
(To modify: Each container directory has its own requirements.txt file. Use Python3.9 and the requirements)
```

## 🎈 Usage <a name="usage"></a>

Create a .env file based on the example in the projects root directory after that,
just use docker-compose:
```
docker-compose up --env <enf-file>
```

### Usage of the Proxy as Client 

The client can connect to the Proxies: ws://hostanme:port/dsws and will get its own message queue.
Afterwards, the client can send a JSON parsable domainstudio-request as specified in:
https://help.internetx.com/display/APIADDITIONALDE/DomainStudio+Guide
For each request, the Client will be forwarded the direct REST response and will get the WebSocket-gates messages back.
For example passing
```
{
  "currency": "USD",
  "searchToken": "house",
  "sources": {
    "recommended": {
      "services": ["WHOIS"],
      ...
    },
    ...
  }
}
```
as a WebSocket message to the proxy will result in something like this coming back:
```
{
  "stid": "20190702-stid",
  "ctid": "myRequestID",
  "data": [
    {
      "domain": "house.com",
      "source": "RECOMMENDED",
      "services": {
        "whois": ...
      }
    },
    ...
  ]
}
```

### Installing for Development and Testing

Git clone and pip install all requirements.
A Redis installation is necessary to test modifications, you can accomplish this by running just the Redis docker image.

```
cd Redis
docker build -t redis .
docker run -p 6379:6379 redis
```
Alternatively, just clone the project and run:

```
docker-compose up --build --force-recreate 
```
To rebuild all containers after you changed something.

## 🚀 Deployment <a name = "deployment"></a>

- [Usage](#usage)

## ⛏️ Built Using <a name = "built_using"></a>

- [Docker](https://www.docker.com) - Container Solution
- [Redis](https://redis.io/) - Message Broker

## ✍️ Authors <a name = "authors"></a>

- [@theemperor66](https://github.com/theemperor66)

See also the list of [contributors](https://github.com/InterNetX/domainstudio-multiplexer/contributors) who participated in this project.

## 🎉 Acknowledgements <a name = "acknowledgement"></a>

original redis-docker file: [redis](https://github.com/dockerfile/redis/blob/master/Dockerfile)

original redisqueue implementation: [redisqueue](http://peter-hoffmann.com/2012/python-simple-queue-redis-queue.html)
