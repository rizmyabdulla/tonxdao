# 🔥🔥 Tonxdao Tapper Bot 🔥🔥
1. CONCURRENT SESSION HANDLING FOR DAO FARMING
2. AUTO COMPLETES TASKS, CLAIMS DAILY REWARDS

# 🔥🔥 MUST USE PYTHON 3.10 🔥🔥

## Features  
| Feature                                                     | Supported  |
|-------------------------------------------------------------|:----------:|
| Concurrent session handling with async                      |     ✅     |
| Proxy binding to session                                     |     ✅     |
| Auto ref                                                     |     ✅     |
| Auto check-in                                                |     ✅     |
| Auto farm points                                               |     ✅     |
| Auto complete tasks                                          |     ✅     |
| Referral code sign-up support                                |     ✅     |
| Multi-session DAO farming                                    |     ✅     |

## [Settings](https://github.com/rizmyabdulla/tonxdao/blob/main/.env-example)
| Settings                     | Description                                                                                         |
|------------------------------|-----------------------------------------------------------------------------------------------------|
| **API_ID / API_HASH**         | Telegram API credentials used for the sessions (default platform - android)                         |       
| **REF_LINK**                  | Put your referral link here (default: your ref link)                                                 |
| **AUTO_TASK**                 | Automatically complete tasks (default: True)                                                        |
| **AUTO_PLAY_GAME**            | Automatically farm the game (default: True)                                                         |
| **DELAY_EACH_ACCOUNT**        | Delay between account actions (default: [15,25])                                                    |
| **USE_PROXY_FROM_FILE**       | Whether to use a proxy from the bot/config/proxies.txt file (True / False)                          |

## Quick Start 📚

To install libraries and run the bot, open `run.bat` on Windows or follow the manual instructions below.

## Prerequisites
Before you begin, make sure you have the following installed:
- [Python](https://www.python.org/downloads/) **version 3.10**

## Obtaining API Keys
1. Go to my.telegram.org and log in using your phone number.
2. Select "API development tools" and fill out the form to register a new application.
3. Record the API_ID and API_HASH provided after registering your application in the `.env` file.

## Installation
You can download the [**repository**](https://github.com/rizmyabdulla/tonxdao) by cloning it to your system and installing the necessary dependencies:
```shell
git clone https://github.com/rizmyabdulla/tonxdao.git
cd tonxdao
```

Then you can do automatic installation by typing:

Windows:
```shell
run.bat
```

Linux:
```shell
run.sh
```

### Linux manual installation
```shell
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
cp .env-example .env
nano .env  # Here you must specify your API_ID and API_HASH, the rest is taken by default
python3 main.py
```
# You can also use arguments for quick start, for example:
```shell
~/tonxdao >>> python3 main.py --action (1/2)
# Or
~/tonxdao >>> python3 main.py -a (1/2)

# 1 - Run clicker
# 2 - Creates a session
```

### Windows manual installation
```shell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env-example .env
# Here you must specify your API_ID and API_HASH, the rest is taken by default
python main.py
```
# You can also use arguments for quick start, for example:
```shell
~/tonxdao >>> python main.py --action (1/2)
# Or
~/tonxdao >>> python main.py -a (1/2)

# 1 - Run clicker
# 2 - Creates a session
```

# Termux manual installation
```
> pkg update && pkg upgrade -y
> pkg install python rust git -y
> git clone https://github.com/rizmyabdulla/tonxdao.git
> cd tonxdao
> pip install -r requirements.txt
> python main.py
```

You can also use arguments for quick start, for example:
```termux
~/tonxdao > python main.py --action (1/2)
# Or
~/tonxdao > python main.py -a (1/2)

# 1 - Run clicker
# 2 - Creates a session 
```