import re
import os
import sys
import time
import toml
import random
import string
import requests
import threading
import queue

from typing import Any, Iterable
from types import FunctionType
from fake_useragent import UserAgent
from rich.console import Console
from itertools import cycle, product


exit_flag = threading.Event()
console = Console(highlight=False, log_path=False, width=200)

class ConfigManager:
    """Instrument for config manage and changes"""                  
    def __init__(self):
        if self.find_config_file() is None:
            self.config_path = "./pyproject.toml"
        self.load_config()
        
    def find_config_file(self, directory: str = ".") -> str | None:
        for file in os.listdir(directory):
            if file.endswith(".toml"):
                self.config_path = os.path.join(directory, file)
                return self.config_path
        return None
    
    def load_config(self):
        with open(self.config_path, 'r') as f:
            self.config = toml.load(f)
    
    def find_option(self, key_path: str) -> bool | Any:
        target = self.config
        keys = key_path.split(".")
        for key in keys:
            if key in target:
                if key is not keys[-1]:
                    target = target[key]
            else:
                raise KeyError(f"{key} not found in config")
            
        # console.log("INFO", f"parsed {key_path} option in {self.config_path}", "VALUE", f"{target[key]}",  sep="      ")
        return target[key]
    
    def toggle_config_option(self, option_path: str) -> None:
        target = self.config
        keys = option_path.split(".")
        for key in keys:
            if key in target:
                if key is not keys[-1]:
                    target = target[key]
            else:
                raise KeyError(f"{key} not found in config")
        if isinstance(target[key], bool):
            target[key] = not target[key]
        else:
            raise ValueError(f"{target[key]} is not a boolean")
        with open(self.config_path, 'wb') as f:
            f.write(toml.dumps(self.config).encode())
        self.load_config()    

    def set_config_option(self, option_path: str, new_value: Any) -> None:
        target = self.config
        keys = option_path.split(".")
        for key in keys:
            if key in target:
                if key is not keys[-1]:
                    target = target[key]
            else:
                raise KeyError(f"{key} not found in config")
        if isinstance(target[key], type(new_value)):
            target[key] = new_value
        else:
            raise ValueError(f"cant change {type(target[key])} to {type(new_value)}")
        with open(self.config_path, 'wb') as f:
            f.write(toml.dumps(self.config).encode())
        self.load_config() 


conf = ConfigManager()


class GenerateManager:
    def __init__(self):
        self._allowed_characters = ""

        if conf.find_option("symbols.digits"): self._allowed_characters += string.digits
        if conf.find_option("symbols.letters"): self._allowed_characters += string.ascii_lowercase
        if conf.find_option("symbols.underlines"): self._allowed_characters += "_"
        if conf.find_option("symbols.dots"): self._allowed_characters += "."
    def generate_username(self, length: int):
        return ''.join(random.choices(self._allowed_characters, k=length))

    def generate_file(self, length: int, quantity: int, filename: str = "usernames.txt"):
        users = [self.generate_username(length) for _ in range(quantity)]
        set(users)
        list(users)
        with open(filename, 'a') as f:
            for user in users:
                if user == users[len(users)-1]:
                    f.write(user)
                else:
                    f.write(f'{user}\n')
        console.log("INFO", f"generated {filename}",  "VALUE", f"{quantity} usernames", sep="   ")

    def all_combinations(self, filename: str = "usernames.txt", length: int = 3):
        combinations = product(self._allowed_characters, repeat=length)
        with open(filename, 'w') as f:
            for combo in combinations:
                f.write(''.join(combo) + '\n')
        console.log(f"[+] generated all {length}L combinations ====> {filename}", style="bold magenta",)


class TokenManager:
    def __init__(self):
        
        self.censor_mode = conf.find_option("settings.censor_mode")
        self.multitokens_mode = conf.find_option("settings.multitokens_mode")
        if self.multitokens_mode:
            self.tokens_path = conf.find_option("settings.tokens_path")
            self._load_tokens(self.tokens_path)
        else: self.token = conf.find_option("settings.token")
        
    def token_filter(self, token: str):
        if self.censor_mode:
            token = re.sub(r"\..+\.", repl=".*******.", string=token)
        return token
        
    def token_validator(self, token: str) -> bool:
        r = requests.get("https://discord.com/api/v9/users/@me", headers={"authorization": token})
        if r.status_code == 200 or r.status_code == 429:
            console.log(f"[+] VALID: {self.token_filter(token)},    STATUS: {r.status_code}", style="bold green")
            return True
        else:
            console.log(f"[-] INVALID: {self.token_filter(token)},    STATUS: {r.status_code}", style="bold red")
            return False
                    
    def add_token(self, token: str):
        with open(self.tokens_path, 'a') as f:
            if self.token_validator(token):
                f.write(f"\n{token}")
            else:
                console.log(f"token {token} was not added due to unavailability", style="bold red")

    def _load_tokens(self, filepath: str):
        with console.status("[#ffaa00]LOADING TOKENS...", spinner_style="#ffaa00"):
            with open(filepath, 'r') as f:
                tokens = [token.strip() for token in f.readlines()]
                invalid_tokens = []
                for token in tokens:
                    if not self.token_validator(token):
                        invalid_tokens.append(token)
                valid_tokens = list(set(tokens) - set(invalid_tokens))
                self.token_cycle = cycle(valid_tokens)
    
    def get_token(self):
        return next(self.token_cycle)


