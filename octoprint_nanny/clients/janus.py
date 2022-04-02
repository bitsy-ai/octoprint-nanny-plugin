import asyncio
import aiohttp
import logging
import random
import string
from aiortc import RTCIceServer, RTCConfiguration

logger = logging.getLogger(__name__)
PEER_CONNECTIONS = set()

# reference: https://github.com/aiortc/aiortc/blob/main/examples/janus/janus.py
def transaction_id():
    return "".join(random.choice(string.ascii_letters) for x in range(12))


class JanusPlugin:
    def __init__(self, session, url):
        self._queue = asyncio.Queue()
        self._session = session
        self._url = url

    async def send(self, payload):
        message = {"janus": "message", "transaction": transaction_id()}
        message.update(payload)
        async with self._session._http.post(self._url, json=message) as response:
            data = await response.json()
            assert data["janus"] == "ack"

        response = await self._queue.get()
        assert response["transaction"] == message["transaction"]
        return response


class JanusSession:
    def __init__(self, url: str):
        self._http = None
        self._poll_task = None
        self._plugins = {}
        self._base_url = url
        self._session_url = None
        self._rtc_config = RTCConfiguration(
            iceServers=[RTCIceServer(urls=["stun:stun.l.google.com:19302"])]
        )

    async def attach(self, plugin_name: str = "janus.plugin.streaming") -> JanusPlugin:
        message = {
            "janus": "attach",
            "plugin": plugin_name,
            "transaction": transaction_id(),
        }
        async with self._http.post(self._session_url, json=message) as response:
            data = await response.json()
            assert data["janus"] == "success"
            plugin_id = data["data"]["id"]
            plugin = JanusPlugin(self, self._session_url + "/" + str(plugin_id))
            self._plugins[plugin_id] = plugin
            return plugin

    async def create(self):
        self._http = aiohttp.ClientSession()
        message = {"janus": "create", "transaction": uuid4().hex}
        async with self._http.post(self._root_url, json=message) as response:
            data = await response.json()
            assert data["janus"] == "success"
            session_id = data["data"]["id"]
            self._session_url = self._root_url + "/" + str(session_id)

        self._poll_task = asyncio.ensure_future(self._poll())


async def run(stream, session):
    await session.create()


def main(url, stream):
    # create signaling session
    loop = asyncio.get_event_loop()
    session = JanusSession(url)

    try:
        loop.run_until_complete(run(stream=stream, session=session))
    except KeyboardInterrupt:
        pass
    finally:
        # teardown janus session
        loop.run_until_complete(session.destroy())
        # ensure all peer connections are closed
        tasks = [pc.close() for pc in PEER_CONNECTIONS]
        loop.run_until_complete(asyncio.gather(*tasks))
