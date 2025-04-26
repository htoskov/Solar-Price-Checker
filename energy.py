from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
from bs4 import BeautifulSoup
import requests
import schedule
import time
import json
from datetime import datetime, timedelta
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
login_frame = tk.Frame(root, bg="#1e1e1e")
login_frame.pack(pady=10)

global driver
def get_driver():
    options = Options()
 #  options.add_argument("--headless") 
    service = Service(executable_path="chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=options)
    return driver

output_box = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=("Consolas", 10), bg="#1e1e1e", fg="white", insertbackground="white")
output_box.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

# Colors
output_box.tag_config("green", foreground="lime")
output_box.tag_config("red", foreground="red")
output_box.tag_config("white", foreground="white")

def log(text, tag="white"):
    output_box.insert(tk.END, text + "\n", tag)
    output_box.see(tk.END)
########################################################## GUI STRUCTURE END ##########################################################

def main():
    current_hour = datetime.now().hour
    global driver
    driver = get_driver()
    

    log(R)
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
            return
        else:
            log("[SUCCESS] Table located.")

        rows = table.find('tbody').find_all('tr')
        selected_prices = []


        for i in range(0, len(rows), 2):
            try:
                last_col = rows[i].find_all('td')[-2].text.strip()
                price = float(last_col.replace(',', '').replace('лв.', ''))
                selected_prices.append(price)
            except (IndexError, ValueError):
                selected_prices.append(None)

        # Get current hour price
        if current_hour < len(selected_prices):
            current_price = selected_prices[current_hour]
            log(f"[INFO] Current hour ({current_hour}) price: {current_price} лв.")

            if current_price is not None:
                if current_price > 40:
                    log(f"[ACTION] Price is high. Turning ON Huawei system.", tag="green")
                    huaweiON()
                else:
                    log(f"[ACTION] Price is low. Turning OFF Huawei system.", tag="red")
                    huaweiOFF()
            else:
                log("[WARNING] No valid price data for current hour.")
        else:
            log("[WARNING] Not enough hourly price data available.")

        programPrint(selected_prices)

    finally:
        driver.quit()

def huaweiON():
    with open('credentials.json') as f:
        credentials = json.load(f)
    username = credentials["username"]
    password = credentials["password"]
    proizvodstveniSgradi = credentials["1"]
    noviSkladove = credentials["2"]

    huaweiURL = "https://eu5.fusionsolar.huawei.com/"
    driver = get_driver()
    time.sleep(5)
    driver.get(huaweiURL)
    time.sleep(5)
    huaweiSoup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.find_element(By.ID, "username").send_keys(username)
    time.sleep(3)
    driver.find_element(By.ID, "value").send_keys(password)
    time.sleep(3)
    driver.find_element(By.CLASS_NAME, "loginBtn").click()
    time.sleep(5)

    # Proizvodstveni Sgradi Inverter
    driver.get("https://uni002eu5.fusionsolar.huawei.com/uniportal/pvmswebsite/assets/build/cloud.html?app-id=smartpvms&instance-id=smartpvms&zone-id=region-2-aaeafa18-4690-4f82-b58f-f69e775e788c#/view/device/NE=134714396/submatrix/details")
    button = WebDriverWait(driver, 20).until(
    EC.element_to_be_clickable((By.XPATH, "//span[@title='Active Power Adjustment']/button"))
    )
    button.click()
    time.sleep(5)
    input_field = driver.find_element(By.CLASS_NAME, "ant-input-number-input")
    input_field.send_keys(proizvodstveniSgradi)
    time.sleep(5)
    button = driver.find_element(By.XPATH, "//span[text()='Preset']/..")
    button.click()
    time.sleep(7)
    button = driver.find_element(By.XPATH, "//span[text()='Execute']/..")
    button.click()
    time.sleep(7)

    try:
        button = driver.find_element(By.CLASS_NAME, "ant-btn-primary")
        button.click()
    except NoSuchElementException:
        # Button not found, continue with the script
        pass

    log(f"[INFO] proizvodstveniSgradi inverter set to {proizvodstveniSgradi}kW")

    # Novi Skladove Inverter
    driver.get("https://uni002eu5.fusionsolar.huawei.com/uniportal/pvmswebsite/assets/build/cloud.html?app-id=smartpvms&instance-id=smartpvms&zone-id=region-2-aaeafa18-4690-4f82-b58f-f69e775e788c#/view/device/NE=134601162/submatrix/details")
    button = WebDriverWait(driver, 20).until(
    EC.element_to_be_clickable((By.XPATH, "//span[@title='Active Power Adjustment']/button"))
    )
    button.click()
    time.sleep(5)
    input_field = driver.find_element(By.CLASS_NAME, "ant-input-number-input")
    input_field.send_keys(noviSkladove)
    time.sleep(5)
    button = driver.find_element(By.XPATH, "//span[text()='Preset']/..")
    button.click()
    time.sleep(7)
    button = driver.find_element(By.XPATH, "//span[text()='Execute']/..")
    button.click()
    time.sleep(7)

    try:
        button = driver.find_element(By.CLASS_NAME, "ant-btn-primary")
        button.click()
    except NoSuchElementException:
        # Button not found, continue with the script
        pass

    log(f"[INFO] Novi Skladove inverter set to {noviSkladove}kW")
    driver.quit()
    return

