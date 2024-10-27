import aiohttp
import asyncio
import json
import os
import pytz
import random
import string
import time
from datetime import datetime
from colorama import init, Fore, Style
from urllib.parse import unquote
from utils.headers import headers_set
from utils.queries import QUERY_USER, QUERY_LOGIN, MUTATION_GAME_PROCESS_TAPS_BATCH, QUERY_BOOSTER, QUERY_NEXT_BOSS
from utils.queries import QUERY_GAME_CONFIG

url = "https://api-gw-tg.memefi.club/graphql"

# HANDLE SEMUA ERROR TAROH DISINI BANG SAFE_POST
async def safe_post(session, url, headers, json_payload):
    retries = 5
    for attempt in range(retries):
        async with session.post(url, headers=headers, json=json_payload) as response:
            if response.status == 200:
                print(Fore.WHITE + Style.BRIGHT + f"▸ Berhasil dengan status {response.status}")
                return await response.json()  # Return the JSON response if successful
            else:
                print(Fore.RED + Style.BRIGHT + f"▸ Gagal dengan status {response.status}, mencoba lagi ({attempt + 1}/{retries})")
                if attempt < retries - 1:  # Jika ini bukan percobaan terakhir, tunggu sebelum mencoba lagi
                    await asyncio.sleep(10)
                else:
                    print(f"{Fore.RED}▸ Gagal setelah beberapa percobaan. Memulai ulang...")
                    return None
    return None

def generate_random_nonce(length=52):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


