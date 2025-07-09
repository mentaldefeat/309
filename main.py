from rich.console import Console
from pystyle import Write, Colorate, Colors, Box
from manage import GenerateManager, CheckManager, ThreadManager, ConfigManager
from typing import Dict, Any
import sys
import os

console = Console(highlight=False)
conf = ConfigManager()
gm = GenerateManager()
check = CheckManager()


app_logo = f"""
  .oooo.     .oooo.    .ooooo.  
.dP""Y88b   d8P'`Y8b  888' `Y88.
      ]8P' 888    888 888    888
    <88b.  888    888  `Vbood888
     `88b. 888    888       888'
o.   .88P  `88b  d88'     .88P' 
`8bd88P'    `Y8bd8P'    .oP'    

discord username's availability checker
by [blink u]https://github.com/ritualise[/blink u]
version {conf.find_option("version")}
"""
options = """Main options:
════════════════════════════════════
[1] Check username
[2] Check usernames from file
[3] Generate usernames in file
[4] Add token
[5] Settings
════════════════════════════════════
[0] Exit
"""

generate_options = """Generate options:
═══════════════════════════
[1] Generate all combos 
[2] Set quantity
═══════════════════════════
[0] Back to menu
"""

def main_menu_handle():
    global filename
    global length
    console.print(Colorate.Vertical(Colors.purple_to_blue, Box.DoubleCube(options)), justify='left', end='\n\n')
    while True:
        main_choice = Write.Input("[?] Choose the option: ", Colors.purple_to_blue, interval=0.02)
        match main_choice:
            case "1":
                check.check_username(input(colorate_text("[?] Enter username: ")))
            case "2":
                check._load_usernames(input(colorate_text("[?] Enter name of the file, which should include .txt (default=usernames.txt): ")))
                tm = ThreadManager(threadquantity=int(input(colorate_text("enter quantity of threads: "))),function=check.check_from_file)
                tm.mass_thread()
                tm.wait_for_completion()
                break
            case "3":
                try:
                    filename = input(colorate_text("[?] Enter the name of file (must include .txt): "))
                    length = int(input(colorate_text("[?] Choose length of usernames: ")))
                except ValueError:
                    print(colorate_text("length must be a number."))
                    continue
                generate_handle()
                break
            case "4":
                check.sm_instance.add_token(input(colorate_text("[?] Enter your token: ")))
            case "5":
                settings_handle()
                break
            case "0":
                print(colorate_text("LEAVE THE PEACE..."))
                sys.exit()
                break
            case _:
                print(Colorate.Horizontal(text="Incorrect option, enter the number of the option without any symbols.", color=Colors.blue_to_purple))
        
def generate_handle():
    console.print(Colorate.Vertical(Colors.purple_to_blue, Box.DoubleCube(generate_options)), justify='left', end='\n\n')
    while True:
        generate_choice = Write.Input("[?] Choose the option: ", Colors.purple_to_blue, interval=0.02)
        
        match generate_choice:
            case "1":
                gm.all_combinations(filename, length)
                main_menu_handle()
                break
            case "2":
                quantity = int(input(colorate_text("[?] Enter the quantity of usernames: ")))
                gm.generate_file(length, quantity, filename)
                main_menu_handle()
                break
            case "0":
                main_menu_handle()
                break
            case _:
                print(colorate_text("Incorrect option, enter the number of the option without any symbols."))
        
def settings_handle():
    while True:
        settings = f"""Main settings:
[1] Slow mode: {conf.find_option("settings.slow_mode")}
[2] Set cooldown (if slow mode true)
[3] Censor mode: {conf.find_option("settings.censor_mode")}
[4] Multi tokens mode: {conf.find_option("settings.multitokens_mode")}
[5] Set tokens' file (if multi tokens mode true)
════════════════════════════════════════════════════════════════
Allowed characters:
[6] Digits: {conf.find_option("symbols.digits")}
[7] Letters: {conf.find_option("symbols.letters")}
[8] Underlines: {conf.find_option("symbols.underlines")}
[9] Dots: {conf.find_option("symbols.dots")}
════════════════════════════════════════════════════════════════
[0] Back to menu
"""
        console.print(Colorate.Vertical(Colors.purple_to_blue, Box.DoubleCube(settings)), justify='left', end='\n\n')
        settings_choice = input(colorate_text("[?] Choose the option: "))
        
        match settings_choice:
            case "1":
                conf.toggle_config_option("settings.slow_mode")
                conf.load_config()
                clear_text_block(settings)
            case "2":
                conf.set_config_option("settings.cooldown", float(input(colorate_text(f"[?] Enter a new cooldown value: "))))
                clear_text_block(settings)
            case "3":
                conf.toggle_config_option("settings.censor_mode")
                clear_text_block(settings)
            case "4":
                conf.toggle_config_option("settings.multitokens_mode")
                clear_text_block(settings)
            case "5":
                conf.set_config_option("settings.tokens_path", input(colorate_text(f"[?] Enter a new tokens path: ")))
                clear_text_block(settings)
            case "6":
                conf.toggle_config_option("symbols.digits")
                clear_text_block(settings)
            case "7":
                conf.toggle_config_option("symbols.letters")
                clear_text_block(settings)
            case "8":
                conf.toggle_config_option("symbols.underlines")
                clear_text_block(settings)
            case "9":
                conf.toggle_config_option("symbols.dots")
                clear_text_block(settings)
            case "0":
                main_menu_handle()
                break
            case _:
                # print(colorate_text("Incorrect option, enter the number of the option without any symbols."))
                clear_text_block(settings)



def clear_text_block(text: str):
    lines = text.count('\n') + 4
    for _ in range(lines):
        sys.stdout.write("\033[F")
        sys.stdout.write("\033[K")
    sys.stdout.flush()

def colorate_text(text: str, pystyle_color: list[str] = Colors.purple_to_blue):
    return Colorate.Horizontal(color=pystyle_color, text=text)



def main():
    console.clear()
    console.set_window_title("309")
    console.print(Colorate.Vertical(Colors.purple_to_blue, app_logo), justify='left', end="\n\n")
    main_menu_handle()


if __name__ == "__main__":
    main()