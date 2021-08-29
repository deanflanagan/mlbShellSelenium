
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
parser = argparse.ArgumentParser()


def load_tournament_url(driver, url):
    wait = WebDriverWait(driver, 5)
    xpath_result_button = '//a[contains(text(), "RESULT")]'
    xpath_first_fixture = '//table[@id="tournamentTable"]/tbody/tr[@xeid]/td[2]/a'

    tries = 0
    while tries < 5:
        try:
            driver.get(url)
            wait.until(lambda driver: driver.find_element_by_xpath(xpath_result_button).is_displayed() and driver.find_element_by_xpath(xpath_result_button).is_enabled() or
                       driver.find_element_by_xpath(xpath_first_fixture).is_displayed() and driver.find_element_by_xpath(xpath_first_fixture).is_enabled())

            return True
        except:
            tries += 1
            print(tries)
    return False


def check_if_league_is_empty(driver):
    wait = WebDriverWait(driver, 1.5)
    empty_league_xpath = '//table[@id="tournamentTable"]/tbody/tr/td[@id="emptyMsg"]'
    try:
        wait.until(lambda driver: driver.find_element_by_xpath(empty_league_xpath).is_displayed() and
                   driver.find_element_by_xpath(empty_league_xpath).is_enabled())
        return False
    except:
        return True


def build_season_urls(url):
    if type(url) != list:
        urls = [url]
    if 'results' not in url:
        for num in range(1, 99):
            if num == 1:
                urls.append(parse.urljoin(url, 'results'))
            else:
                suffix = f'results/#/page/{num}/'
                urls.append(parse.urljoin(url, suffix))
    return urls


def get_tournament_id(first_table_row):
    try:
        return int(first_table_row.get("xtid"))
    except:
        return -1


def get_sport_country_league(first_table_row):
    try:
        value = first_table_row.find("th/a[3]").get("href")
        return value.split("/")[1], value.split("/")[2], value.split("/")[3]
    except:
        return np.nan, np.nan, np.nan


def get_odds(row):
    odds_list = row.findall("td[@xodd]")
    if len(odds_list) == 3:
        try:
            home = float(odds_list[0].text_content())
        except:
            home = 1.01
        try:
            draw = float(odds_list[1].text_content())
        except:
            draw = 1.01
        try:
            away = float(odds_list[2].text_content())
        except:
            away = 1.01
        return home, away, draw
    elif len(odds_list) == 2:
        try:
            home = float(odds_list[0].text_content())
        except:
            home = 1.01
        try:
            away = float(odds_list[1].text_content())
        except:
            away = 1.01
        return home, away, None
    else:
        print("There is a different kind of odds and scrapper needs to be edited!")


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


# note the url has to be a single league endpoint so sport/country/competition

def get_tournament_data(driver):

    tree = html.fromstring(driver.page_source)
    first_table_row = tree.xpath(
        '//table[@id="tournamentTable"]/tbody/tr[1]')[0]
    tournament_id = get_tournament_id(first_table_row)
    sport, country, league = get_sport_country_league(first_table_row)

    fixtures_list = tree.xpath(
        '//table[@id="tournamentTable"]/tbody/tr[@xeid]')
    data = []

    # make GET of all finished ft games here to compare when to break
    for row in fixtures_list:

        match_id = row.get("xeid")

        # if the game is in the already posted ft games and it's more than a day since, continue

        match_unix_time = int(row.find("td[1]").get(
            "class").split("t")[-1].split("-")[0])
        match_utc_time = dt.datetime.utcfromtimestamp(
            match_unix_time)

        fixture = row.xpath(
            'td[2]/a[not(starts-with(@href, "javascript"))]')[0].text_content()

        team = fixture.split(" - ")[0]

        try:
            opposition = fixture.split(" - ")[1]
        except IndexError:
            continue
        home, away, draw = get_odds(row)
        if home == 1.01 and away == 1.01:
            continue

        unfinished_games_substrings = ['postp.', 'award.', 'canc.', 'w.o.']

        if 'table-score' in row.find("td[3]").get('class'):
            if any(substr in row.find("td[3]").text_content() for substr in unfinished_games_substrings):
                continue
            else:
                match_status = 'ft'
                result = row.find("td[3]").text_content().split(":")
                try:
                    ft1, ft2 = float(result[0]), float(result[1])
                except ValueError:
                    ft1, ft2 = float(result[0]), float(
                        result[1].split('\xa0OT')[0])
                except ValueError:
                    ft1, ft2 = float(result[0]), float(
                        result[1].split('\xa0ET')[0])
        else:
            # unplayed game. Below you append the odds of the games that aren't played yet
            match_status = "pre"
            ft1, ft2 = np.nan, np.nan

        match_values = [sport, country, league, tournament_id, match_id,
                        match_utc_time, match_status, team, opposition, ft1, ft2, home, away, draw]

        data.append([x for x in match_values if x])
    return data