# Mendapatkan akses token
async def fetch(account_line):
    with open('query_id.txt', 'r') as file:
        lines = file.readlines()
        raw_data = lines[account_line - 1].strip()

    tg_web_data = unquote(unquote(raw_data))
    query_id = tg_web_data.split('query_id=', maxsplit=1)[1].split('&user', maxsplit=1)[0]
    user_data = tg_web_data.split('user=', maxsplit=1)[1].split('&auth_date', maxsplit=1)[0]
    auth_date = tg_web_data.split('auth_date=', maxsplit=1)[1].split('&hash', maxsplit=1)[0]
    hash_ = tg_web_data.split('hash=', maxsplit=1)[1].split('&', maxsplit=1)[0]

    user_data_dict = json.loads(unquote(user_data))

    url = 'https://api-gw-tg.memefi.club/graphql'
    headers = headers_set.copy()  # Membuat salinan headers_set agar tidak mengubah variabel global
    data = {
        "operationName": "MutationTelegramUserLogin",
        "variables": {
            "webAppData": {
                "auth_date": int(auth_date),
                "hash": hash_,
                "query_id": query_id,
                "checkDataString": f"auth_date={auth_date}\nquery_id={query_id}\nuser={unquote(user_data)}",
                "user": {
                    "id": user_data_dict["id"],
                    "allows_write_to_pm": user_data_dict["allows_write_to_pm"],
                    "first_name": user_data_dict["first_name"],
                    "last_name": user_data_dict["last_name"],
                    "username": user_data_dict.get("username", "Username gak diset"),
                    "language_code": user_data_dict["language_code"],
                    "version": "7.2",
                    "platform": "ios"
                }
            }
        },
        "query": QUERY_LOGIN
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            try:
                json_response = await response.json()
                if 'errors' in json_response:
                    # print("Query ID Salah")
                    return None
                else:
                    access_token = json_response['data']['telegramUserLogin']['access_token']
                    return access_token
            except aiohttp.ContentTypeError:
                print("Failed to decode JSON response")
                return None

# Cek akses token
async def cek_user(index):
    access_token = await fetch(index + 1)
    url = "https://api-gw-tg.memefi.club/graphql"

    headers = headers_set.copy()  # Membuat salinan headers_set agar tidak mengubah variabel global
    headers['Authorization'] = f'Bearer {access_token}'
    
    json_payload = {
        "operationName": "QueryTelegramUserMe",
        "variables": {},
        "query": QUERY_USER
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=json_payload) as response:
            if response.status == 200:
                response_data = await response.json()
                if 'errors' in response_data:
                    print(f"{Fore.RED}▸ Gagal: Query ID salah, mohon cek dahulu")
                    return None
                else:
                    user_data = response_data['data']['telegramUserMe']
                    return user_data  # Mengembalikan hasil response
            else:
                print(f"{Fore.RED}▸ Gagal dengan status {response.status}, mencoba lagi...")
                return None  # Mengembalikan None jika terjadi error
            
async def activate_energy_recharge_booster(index,headers):
    access_token = await fetch(index + 1)
    url = "https://api-gw-tg.memefi.club/graphql"

    access_token = await fetch(index + 1)
    headers = headers_set.copy()  # Membuat salinan headers_set agar tidak mengubah variabel global
    headers['Authorization'] = f'Bearer {access_token}'
    
    recharge_booster_payload = {
            "operationName": "telegramGameActivateBooster",
            "variables": {"boosterType": "Recharge"},
            "query": QUERY_BOOSTER
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=recharge_booster_payload) as response:
            if response.status == 200:
                response_data = await response.json()
                if response_data and 'data' in response_data and response_data['data'] and 'telegramGameActivateBooster' in response_data['data']:
                    new_energy = response_data['data']['telegramGameActivateBooster']['currentEnergy']
                    print(Fore.WHITE + Style.BRIGHT + f"\n⌈ Energi terisi. Energi saat ini: {new_energy}")
                else:
                    print(f"{Fore.RED}[ Gagal mengaktifkan Recharge Booster: Data tidak lengkap atau tidak ada.{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}▸ Gagal dengan status {response.status}, mencoba lagi...{Style.RESET_ALL}")
                return None  # Mengembalikan None jika terjadi error
   
async def activate_booster(index, headers):
    access_token = await fetch(index + 1)
    url = "https://api-gw-tg.memefi.club/graphql"
    print(Fore.WHITE + Style.BRIGHT + f"\r↑ Mengaktifkan Turbo Boost (Kekuatan Penuh) ... ", end="", flush=True)

    headers = headers_set.copy()  # Membuat salinan headers_set agar tidak mengubah variabel global
    headers['Authorization'] = f'Bearer {access_token}'

    recharge_booster_payload = {
        "operationName": "telegramGameActivateBooster",
        "variables": {"boosterType": "Turbo"},
        "query": QUERY_BOOSTER
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=recharge_booster_payload) as response:
            if response.status == 200:
                response_data = await response.json()
                current_health = response_data['data']['telegramGameActivateBooster']['currentBoss']['currentHealth']
                if current_health == 0:
                    print(Fore.WHITE + Style.BRIGHT + f"\n⌈ Bos telah dikalahkan, mengatur bos berikutnya...")
                    await set_next_boss(index, headers)
                else:
                    if god_mode == 'y':
                        total_hit = random.randint(10000000, 50000000)  # Hit acak antara 40.000.000 dan 50.000.000
                    else:
                        total_hit = random.randint(100, 50000)  # Hit acak 
                    
                    tap_payload = {
                        "operationName": "MutationGameProcessTapsBatch",
                        "variables": {
                            "payload": {
                                "nonce": generate_random_nonce(),
                                "tapsCount": total_hit
                            }
                        },
                        "query": MUTATION_GAME_PROCESS_TAPS_BATCH
                    }
                    
                    for _ in range(25):
                        tap_result = await submit_taps(index, tap_payload)
                        if tap_result is not None:
                            if 'data' in tap_result and 'telegramGameProcessTapsBatch' in tap_result['data']:
                                tap_data = tap_result['data']['telegramGameProcessTapsBatch']
                                if tap_data['currentBoss']['currentHealth'] == 0:
                                    print(f"{Fore.WHITE}{Style.BRIGHT}\n⌊ Sedang berjuang melawan boss di Level {tap_data['currentBoss']['level']}{Style.RESET_ALL}", end="", flush=True)
                                    await set_next_boss(index, headers)
                                    print(Fore.WHITE + Style.BRIGHT + f"\r[ Merampas {tap_data['coinsAmount']} Coin, Sisa darah boss {tap_data['currentBoss']['currentHealth']} / {tap_data['currentBoss']['maxHealth']}          ", end="", flush=True)
                        else:
                            print(f"{Fore.RED}⌊ Gagal dengan status bangga, mencoba lagi...{Style.RESET_ALL}", end="", flush=True)
            else:
                print(f"{Fore.RED}⌊ Gagal dengan status kelemahan, mencoba lagi...{Style.RESET_ALL}", end="", flush=True)
                return None  # Mengembalikan None jika terjadi error
async def submit_taps(index, json_payload):
    access_token = await fetch(index + 1)
    url = "https://api-gw-tg.memefi.club/graphql"

    headers = headers_set.copy()
    headers['Authorization'] = f'Bearer {access_token}'

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=json_payload) as response:
            if response.status == 200:
                response_data = await response.json()
                return response_data  # Pastikan mengembalikan data yang sudah diurai
            else:
                print(f"▸ Gagal dengan status {response}, mencoba lagi...")
                return None  # Mengembalikan None jika terjadi error
