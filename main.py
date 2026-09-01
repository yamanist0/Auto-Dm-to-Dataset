import json
import os
import glob
import re
import argparse
import sys
from collections import defaultdict

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "assistant_names": [],
    "categories": {},
    "instagram_paths": [],
    "whatsapp_paths": [],
    "tiktok_paths": [],
    "excluded_users": [],
    "output_file": "output.jsonl"
}

TITLE = r"""
    ___         __           ____               __           ____        __                  __ 
   /   | __  __/ /_____     / __ \____ ___     / /_____     / __ \____ _/ /_____ _________  / /_
  / /| |/ / / / __/ __ \   / / / / __ `__ \   / __/ __ \   / / / / __ `/ __/ __ `/ ___/ _ \/ __/
 / ___ / /_/ / /_/ /_/ /  / /_/ / / / / / /  / /_/ /_/ /  / /_/ / /_/ / /_/ /_/ (__  )  __/ /_  
/_/  |_\__,_/\__/\____/  /_____/_/ /_/ /_/   \__/\____/  /_____/\__,_/\__/\__,_/____/\___/\__/  
                                                                                                                                                                                                                                                                                             
"""

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return DEFAULT_CONFIG.copy()
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        try:
            config = json.load(f)
# filling in any settings we missed
            for key in DEFAULT_CONFIG:
                if key not in config:
                    config[key] = DEFAULT_CONFIG[key]
            return config
        except json.JSONDecodeError:
            print("error config.json is corrupted using default settings.")
            return DEFAULT_CONFIG.copy()

def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

def fix_encoding(text):
    if not isinstance(text, str):
        return text
    try:
# hopefully fixes weird text encoding issues
        return text.encode('latin1').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text

def parse_wp_txt(file_path):
    messages = []
    with open(file_path, 'r', encoding='utf-8') as f:
        pattern = re.compile(r"^(\d{1,2}\.\d{1,2}\.\d{2,4} \d{1,2}:\d{2}) - ([^:]+): (.*)$")
        sys_pattern = re.compile(r"^(\d{1,2}\.\d{1,2}\.\d{2,4} \d{1,2}:\d{2}) - (.*)$")
        
        current_sender = None
        current_content = []
        
        for line in f:
            line = line.replace('\u200e', '') 
            print(f"Processing line: {line.strip()}")
            match = pattern.match(line)
            if match:
                if current_sender is not None:
                    messages.append({
                        "sender_name": current_sender,
                        "content": " \n ".join(current_content).strip()
                    })
                current_sender = match.group(2)
                current_content = [match.group(3).rstrip('\n')]
            else:
                sys_match = sys_pattern.match(line)
                if sys_match:
                    if current_sender is not None:
                        messages.append({
                            "sender_name": current_sender,
                            "content": " \n ".join(current_content).strip()
                        })
                        current_sender = None
                        current_content = []
                else:
                    if current_sender is not None:
                        current_content.append(line.rstrip('\n'))
                        
        if current_sender is not None:
            messages.append({
                "sender_name": current_sender,
                "content": " \n ".join(current_content).strip()
            })
    return messages

def parse_tiktok_json(file_path, excluded_users):
    conversations = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        info = json.load(f)
        
    chat_hist = info.get("Direct Message", {}).get("Direct Messages", {}).get("ChatHistory", {})
    
    print(f"Found {len(chat_hist)} chats in history")
    for chat_key, messages in chat_hist.items():
        person_name = chat_key.replace("Chat History with ", "").rstrip(":")
        
        if any(exc in person_name for exc in excluded_users):
            continue
            
        tk_raw_data = []
        for msg in messages:
            tk_raw_data.append({
                "sender_name": msg.get("From"),
                "content": msg.get("Content"),
                "timestamp_str": msg.get("Date", "")
            })
            
        tk_raw_data.sort(key=lambda x: x["timestamp_str"])
        conversations[person_name] = tk_raw_data
        
    return conversations