def huaweiOFF():
    with open('credentials.json') as f:
        credentials = json.load(f)
    username = credentials["username"]
    password = credentials["password"]

    huaweiURL = "https://eu5.fusionsolar.huawei.com/"
    driver = get_driver()
    time.sleep(5)
    driver.get(huaweiURL)
    time.sleep(5)
    huaweiSoup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.find_element(By.ID, "username").send_keys(username)
    time.sleep(3)
    driver.find_element(By.ID, "value").send_keys(password)
    time.sleep(3)
    driver.find_element(By.CLASS_NAME, "loginBtn").click()
    time.sleep(5)

    # Proizvodstveni Sgradi Inverter
    driver.get("https://uni002eu5.fusionsolar.huawei.com/uniportal/pvmswebsite/assets/build/cloud.html?app-id=smartpvms&instance-id=smartpvms&zone-id=region-2-aaeafa18-4690-4f82-b58f-f69e775e788c#/view/device/NE=134714396/submatrix/details")
    button = WebDriverWait(driver, 20).until(
    EC.element_to_be_clickable((By.XPATH, "//span[@title='Active Power Adjustment']/button"))
    )
    button.click()
    time.sleep(5)
    input_field = driver.find_element(By.CLASS_NAME, "ant-input-number-input")
    input_field.send_keys("0")
    time.sleep(5)
    button = driver.find_element(By.XPATH, "//span[text()='Preset']/..")
    button.click()
    time.sleep(7)
    button = driver.find_element(By.XPATH, "//span[text()='Execute']/..")
    button.click()
    time.sleep(7)

    try:
        button = driver.find_element(By.CLASS_NAME, "ant-btn-primary")
        button.click()
    except NoSuchElementException:
        # Button not found, continue with the script
        pass

    log("[INFO] proizvodstveniSgradi inverter set to 0 kW")

    # Novi Skladove Inverter
    driver.get("https://uni002eu5.fusionsolar.huawei.com/uniportal/pvmswebsite/assets/build/cloud.html?app-id=smartpvms&instance-id=smartpvms&zone-id=region-2-aaeafa18-4690-4f82-b58f-f69e775e788c#/view/device/NE=134601162/submatrix/details")
    button = WebDriverWait(driver, 20).until(
    EC.element_to_be_clickable((By.XPATH, "//span[@title='Active Power Adjustment']/button"))
    )
    button.click()
    time.sleep(5)
    input_field = driver.find_element(By.CLASS_NAME, "ant-input-number-input")
    input_field.send_keys("0")
    time.sleep(5)
    button = driver.find_element(By.XPATH, "//span[text()='Preset']/..")
    button.click()
    time.sleep(7)
    button = driver.find_element(By.XPATH, "//span[text()='Execute']/..")
    button.click()
    time.sleep(7)

    try:
        button = driver.find_element(By.CLASS_NAME, "ant-btn-primary")
        button.click()
    except NoSuchElementException:
        # Button not found, continue with the script
        pass

    log("[INFO] Novi Skladove inverter set to 0 kW")
    driver.quit()
    return

def wait_until_next_hour():
    now = datetime.now()
    next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    sleep_seconds = (next_hour - now).total_seconds()
    time.sleep(sleep_seconds)

def programPrint(selected_prices):
    log("\n")
    log(f"Prices Tomorrow:\n{selected_prices}")
    log(f"\n[INFO] Checking again in the next hour...")

def hourly_loop():
    while True:
        main()
        wait_until_next_hour()

# Run the program
Thread(target=hourly_loop, daemon=True).start()
root.mainloop()
