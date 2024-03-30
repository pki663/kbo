from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd
from datetime import date, timedelta
import time

completed_games = pd.read_pickle('data/completed_games.pkl')
comingup_games = pd.read_pickle('data/comingup_games.pkl')
comingup_games['win'] = ''

canceled = []
for idx in comingup_games.index:
    answer = ''
    while answer not in [comingup_games.at[idx, 'away'], comingup_games.at[idx, 'home'], 'draw', 'canceled']:
        answer = input('Which team won? Away({away})? Home({home})?, draw? or canceled?)'.format(away = comingup_games.at[idx, 'away'], home = comingup_games.at[idx, 'home']))
    if answer != 'canceled':
        comingup_games.at[idx, 'win'] = answer
    else: canceled.append(idx)
comingup_games.drop(canceled, inplace = True)

completed_games = pd.concat([completed_games, comingup_games], ignore_index = True)

from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
options = Options()
driver = webdriver.Edge(service = Service(EdgeChromiumDriverManager().install()), options=options)
driver.implicitly_wait(3)
action = webdriver.ActionChains(driver)
driver.get('https://www.koreabaseball.com/Schedule/GameCenter/Main.aspx')

for coming_day in [comingup_games.iloc[0,0] + timedelta(days=x) for x in range(1, 8)]:
    driver.execute_script("getGameDate('{}');".format(coming_day))
    time.sleep(0.3)
    coming_up = pd.DataFrame([[date.fromisoformat(x.get_attribute('g_dt')), x.get_attribute('away_nm'), x.get_attribute('home_nm')] for x in driver.find_elements(By.XPATH, '//li[@class="game-cont"]')], columns = ['date', 'away', 'home'])
    if len(coming_up):
        break
coming_up.to_pickle('data/comingup_games.pkl')
completed_games.to_pickle('data/completed_games.pkl')