def filter_and_group_messages(raw_messages, rel_type, config):
    valid_messages = []
    for msg in raw_messages:
        content = msg.get("content")
        if not content:
            continue
            
        # Clean up any weird text encoding issues
        content = fix_encoding(content)
        
        stripped_content = content.strip()
        if stripped_content in ["Liked a message", "<Medya dahil edilmedi>", "<Media omitted>"]:
            continue
        if stripped_content.startswith("Reacted ") and " to your message" in stripped_content:
            continue
            
        valid_messages.append({
            "sender_name": msg.get("sender_name"),
            "content": content
        })

    if not valid_messages:
        return None

    formatted_messages = []
    current_role = None
    current_content = []
    
    assistant_names = config.get("assistant_names", [])

    for msg in valid_messages:
        sender = msg["sender_name"]
        content = msg["content"]
        
        role = "assistant" if sender in assistant_names else "user"
        
        if role == current_role:
            current_content.append(content)
        else:
            if current_role is not None:
                formatted_messages.append({
                    "role": current_role,
                    "content": " \n ".join(current_content)
                })
            current_role = role
            current_content = [content]

    if current_role is not None:
        formatted_messages.append({
            "role": current_role,
            "content": " \n ".join(current_content)
        })

    final_messages = []
    
    system_prompt = config.get("categories", {}).get(rel_type, "")
    if system_prompt:
        final_messages.append({
            "role": "system",
            "content": system_prompt
        })
    
    i = 0
    while i < len(formatted_messages):
        msg = formatted_messages[i]
        if "dosya eki gönderd" in msg["content"] or "media omitted" in msg["content"]:
            i += 2
            continue
        final_messages.append(msg)
        i += 1

    roles = [m["role"] for m in final_messages]
    if "user" in roles and "assistant" in roles:
        return {"messages": final_messages}
    return None

