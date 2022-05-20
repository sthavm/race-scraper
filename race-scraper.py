from flask import Flask, request, jsonify
from flask_cors import CORS
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import os

RACE_RESULTS_URL = "https://racing.hkjc.com/racing/information/english/Racing/LocalResults.aspx?"
CHROMEDRIVER_PATH = os.environ.get("CHROMEDRIVER_PATH")
GOOGLE_CHROME_BIN = os.environ.get("GOOGLE_CHROME_BIN")
app = Flask(__name__)

CORS(app)

@app.route("/race-results")
def return_race_results():
    race_date = request.args.get('race-date')
    race_no = request.args.get('race-no')
    race_results = get_race_results(race_date, race_no)
    if race_results == 'date invalid':
        return 'date invalid', 200
    elif race_results == 'race invalid':
        return 'race invalid', 200
    profit = calculate_profit(race_results)
    results_dict = {"dividend_table":race_results, "profit":profit}
    return jsonify(results_dict), 200

@app.route("/")
def home():
    return "<h2>Hello</h2>"

def get_race_results(race_date, race_no):
    specific_url = RACE_RESULTS_URL + '&RaceDate='+ str(race_date) + '&RaceNo='+str(race_no)
    options = Options()
    options.add_argument("--headless")
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-sandbox')
    options.binary_location = GOOGLE_CHROME_BIN
    driver = webdriver.Chrome(executable_path =CHROMEDRIVER_PATH, options=options)
    driver.get(specific_url)
    try:
        element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "commContent")))
    finally:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        driver.quit()
    local_results = soup.find("div", class_="localResults")
    performance = soup.find("div", class_="performance")
    if local_results == None:
        return "date invalid"
    elif performance == None:
        return "race invalid"
    dividend_table = soup.find("div", class_='dividend_tab').find("table")
    return extract_dividend_data(dividend_table)

def extract_dividend_data(table):
    results_and_dividends = {}
    rows = table.tbody.find_all("tr")

    win_data = rows[0].find_all("td")
    results_and_dividends["win"] = (win_data[1].text, win_data[2].text)

    winning_place_bets = []
    for i in range(1,4):
        place_data = rows[i].find_all("td")
        if i == 1:
            winning_place_bets.append((place_data[1].text, place_data[2].text))
        else:
            winning_place_bets.append((place_data[0].text, place_data[1].text))
    results_and_dividends["place"] = winning_place_bets

    quinella_data = rows[4].find_all("td")
    results_and_dividends["quinella"] = (quinella_data[1].text, quinella_data[2].text)

    winning_quinella_place_bets = []
    for i in range(5,8):
        quinella_place_data = rows[i].find_all("td")
        if i == 5:
            winning_quinella_place_bets.append((quinella_place_data[1].text,quinella_place_data[2].text))
        else:
            winning_quinella_place_bets.append((quinella_place_data[0].text, quinella_place_data[1].text))
    results_and_dividends["quinella-place"] = winning_quinella_place_bets

    winning_composite_bets = []
    for i in range(8,11):
        composite_data = rows[i].find_all("td")
        if i == 8:
            winning_composite_bets.append((composite_data[1].text, composite_data[2].text))
        else:
            winning_composite_bets.append((composite_data[0].text, composite_data[1].text))
    results_and_dividends["composite"] = winning_composite_bets

    forecast_data = rows[12].find_all("td")
    results_and_dividends["forecast"] = (forecast_data[1].text, forecast_data[2].text)

    tierce_data = rows[13].find_all("td")
    results_and_dividends["tierce"] = (tierce_data[1].text, tierce_data[2].text)

    results_and_dividends["trio"] = (results_and_dividends["tierce"][0], rows[14].find_all("td")[2].text)

    first_4_data = rows[15].find_all("td")
    results_and_dividends["first-4"] = (first_4_data[1].text, first_4_data[2].text)

    quartet_data = rows[16].find_all("td")
    results_and_dividends["quartet"] = (quartet_data[1].text, quartet_data[2].text)

    winning_1st_double_bets = []
    for i in range(17, 19):
        _1st_double_data = rows[i].find_all("td")
        if i == 17:
            winning_1st_double_bets.append((_1st_double_data[1].text, _1st_double_data[2].text))
        else:
            winning_1st_double_bets.append((_1st_double_data[0].text, _1st_double_data[1].text))
    results_and_dividends["1st-double"] = winning_1st_double_bets

    return results_and_dividends

def calculate_profit(results_and_dividends):
    f = open('bet-list.json')
    bets = json.load(f)["bets"]
    quinella_profits = calculate_quinella_profits(bets["qin"], results_and_dividends["quinella"])
    quinella_place_profits = calculate_quinella_place_profits(bets["qpl"], results_and_dividends["quinella-place"])
    return quinella_profits+quinella_place_profits

def calculate_quinella_profits(quinella_bets, quinella_dividends):
    quinella_win_configurations = (quinella_dividends[0], quinella_dividends[0].split(',')[1]+','+quinella_dividends[0].split(',')[0])

    bet_profits = []

    for bet in quinella_bets:
        bet_profit = {"bet_type": "quinella", "combination":bet, "amount":quinella_bets[bet]}
        if (quinella_win_configurations[0] == bet or quinella_win_configurations[1] == bet):
            bet_profit["dividend"] = float(quinella_dividends[1])
            bet_profit["profit"] = (bet_profit["amount"]/10) * bet_profit["dividend"] - bet_profit["amount"]
        else:
            bet_profit["dividend"] = 0
            bet_profit["profit"] = -1 * bet_profit["amount"]
        bet_profits.append(bet_profit)
    return bet_profits


def calculate_quinella_place_profits(quinella_place_bets, quinella_place_dividends):
    quinella_place_win_configurations = {}
    for dividend in quinella_place_dividends:
        quinella_place_win_configurations[dividend[0]] = dividend[1]
        quinella_place_win_configurations[dividend[0].split(',')[1]+','+dividend[0].split(',')[0]] = dividend[1]

    bet_profits = []
    for bet in quinella_place_bets:
        bet_profit = {"bet_type": "quinella-place", "combination":bet, "amount":quinella_place_bets[bet]}
        if bet in quinella_place_win_configurations:
            bet_profit["dividend"] = float(quinella_place_win_configurations[bet].replace(',',''))
            bet_profit["profit"] = (bet_profit["amount"]/10) * bet_profit["dividend"] - bet_profit["amount"]
        else:
            bet_profit["dividend"] = 0
            bet_profit["profit"] = -1 * bet_profit["amount"]
        bet_profits.append(bet_profit)
    return bet_profits
    

if __name__ == "__main__":
  app.run()

