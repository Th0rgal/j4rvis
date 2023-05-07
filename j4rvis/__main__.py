from agent import create_agent
from server import WebServer
from auth import hash_password
from langchain.agents import AgentExecutor
from aiohttp import web
from typing import Any
import tomllib
import asyncio
import os


def load_config() -> dict[str, Any]:
    with open("config.toml", "rb") as f:
        return tomllib.load(f)


def load_api_keys(config: dict[str, Any]):
    os.environ["OPENAI_API_KEY"] = config["api"]["open_ai"]
    os.environ["OPENWEATHERMAP_API_KEY"] = config["api"]["openweathermap"]


async def start_server(config: dict[str, Any], agent: AgentExecutor):
    app = WebServer(agent, hash_password(config["server"]["password"])).build_app()
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, port=config["server"]["port"]).start()
    stop_event = asyncio.Event()
    await stop_event.wait()


async def main():
    config = load_config()
    load_api_keys(config)
    agent = create_agent()
    server_task = start_server(config, agent)
    await asyncio.gather(server_task)


asyncio.run(main())