def process_all(config):
    final_output_data = []
    all_conversations_map = defaultdict(lambda: defaultdict(list))
    
    categories = list(config.get("categories", {}).keys())
    excluded_users = config.get("excluded_users", [])
    
    if not categories:
        print("error no categories defined please add a category using config add-category")
        sys.exit(1)

    print("processing data...")

    # collect instagram data
    for current_inbox in config.get("instagram_paths", []):
        for rel_type in categories:
            rel_path = os.path.join(current_inbox, rel_type)
            if not os.path.exists(rel_path):
                continue
                
            for person_folder in os.listdir(rel_path):
                if any(exc in person_folder for exc in excluded_users):
                    continue
                    
                person_dir = os.path.join(rel_path, person_folder)
                if os.path.isdir(person_dir):
                    msg_files = glob.glob(os.path.join(person_dir, "message_*.json"))
                    for mf in msg_files:
                        with open(mf, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            all_conversations_map[rel_type][person_folder].extend(data.get("messages", []))

# now we sort and group the instagram chats we found
    for rel_type, persons_dict in all_conversations_map.items():
        for person_folder, all_raw_messages in persons_dict.items():
            if not all_raw_messages:
                continue
            all_raw_messages.sort(key=lambda x: x.get("timestamp_ms", 0))
            conv = filter_and_group_messages(all_raw_messages, rel_type, config)
            if conv:
                final_output_data.append(conv)

    for wp_path in config.get("whatsapp_paths", []):
        for rel_type in categories:
            rel_path = os.path.join(wp_path, rel_type)
            if not os.path.exists(rel_path):
                continue
                
            txts = glob.glob(os.path.join(rel_path, "*.txt"))
            for tf in txts:
                file_name = os.path.basename(tf)
                if any(exc in file_name for exc in excluded_users):
                    continue
                    
                wp_raw_messages = parse_wp_txt(tf)
                if not wp_raw_messages:
                    continue
                
                conv = filter_and_group_messages(wp_raw_messages, rel_type, config)
                if conv:
                    final_output_data.append(conv)

    for tk_entry in config.get("tiktok_paths", []):
        tk_path = tk_entry.get("path")
        tk_rel_type = tk_entry.get("category")
        
        if tk_path and os.path.exists(tk_path) and tk_rel_type in categories:
            tk_conversations = parse_tiktok_json(tk_path, excluded_users)
            for person_name, tk_raw_messages in tk_conversations.items():
                conv = filter_and_group_messages(tk_raw_messages, tk_rel_type, config)
                if conv:
                    final_output_data.append(conv)

    # calculate total words and assign ids
    total_words = 0
    global_msg_id = 0
    
    def format_id(n):
        # pad with zeros to make it nine digits
        s = f"{n:09d}"
        return f"{s[:3]}-{s[3:6]}-{s[6:]}"

    for conv in final_output_data:
        new_messages = []
        for msg in conv["messages"]:
            new_msg = {"id": format_id(global_msg_id)}
            new_msg.update(msg)
            new_messages.append(new_msg)
            
            global_msg_id += 1
            total_words += len(new_msg["content"].split())
        conv["messages"] = new_messages

    output_file = config.get("output_file", "output.jsonl")
    
    # write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_output_data, f, ensure_ascii=False, indent=2)
        
    print(f"total {len(final_output_data)} conversations converted. output {output_file}")
    print(f"total words used {total_words}")

def interactive_menu(title, options):
    current_index = 0
    while True:
        # this clears the terminal screen for a clean look
        os.system('cls' if os.name == 'nt' else 'clear')
        print(title)
        print("please use up down arrow keys to navigate and press enter\n")
        
        for i, option in enumerate(options):
            if i == current_index:
                print(f" > {option}")
            else:
print(f"  {option}")

        #  check for keypress without blocking
        if os.name == 'nt':
            import msvcrt
            key = msvcrt.getch()
            if key in [b'\xe0', b'\x00']:
                key = msvcrt.getch()
                if key == b'H': # up
                    current_index = (current_index - 1) % len(options)
                elif key == b'P': # down
                    current_index = (current_index + 1) % len(options)
            elif key == b'\r': # enter
                return current_index
            elif key == b'\x03': # ctrl c
                sys.exit(0)
        else:
            import tty, termios
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
                ch = sys.stdin.read(1)
                if ch == '\x1b':
                    ch2 = sys.stdin.read(2)
                    if ch2 == '[A':
                        current_index = (current_index - 1) % len(options)
                    elif ch2 == '[B':
                        current_index = (current_index + 1) % len(options)
                elif ch == '\r' or ch == '\n':
                    return current_index
                elif ch == '\x03': # ctrl c
                    sys.exit(0)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def run_interactive_mode(config):
    options = [
        "1. process data and generate jsonl (run)",
        "2. view current configuration",
        "3. set assistant names",
        "4. add new category",
        "5. add instagram path",
        "6. add whatsapp path",
        "7. add tiktok path",
        "8. exit"
    ]
    
    while True:
        choice = interactive_menu(TITLE, options)
        
        if choice == 0:
            os.system('cls' if os.name == 'nt' else 'clear')
            print(TITLE)
            print("your current settings\n")
            print(json.dumps(config, indent=4, ensure_ascii=False))
            print("\nare you sure about these settings\n")
            
            conf_opts = ["1. yes start process", "2. no return to menu"]
            confirm_choice = interactive_menu(TITLE + "\nsettings confirmation", conf_opts)
            
            if confirm_choice == 0:
                print("\nstarting process\n")
                process_all(config)
                input("\npress enter to continue")
            else:
                print("\nprocess cancelled. returning to menu")
                import time
                time.sleep(1)
        
        elif choice == 1:
            os.system('cls' if os.name == 'nt' else 'clear')
            print(TITLE)
            print("current settings\n")
            print(json.dumps(config, indent=4, ensure_ascii=False))
            input("\npress enter to continue")
            
        elif choice == 2:
            os.system('cls' if os.name == 'nt' else 'clear')
            print(TITLE)
            names = input("enter assistant names separated by space ")
            if names.strip():
                config["assistant_names"] = names.split()
                save_config(config)
                print("assistant names successfully saved")
            input("\npress enter to continue")
            
        elif choice == 3:
            os.system('cls' if os.name == 'nt' else 'clear')
            print(TITLE)
            cat_name = input("category name (e.g. friend) ")
            if cat_name.strip():
                cat_prompt = input("category prompt ")
                config["categories"][cat_name.strip()] = cat_prompt
                save_config(config)
                print("category successfully saved")
            input("\npress enter to continue")
            
        elif choice == 4:
            os.system('cls' if os.name == 'nt' else 'clear')
            print(TITLE)
            ig_path = input("instagram folder path ")
            if ig_path.strip():
                if ig_path not in config["instagram_paths"]:
                    config["instagram_paths"].append(ig_path.strip())
                    save_config(config)
                    print("path successfully added")
                else:
                    print("this path already exists")
            input("\npress enter to continue")
            
        elif choice == 5:
            os.system('cls' if os.name == 'nt' else 'clear')
            print(TITLE)
            wp_path = input("whatsapp folder path ")
            if wp_path.strip():
                if wp_path not in config["whatsapp_paths"]:
                    config["whatsapp_paths"].append(wp_path.strip())
                    save_config(config)
                    print("path successfully added")
                else:
                    print("this path already exists")
            input("\npress enter to continue")
            
        elif choice == 6:
            os.system('cls' if os.name == 'nt' else 'clear')
            print(TITLE)
            tcl_path = input("tiktok json file path ")
            if tcl_path.strip():
                tk_cat = input("category for tiktok file (e.g. friend) ")
                if tk_cat.strip():
                    new_tk = {"path": tcl_path.strip(), "category": tk_cat.strip()}
                    if new_tk not in config["tiktok_paths"]:
                        config["tiktok_paths"].append(new_tk)
                        save_config(config)
                        print("path and category successfully added")
                    else:
                        print("this setting already exists")
            input("\npress enter to continue")
            

        elif choice == 7:
            os.system('cls' if os.name == 'nt' else 'clear')
            print("exiting...")
            break

def setup_cli():
    # open interactive menu if no arguments are provided
    if len(sys.argv) == 1:
        config = load_config()
        run_interactive_mode(config)
        return

    parser = argparse.ArgumentParser(description="chat dataset builder for ai")
    subparsers = parser.add_subparsers(dest="command", help="available commands")

    # config command
    config_parser = subparsers.add_parser("config", help="manage configuration settings")
    config_parser.add_argument("--set-assistant", nargs="+", help="set assistant names separate multiple names with spaces")
    config_parser.add_argument("--add-category", nargs=2, metavar=("NAME", "PROMPT"), help="add category and system prompt")
    config_parser.add_argument("--add-ig-path", metavar="PATH", help="add root folder path for instagram data")
    config_parser.add_argument("--add-wp-path", metavar="PATH", help="add root folder path for whatsapp data")
    config_parser.add_argument("--add-tk-path", nargs=2, metavar=("PATH", "CATEGORY"), help="add tiktok json file and category")
    config_parser.add_argument("--exclude-user", metavar="USERNAME", help="add username to exclude")
    config_parser.add_argument("--set-output", metavar="FILE", help="set output file name")
    config_parser.add_argument("--show", action="store_true", help="show current configuration")

    # run command
    run_parser = subparsers.add_parser("run", help="process data and generate jsonl")

    args = parser.parse_args()
    config = load_config()

    if args.command == "config":
        updated = False
        
        if args.set_assistant:
            config["assistant_names"] = args.set_assistant
            print(f"assistant names set to {args.set_assistant}")
            updated = True
            
        if args.add_category:
            cat_name, cat_prompt = args.add_category
            config["categories"][cat_name] = cat_prompt
            print(f"category added {cat_name}")
            updated = True
            
        if args.add_ig_path:
            if args.add_ig_path not in config["instagram_paths"]:
                config["instagram_paths"].append(args.add_ig_path)
                print(f"instagram path added {args.add_ig_path}")
                updated = True
                
        if args.add_wp_path:
            if args.add_wp_path not in config["whatsapp_paths"]:
                config["whatsapp_paths"].append(args.add_wp_path)
                print(f"whatsapp path added {args.add_wp_path}")
                updated = True
                
        if args.add_tk_path:
            path, category = args.add_tk_path
            new_tk = {"path": path, "category": category}
            if new_tk not in config["tiktok_paths"]:
                config["tiktok_paths"].append(new_tk)
                print(f"tiktok path added {path} category {category}")
                updated = True
                
        if args.exclude_user:
            if args.exclude_user not in config["excluded_users"]:
                config["excluded_users"].append(args.exclude_user)
                print(f"excluded user added {args.exclude_user}")
                updated = True
                
        if args.set_output:
            config["output_file"] = args.set_output
            print(f"output file set to {args.set_output}")
            updated = True

        if updated:
            save_config(config)
            print("configuration updated and saved")
            
        if args.show or not updated:
print("Current config:", json.dumps(config, indent=2, ensure_ascii=False))

    elif args.command == "run":
        process_all(config)
    else:
        parser.print_help()

if __name__ == '__main__':
    setup_cli()
