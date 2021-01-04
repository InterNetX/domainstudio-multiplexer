<p align="center">
  <a href="" rel="noopener">
 <img width=200px height=200px src="https://login.autodns.com/resources/img/autodns_new_logo_4c.svg" alt="Project logo"></a>
</p>

<h3 align="center">domainstudio-multiplexer</h3>

<div align="center">

[![Status](https://img.shields.io/badge/status-active-success.svg)]()
[![GitHub Issues](https://img.shields.io/github/issues/kylelobo/The-Documentation-Compendium.svg)](https://github.com/InterNetX/domainstudio-multiplexer/issues)
[![GitHub Pull Requests](https://img.shields.io/github/issues-pr/kylelobo/The-Documentation-Compendium.svg)](https://github.com/InterNetX/domainstudio-multiplexer/pulls)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](/LICENSE)

</div>

---

<p align="center"> A Multiplexing Proxy used for async DomainStudio-Operations. It communicates over a single Websocket with the DomainStudio and uses each Frontend/Clientconnection to redistribute the Results, so that each client only receives messages that were caused by on of it's requests. The Client can send unauthorized messages in Json parsable format as ws-message to the Proxy which will send them to the normal AutoDNS Json API (authorized via the ProxyUser). These Results are then fetched from the WS-Gate and transmitted to the client.
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

This Proxy can be used to authorize DomainStudio requests without sharing any credentials with the client. 

## 🏁 Getting Started <a name = "getting_started"></a>

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See [deployment](#deployment) for notes on how to deploy the project on a live system.

### Prerequisites

You'll need working Docker and Docker-compose.

```
(To modify: Each container directory has its own requirements.txt file. Use Python3.9 and the requirements)
```

### Installing

Git clone and pip install all requirements.
A redis installation is necessary in order to test modifications, you can accomplish this by running just the redis docker image.

```
cd redis
docker build -t redis .
docker run -p 6379:6379 redis
```

## 🎈 Usage <a name="usage"></a>

Just use Docker-compose
```
docker-compose up
```

## 🚀 Deployment <a name = "deployment"></a>

Add additional notes about how to deploy this on a live system.

## ⛏️ Built Using <a name = "built_using"></a>

- [Docker](https://www.docker.com) - Container Solution
- [Redis](https://redis.io/) - Message Broker

## ✍️ Authors <a name = "authors"></a>

- [@theemperor66](https://github.com/theemperor66)

See also the list of [contributors](https://github.com/InterNetX/domainstudio-multiplexer/contributors) who participated in this project.

## 🎉 Acknowledgements <a name = "acknowledgement"></a>

original redis-docker file: [redis](https://github.com/dockerfile/redis/blob/master/Dockerfile)
original redisqueue implementation: [redisqueue](http://peter-hoffmann.com/2012/python-simple-queue-redis-queue.html)
