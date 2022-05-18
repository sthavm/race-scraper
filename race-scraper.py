from flask import Flask, request, jsonify
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

RACE_RESULTS_URL = "https://racing.hkjc.com/racing/information/english/Racing/LocalResults.aspx?Racecourse=HV"
app = Flask(__name__)

@app.route("/race-results")
def return_race_results():
    race_date = request.args.get('race-date')
    race_no = request.args.get('race-no')
    race_results = get_race_results(race_date, race_no)
    if race_results == 'date invalid':
        return 'date invalid', 204
    elif race_results == 'race invalid':
        return 'race invalid', 204
    return jsonify(race_results), 200


def get_race_results(race_date, race_no):
    specific_url = RACE_RESULTS_URL + '&RaceDate='+ str(race_date) + '&RaceNo='+str(race_no)
    options = Options()
    options.add_argument("--headless")
    options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(executable_path = './chromedriver', options=options)
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



print(get_race_results('2021/12/08',2))