async def set_next_boss(index, headers):
    access_token = await fetch(index + 1)
    url = "https://api-gw-tg.memefi.club/graphql"

    headers = headers_set.copy()  # Membuat salinan headers_set agar tidak mengubah variabel global
    headers['Authorization'] = f'Bearer {access_token}'
    boss_payload = {
        "operationName": "telegramGameSetNextBoss",
        "variables": {},
        "query": QUERY_NEXT_BOSS
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=boss_payload) as response:
            if response.status == 200:
                print(Fore.WHITE + Style.BRIGHT + f"\r⌊ Berhasil mendapatkan bos baru.", end="", flush=True)
            else:
                print(Fore.RED + Style.BRIGHT + f"\r⌊ Gagal mendapatkan bos baru.", flush=True)
                 # Mengembalikan respons error
# cek stat
async def cek_stat(index,headers):
    access_token = await fetch(index + 1)
    url = "https://api-gw-tg.memefi.club/graphql"

    headers = headers_set.copy()  # Membuat salinan headers_set agar tidak mengubah variabel global
    headers['Authorization'] = f'Bearer {access_token}'
    
    json_payload = {
        "operationName": "QUERY_GAME_CONFIG",
        "variables": {},
        "query": QUERY_GAME_CONFIG
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=json_payload) as response:
            if response.status == 200:
                response_data = await response.json()
                if 'errors' in response_data:
                    return None
                else:
                    user_data = response_data['data']['telegramGameGetConfig']
                    return user_data
            else:
                print(response)
                print(f"▸ Gagal dengan status {response.status}, mencoba lagi...")
                return None, None  # Mengembalikan None jika terjadi error

async def main():
    print(Fore.YELLOW + Style.BRIGHT + f"\n⨠ Starting Memefi bot...\n")
    while True:
        with open('query_id.txt', 'r') as file:
            lines = file.readlines()

        # Kumpulkan informasi akun terlebih dahulu
        accounts = []
        for index, line in enumerate(lines):
            result = await cek_user(index)
            if result is not None:
                first_name = result.get('firstName', 'Unknown')
                last_name = result.get('lastName', 'Unknown')
                league = result.get('league', 'Unknown')
                accounts.append((index, result, first_name, last_name, league))
            else:
                print(Fore.RED + Style.BRIGHT + f"▸ Akun {index + 1}: Token tidak valid atau terjadi kesalahan")

        # Setelah menampilkan semua akun
        for index, result, first_name, last_name, league in accounts:
            
            headers = {'Authorization': f'Bearer {result}'}
            stat_result = await cek_stat(index, headers)

            if stat_result is not None:
                user_data = stat_result
                output = (
                    f"\r\n\n⌈ {Fore.WHITE}{Style.BRIGHT}Pendekar : {first_name} {last_name} | {league}\n"
                    f"⌊ {Fore.WHITE}{Style.BRIGHT}Balance  | {user_data['coinsAmount']:,} | Energy : {user_data['currentEnergy']} / {user_data['maxEnergy']}\n"
                    f"⌈ {Fore.WHITE}{Style.BRIGHT}Level    | WP     : {user_data['weaponLevel']}  | Energy : {user_data['energyLimitLevel']} | Charge : {user_data['energyRechargeLevel']}\n"
                    f"⌊ {Fore.WHITE}{Style.BRIGHT}Boss     | Level  : {user_data['currentBoss']['level']}  | Health {user_data['currentBoss']['currentHealth']} / {user_data['currentBoss']['maxHealth']}\n"
                    f"⌈ {Fore.WHITE}{Style.BRIGHT}Free     | Boost  : {user_data['freeBoosts']['currentTurboAmount']}  | Energy {user_data['freeBoosts']['currentRefillEnergyAmount']}\n"
                )
                print(output, end="", flush=True)
                level_bos = user_data['currentBoss']['level']
                darah_bos = user_data['currentBoss']['currentHealth']
                       
                if level_bos == 10 and darah_bos == 0:
                    print(Fore.BLUE + Style.BRIGHT + f"\n⌊ {first_name} {last_name} Sudah bertemu Boss level {user_data['currentBoss']['level']}\n")
                    continue
                if darah_bos == 0:
                    print(Fore.WHITE + Style.BRIGHT + f"\n⌈ Bos Level {user_data['currentBoss']['level']} kalah, mencari boss berikutnya.", flush=True)
                    await set_next_boss(index, headers)
                print(f"\r⌊ Sedang mencari bos Level {user_data['currentBoss']['level']}            ", end="", flush=True)

                energy_sekarang = user_data['currentEnergy']
                energy_used = energy_sekarang - 100
                damage = user_data['weaponLevel']+1
                total_tap = energy_used // damage
  
                if energy_sekarang < 0.25 * user_data['maxEnergy']:
                    if auto_booster == 'y':
                        if user_data['freeBoosts']['currentRefillEnergyAmount'] > 0:
                            print(f"\r⌊ Energy Habis, mengaktifkan Recharge Booster... \n", end="", flush=True)
                            await activate_energy_recharge_booster(index, headers)
                            continue  # Lanjutkan tapping setelah recharge
                        else:
                            print(Fore.WHITE + Style.BRIGHT + f"\r⌊ Energy Habis, tidak ada booster tersedia.\n", flush=True)
                            
                    else:
                        print(Fore.WHITE + Style.BRIGHT + f"\r⌊ Energy Habis, Beralih ke pendekar berikutnya.\n", flush=True)
                        
                tap_payload = {
                        "operationName": "MutationGameProcessTapsBatch",
                        "variables": {
                            "payload": {
                                "nonce": generate_random_nonce(),
                                "tapsCount": total_tap
                            }
                        },
                        "query": MUTATION_GAME_PROCESS_TAPS_BATCH
                    }
                tap_result = await submit_taps(index, tap_payload)
                if tap_result is not None:
                    print(Fore.WHITE + Style.BRIGHT + f"\r⌊ Berhasil bertemu boss Level {user_data['currentBoss']['level']}")
                else:
                    print(Fore.RED + Style.BRIGHT +f"\r▸ Gagal bertemu boss Level {user_data['currentBoss']['level']}, mencoba lagi.")

                if turbo_booster == 'y':
                    if user_data['freeBoosts']['currentTurboAmount'] > 0:
                        await activate_booster(index, headers)
                      #  activate_turbo_boost(headers)
        animate_energy_recharge(15)   

