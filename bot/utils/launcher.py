import os
import re
import glob
import asyncio
import argparse
import random
from itertools import cycle

from pyrogram import Client
from better_proxy import Proxy

from bot.config import settings
from bot.utils import logger
from bot.core.tapper import run_tapper
from bot.core.query import run_query
from bot.core.registrator import register_sessions

start_text = """

Select an action:

    1. Run clicker (Session)
    2. Create session
    3. Run clicker (Query)
"""

global tg_clients


def numerical_sort(value):
    numbers = re.compile(r'(\d+)')
    parts = numbers.split(value)
    parts[1::2] = map(int, parts[1::2])
    return parts

def get_session_folders() -> list[str]:
    return sorted(glob.glob("sessions/"), key=numerical_sort)


def get_session_names(folder_path: str) -> list[str]:
    session_names = sorted(glob.glob(f"{folder_path}*.session"))
    session_names = [
        os.path.splitext(os.path.basename(file))[0] for file in session_names
    ]

    return session_names


def get_proxies() -> list[Proxy]:
    if settings.USE_PROXY_FROM_FILE:
        with open(file="bot/config/proxies.txt", encoding="utf-8-sig") as file:
            proxies = [Proxy.from_str(proxy=row.strip()).as_url for row in file]
    else:
        proxies = []

    return proxies


async def get_tg_clients(folder_path: str, session_names: list[str]) -> list[Client]:
    global tg_clients

    if not session_names:
        raise FileNotFoundError("No session files found in the folder.")

    if not settings.API_ID or not settings.API_HASH:
        raise ValueError("API_ID and API_HASH not found in the .env file.")

    tg_clients = [
        Client(
            name=session_name,
            api_id=settings.API_ID,
            api_hash=settings.API_HASH,
            workdir=folder_path, 
        )
        for session_name in session_names
    ]

    return tg_clients


async def process() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--action", type=int, help="Action to perform")

    action = parser.parse_args().action

    if not action:
        print(start_text)
        while True:
            action = input("> ")
            if not action.isdigit():
                logger.warning("Action must be a number.")
            elif action not in ["1", "2", "3"]:
                logger.warning("Action must be 1, 2 or 3.")
            else:
                action = int(action)
                break

    if action == 1:
        while True: 
            session_folders = get_session_folders()
            
            for folder in session_folders:
                session_names = get_session_names(folder)
                tg_clients = await get_tg_clients(folder, session_names)
                
                logger.info(f"Running sessions in folder {folder} with {len(session_names)} sessions.")
                await run_tasks(tg_clients=tg_clients) 

            # Random sleep time between 3 and 6 hours (10800 to 21600 seconds)
            sleep_duration = random.randint(10800, 21600)
            logger.info(f"All sessions completed. Sleeping for {sleep_duration / 3600:.2f} hours before restarting.")
            await asyncio.sleep(sleep_duration)

    elif action == 2:
        await register_sessions()

    elif action == 3:
        while True: 
            with open("data.txt", "r") as f:
                query_ids = [line.strip() for line in f.readlines()]
            
            proxies = get_proxies()
            proxies_cycle = cycle(proxies) if proxies else None
            account_name = [i for i in range(len(query_ids) + 10)]
            name_cycle = cycle(account_name) if account_name else None

            logger.info(f"Found {len(query_ids)} queries.")
            for query_id in query_ids:
                await run_query(query_id, session_name=f"Account {next(name_cycle)}", proxy=next(proxies_cycle) if proxies_cycle else None)

            # Random sleep time between 3 and 6 hours (10800 to 21600 seconds)
            sleep_duration = random.randint(10800, 21600)
            logger.info(f"All sessions completed. Sleeping for {sleep_duration / 3600:.2f} hours before restarting.")
            await asyncio.sleep(sleep_duration)


async def run_tasks(tg_clients: list[Client]):
    proxies = get_proxies()
    proxies_cycle = cycle(proxies) if proxies else None

    tasks = [
        asyncio.create_task(
            run_tapper(
                tg_client=tg_client,
                proxy=next(proxies_cycle) if proxies_cycle else None,
            )
        )
        for tg_client in tg_clients
    ]

    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        logger.warning("Shutting down gracefully...")

        for task in tasks:
            task.cancel()

        for tg_client in tg_clients:
            await tg_client.stop()
    finally:
        logger.info("All tasks in the current DAO folder completed.")

