
from django.core.management.base import BaseCommand
from django.core import exceptions
from selenium import webdriver
from scraping.models import Game
import time
from shutil import which
from psutil import Process
from selenium.webdriver.support.ui import WebDriverWait
from urllib import parse
import datetime as dt
import numpy as np
from lxml import html
import os
import argparse

def start_chromedriver(local=True):
    
    
    chrome_options = webdriver.ChromeOptions()
    
    chrome_options.add_argument("--headless")
    # chrome_options.add_argument('--proxy-server=10.20.30.40:13000')

    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("window-size=1028,900")
    # chrome_options.add_argument("--disable-browser-side-navigation")
    # chrome_options.add_argument("--disable-infobars")
    # chrome_options.add_argument("--incognito")
    # chrome_options.add_argument("enable-automation")

    if local:
        chromepath = os.path.join(os.getcwd(), 'chromedriver') if not which('chromedriver') else which('chromedriver')
        driver = webdriver.Chrome(executable_path=chromepath, chrome_options=chrome_options)
    else:
        chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
        driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chrome_options)
        
    # driver = webdriver.Chrome(executable_path=which('chromedriver'), chrome_options=chrome_options)
    driver.set_page_load_timeout(30)
    driver.set_window_size(1028, 900)

    global chromedriver_pid
    chromedriver_pid = Process(driver.service.process.pid).pid
    return driver


def stop_chromedriver(driver):
    try:
        driver.quit()
    except:
        pass
    try:
        p = Process(chromedriver_pid)
        p.terminate()
    except:
        pass

class Command(BaseCommand):
    help = "collect odds"
        
    # scraper logic below
    def handle(self, *args, **options):
        
        test = False


        driver = start_chromedriver()

        # base_url = 'https://www.oddsportal.com/baseball/usa/mlb/'
        # url_tables_to_scrape = [
        #     base_url] if test else build_season_urls(base_url)

        # wait = WebDriverWait(driver, 5)
        # xpath_result_button = '//a[contains(text(), "RESULT")]'
        # xpath_first_fixture = '//table[@id="tournamentTable"]/tbody/tr[@xeid]/td[2]/a'

        # for url in url_tables_to_scrape:
        #     # both checks if url is still valid and loads it

        driver.get('https://www.google.com')
        # if wait.until(lambda driver: driver.find_element_by_xpath(xpath_result_button).is_displayed() and driver.find_element_by_xpath(xpath_result_button).is_enabled() or
        #               driver.find_element_by_xpath(xpath_first_fixture).is_displayed() and driver.find_element_by_xpath(xpath_first_fixture).is_enabled()):
            

        print(driver.page_source)

        self.stdout.write('url complete')
        time.sleep(10)

        stop_chromedriver(driver)