class Command(BaseCommand):
    help = "collect odds"
        

    # def add_arguments(self, parser):
        # import argparse
        # # parser = argparse.ArgumentParser()
        # parser.add_argument('--test', dest='test', action='store_true')
        # parser.add_argument('--remote', dest='local', action='store_false')

    # scraper logic below
    def handle(self, *args, **options):
        
        test = False


        driver = start_chromedriver()

        base_url = 'https://www.oddsportal.com/baseball/usa/mlb/'
        url_tables_to_scrape = [
            base_url] if test else build_season_urls(base_url)

        wait = WebDriverWait(driver, 5)
        xpath_result_button = '//a[contains(text(), "RESULT")]'
        xpath_first_fixture = '//table[@id="tournamentTable"]/tbody/tr[@xeid]/td[2]/a'

        for url in url_tables_to_scrape:
            # both checks if url is still valid and loads it

            driver.get(url)
            # if wait.until(lambda driver: driver.find_element_by_xpath(xpath_result_button).is_displayed() and driver.find_element_by_xpath(xpath_result_button).is_enabled() or
            #               driver.find_element_by_xpath(xpath_first_fixture).is_displayed() and driver.find_element_by_xpath(xpath_first_fixture).is_enabled()):
                

            tree = html.fromstring(driver.page_source)
            first_table_row = tree.xpath(
                '//table[@id="tournamentTable"]/tbody/tr[1]')[0]
            tournament_id = get_tournament_id(first_table_row)
            sport, country, league = get_sport_country_league(
                first_table_row)
            # datelist = tree.xpath(
            #     '//table[@id="tournamentTable"]/tbody/tr[contains(@class,"nob-border")]')

            fixtures_list = tree.xpath(
                '//table[@id="tournamentTable"]/tbody/tr[@xeid]')

            for row in fixtures_list:

                match_id = row.get("xeid")

                match_unix_time = int(row.find("td[1]").get(
                    "class").split("t")[-1].split("-")[0])
                match_utc_time = dt.datetime.utcfromtimestamp(
                    match_unix_time)

                # pre season cut off
                if match_utc_time.date() <= dt.date(2021, 3, 31):
                    return

                fixture = row.xpath(
                    'td[2]/a[not(starts-with(@href, "javascript"))]')[0].text_content()

                team = fixture.split(" - ")[0]

                try:
                    opposition = fixture.split(" - ")[1]
                except IndexError:
                    continue
                home, away, draw = get_odds(row)

                unfinished_games_substrings = [
                    'postp.', 'award.', 'canc.', 'w.o.','int.']

                if 'table-score' in row.find("td[3]").get('class'):
                    if any(substr in row.find("td[3]").text_content() for substr in unfinished_games_substrings):
                        continue
                    else:
                        match_status = 'ft'
                        result = row.find(
                            "td[3]").text_content().split(":")
                        try:
                            ft1, ft2 = float(result[0]), float(result[1])
                        except ValueError:
                            ft1, ft2 = float(result[0]), float(
                                result[1].split('\xa0OT')[0])
                        except ValueError:
                            ft1, ft2 = float(result[0]), float(
                                result[1].split('\xa0ET')[0])
                else:
                    # unplayed game. Below you append the odds of the games that aren't played yet
                    match_status = "pre"
                    ft1, ft2 = None, None

                if match_status == 'ft':

                    try:
                        # no need to add existing scraped games that are finished
                        Game.objects.get(
                            match_id=match_id, match_status='ft')
                        continue

                    except Game.DoesNotExist:
                        pass

                Game.objects.create(sport=sport, country=country, league=league, tournament_id=tournament_id, match_id=match_id,
                                    match_utc_time=match_utc_time, match_status=match_status, team=team, opposition=opposition,
                                    ft1=ft1, ft2=ft2, home_odds=home, away_odds=away, draw_odds=draw)

            self.stdout.write('url complete')
            time.sleep(10)

        stop_chromedriver(driver)