class SessionManager(TokenManager):
    
    def create_session(self) -> requests.Session:
        useragent = UserAgent()
        if self.multitokens_mode:
            self.token = self.get_token()
        session = requests.Session()
        session.headers.update({"user-agent": useragent.random, "authorization": self.token})
        console.log(f"[+] NEW SESSION: ---> {self.token_filter(self.token)}", style="bold blue")
        return session


class CheckManager:
    def __init__(self):

        self.slow_mode = conf.find_option("settings.slow_mode")
        self.cooldown = conf.find_option("settings.cooldown")
        if self.slow_mode is False:
            self.cooldown = 0
        self.checked_count = 0
        self.taken_count = 0
        self.available_count = 0
        self.sm_instance = SessionManager()
        self.usernames = queue.Queue()
        
    def username_validator(self, username: str) -> bool:
        symbols = "0123456789abcdefghijklmnopqrstuvwxyz._"
        flag = True
        if len(username) < 2 or len(username) > 32 or '..' in username:
            flag = False
        for symbol in username:
            if symbol not in symbols:
                flag = False
        return flag

    def update_counter_title(self):
        console.set_window_title(f"RQS:[{self.checked_count}] | FREE:[{self.available_count}] | TAKEN:[{self.taken_count}]")
    
    def check_username(self, username: str, session: requests.Session | None = None) -> bool:
        if self.username_validator(username):
            if session is None:
                session = self.sm_instance.create_session()
            show_token = self.sm_instance.token_filter(session.headers["authorization"])
            response = session.post("https://discord.com/api/v9/users/@me/pomelo-attempt", json={"username": username})
            data = response.json()
            if response.status_code == 200:
                self.checked_count += 1
                if data["taken"] == False:
                    self.available_count += 1
                    console.log(f"[+] {username}: FREE ", f"[#5a5019]#{self.checked_count}[/]", f"RESP: {data}", f"[#273c5c]{show_token}[/]", style="bold green", sep="     ")
                    with open("valid.txt", 'a') as f:
                        f.write(f"{username}\n")
                else:
                    self.taken_count += 1
                    console.log(f"[-] {username}: TAKEN", f"[#5a5019]#{self.checked_count}[/]", f"RESP: {data} ", f"[#273c5c]{show_token}[/]", style="bold red", sep="     ")
                return True
            elif response.status_code == 429:
                console.log(f"[!] REQUEST ERROR: {response.status_code}", f"[#273c5c]{show_token}[/]", style="bold red")
                console.log(f"INFO: rate limited session, retry after {data['retry_after']}ms", style="bold magenta")
            else: 
                console.log(f"[!] REQUEST ERROR: {response.status_code}", f"RESP: {data}", f"[#273c5c]{show_token}[/]", style="bold red", sep="  ")
            return False
        else:
            console.log(f'[!] username "{username}" is invalid. the username must contain digits, letters, underlines and dots from 2 to 32 characters and it cant contain repeating dots', style="bold red")
            return True


    def _load_usernames(self, filename: str = "usernames.txt"):
        self.filename = filename
        with open(self.filename, 'r') as f:
            for username in f.readlines():
                self.usernames.put(username.strip())
            # console.log("INFO", f"loaded usernames from {self.filename}", sep="     ")
        

    def check_from_file(self):
        session = self.sm_instance.create_session()
        while not exit_flag.is_set():
            try:
                username = self.usernames.get_nowait()
            except queue.Empty:
                # console.log("INFO", f" checked all usernames in {self.filename}",  sep="     ")
                break
            success = self.check_username(username, session)
            while success is False:
                session = self.sm_instance.create_session()
                success = self.check_username(username, session)
            self.usernames.task_done()
            self.update_counter_title()
            time.sleep(self.cooldown)

    def check_gens(self, length: int, quantity: int):
        gm = GenerateManager()
        session = self.sm_instance.create_session()
        for _ in range(quantity):
            success = self.check_username(gm.generate_username(length), session)
            while success is False:
                session = self.sm_instance.create_session()
                success = self.check_username(gm.generate_username(length), session)
            self.update_counter_title()
            time.sleep(self.cooldown)
    

class ThreadManager:
    def __init__(self, threadquantity: int, function: FunctionType, args: Iterable[Any] | None = ()):
        self.function = function
        self.args = args
        self.threadquantity = threadquantity
        self.threads = []
    
    def signal_handler(self):
        console.log("INFO", f"Ctrl+C signal detected", sep="     ")
        console.log("INFO", f"end all threads...", sep="     ")
        exit_flag.set()
        sys.exit()
    
    def wait_for_completion(self):
        while True:
            try:
                time.sleep(0.1)
            except KeyboardInterrupt:
                self.signal_handler()
                for t in self.threads:
                    t.join()
    
    def mass_thread(self):
        start = time.time()
        for i in range(self.threadquantity):
            thread = threading.Thread(target=self.function, args=self.args, name=f"thread-{i}")
            thread.start()
            self.threads.append(thread)
        end = time.time()
        console.log(f"[bold magenta]INFO[bold magenta]: checked all in {round(end-start, 3)}ms")

if __name__ == "__main__":
    # cm = CheckManager()
    # cm._load_usernames(filename="3L.txt")
    # tm = ThreadManager(function=cm.check_from_file, threadquantity=3)
    # tm.mass_thread()
    # tm.wait_for_completion()
    print('enter the command: python main.py')
    sys.exit()