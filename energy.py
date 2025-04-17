import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
from bs4 import BeautifulSoup
import schedule
import time
from threading import Thread
import tkinter as tk
from tkinter import scrolledtext
import os

R = r"""
/////////////////////////////////////////////////////////////////////////////////////////////////
//     ___  ___  _      _   ___   ___ ___ ___ ___ ___    ___ _  _ ___ ___ _  _____ ___       ///
//    / __|/ _ \| |    /_\ | _ \ | _ \ _ \_ _/ __| __|  / __| || | __/ __| |/ / __| _ \     ///
//    \__ \ (_) | |__ / _ \|   / |  _/   /| | (__| _|  | (__| __ | _| (__| ' <| _||   /    ///
//    |___/\___/|____/_/ \_\_|_\ |_| |_|_\___\___|___|  \___|_||_|___\___|_|\_\___|_|_\   ///      
//                                                                                       ///                                    
///////////////////////////////////////////////////////////////////////////////////////////
                                                                                  
"""

# IBEX URL
URL = 'https://ibex.bg/данни-за-пазара/пазарен-сегмент-ден-напред/day-ahead-prices-and-volumes-v2-0/'

# GUI Initialization
root = tk.Tk()
root.title("Solar Price Checker")
root.geometry("900x600")
root.configure(bg="#1e1e1e")
username_var = tk.StringVar()
password_var = tk.StringVar()

# Login function to connect with the Login.py script
login_frame = tk.Frame(root, bg="#1e1e1e")
login_frame.pack(pady=10)

tk.Label(login_frame, text="Username:", fg="white", bg="#1e1e1e").grid(row=0, column=0, sticky='w')
tk.Entry(login_frame, textvariable=username_var, width=30).grid(row=0, column=1)

tk.Label(login_frame, text="Password:", fg="white", bg="#1e1e1e").grid(row=1, column=0, sticky='w')
tk.Entry(login_frame, textvariable=password_var, show="*", width=30).grid(row=1, column=1)

def run_login_script():
    global user 
    global pwd
    user = username_var.get()
    pwd = password_var.get()

    if not user or not pwd:
        log("[ERROR] Username or password cannot be empty.")
        return
    
    # Remove login frame from GUI
    login_frame.pack_forget()
    log("[ACTION] Submitting credentials and connecting with Huawei hardware...")
    log("[WARNING] This software will not check for valid credentials, so please make sure you enter them correctly.")

login_btn = tk.Button(login_frame, text="Login", command=run_login_script, bg="#3a3a3a", fg="white")
login_btn.grid(row=2, column=0, columnspan=2, pady=10)

output_box = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=("Consolas", 10), bg="#1e1e1e", fg="white", insertbackground="white")
output_box.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

def log(text):
    output_box.insert(tk.END, text + "\n")
    output_box.see(tk.END)

# Main logic
def main():
    global sunnyHoursCounter, price_above_40, hours_above_40, avgSunnyPrice, switcher

    # Based on the required price this variable will be used to initialize the ON or OFF script.
    switcher = False
  
    sunnyHoursCounter = 0
    price_above_40 = False
    hours_above_40 = 0
    avgSunnyPrice = 0.0

    options = Options()
    options.add_argument("--headless")
    service = Service(executable_path="chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=options)

    log("\n" + "="*70 + "\n[INFO] Checking prices...\n")

    try:
        try:
            driver.get(URL)
            time.sleep(5)
        except WebDriverException:
            log("[ERROR] Network error or page failed to load. Will retry next hour.\n")
            return

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        table = soup.find('table', {'id': 'wpdtSimpleTable-33'})
        if not table:
            log("[ERROR] Table not found. Retrying...")
            main()  # Retry
        else:
            log("[SUCCESS] Table located.")

        rows = table.find('tbody').find_all('tr')
        selected_prices = []

        try:
            first_row_last_col = rows[0].find_all('td')[-1].text.strip()
            price = float(first_row_last_col.replace(',', ''))
            selected_prices.append(price)
        except ValueError:
            pass

        for i in range(2, len(rows), 2):
            sunnyHoursCounter += 1
            try:
                last_col = rows[i].find_all('td')[-1].text.strip()
                price = float(last_col.replace(',', ''))
                if price > 40:
                    hours_above_40 += 1
                if 9 <= sunnyHoursCounter <= 20:
                    avgSunnyPrice += price
                selected_prices.append(price)
            except (IndexError, ValueError):
                continue

  # Calling the huawei logical methods
        if switcher == True:
            huaweiON()
        elif switcher == False:
            huaweiOFF()
        
        programPrint(selected_prices)

    finally:
        driver.quit()

def huaweiON():
            # Here will be the Huawei interface logic to turn ON the solar plantation.
    return

def huaweiOFF():
            # Here will be the Huawei interface logic to turn OFF the solar plantation.
    return

def programPrint(selected_prices):
    log("\n"*20)
    log(R)
    avg_price = (avgSunnyPrice / 12)
    log(f"Prices Tomorrow:\n{selected_prices}")
    log(f"\nHours that the price is above 40 BGN: {hours_above_40}")
    log(f"Tomorrow avg sunny price (09:00 - 20:00): {avg_price:.2f} BGN")
    log(f"Sunny hours avg price above 40 BGN: {'Yes' if avg_price > 40 else 'No'}")
    log(f"\n[INFO] Checking again in 1 hour...")

# Threaded Scheduler to avoid freezing the GUI
def run_schedule():
    schedule.every().hour.do(main)
    while True:
        schedule.run_pending()
        time.sleep(1)

main()
Thread(target=run_schedule, daemon=True).start()

# Run the GUI
root.mainloop()