def animate_energy_recharge(duration):
    frames = ["🙏", "🫷", "👐", "👋"]
    end_time = time.time() + duration
    while time.time() < end_time:
        remaining_time = int(end_time - time.time())
        for frame in frames:
            print(Fore.WHITE + Style.BRIGHT + f"\r⌊ Mengisi ulang energi {frame} - Tersisa {remaining_time} detik         ", end="", flush=True)
            time.sleep(0.25)
    print(Fore.WHITE + Style.BRIGHT + f"\r⌊ Pengisian energi selesai.                            ", flush=True)     

# Membuat banner
def print_banner():
    banner = f"""
{Fore.GREEN}{Style.BRIGHT}
===============================================
                                    ___  _ 
                                   / __)(_)
    ____   _____  ____   _____   _| |__  _ 
    |    \ | ___ ||    \ | ___ |(_   __)| |
    | | | || ____|| | | || ____|  | |   | |
    |_|_|_||_____)|_|_|_||_____)  |_|   |_|  

                            TG : itsjaw_real                                 
===============================================

{Fore.YELLOW}{Style.BRIGHT}Please Activate Turbo Booster to Unlock God Mode!
{Style.RESET_ALL}
"""
    print(banner)

# Fungsi untuk mendapatkan input dengan validasi
def get_input(prompt, default='n'):
    while True:
        user_input = input(prompt).strip().lower()
        if user_input in ['y', 'n', '']:
            return user_input or default
        else:
            print(f"{Fore.GREEN}Please Enter 'y' atau 'n'.{Style.RESET_ALL}")

# Mencetak banner
print_banner()

# Menu on/off fitur

auto_booster = input(" 1. Use Energy Booster (default n) ? (y/n): ").strip().lower()
god_mode = input(" 2. Activate God Mode (Damage x50,000,000) ? (y/n): ").strip().lower()

# Atur turbo_booster berdasarkan nilai god_mode
if god_mode == 'y':
    turbo_booster = 'y'
    print(f"\n{Fore.BLUE}{Style.BRIGHT}God Mode : Turbo Booster Automaticaly Active !{Style.RESET_ALL}")
else:
    turbo_booster = input(" 3. Use Turbo Booster (default n) ? (y/n): ").strip().lower()

# Menampilkan konfigurasi yang dipilih
print(f"\n{Fore.YELLOW}{Style.BRIGHT}Konfigurasi yang dipilih:{Style.RESET_ALL}")
print(f"{Fore.WHITE}{Style.BRIGHT}  —— Use Energy Booster: {auto_booster}")
print(f"{Fore.WHITE}{Style.BRIGHT}  —— God Mode: {god_mode}")
print(f"{Fore.WHITE}{Style.BRIGHT}  —— Use Turbo Booster: {turbo_booster}")
# Jalankan fungsi main() dan simpan hasilnya
init(autoreset=True)  # Inisialisasi colorama
asyncio.run(main())


