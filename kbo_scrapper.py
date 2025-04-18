from selenium import webdriver
from selenium.webdriver.common.by import By
import platform
from datetime import date, timedelta, datetime, time, timezone
import pandas as pd
import time
import sys

if pd.read_pickle('data/comingup_games.pkl')['date'].iloc[0] > date.today():
    sys.exit()

game_df = pd.read_pickle('data/completed_games.pkl')
if 'Linux' == platform.system():
    from webdriver_manager.firefox import GeckoDriverManager
    from selenium.webdriver.firefox.service import Service
    from selenium.webdriver.firefox.options import Options
    options = Options()
    options.add_argument('--headless')
    driver = webdriver.Firefox(service = Service(GeckoDriverManager().install()), options=options)
else:
    from webdriver_manager.microsoft import EdgeChromiumDriverManager
    from selenium.webdriver.edge.service import Service
    from selenium.webdriver.edge.options import Options
    options = Options()
    options.add_argument('--edge-skip-compat-layer-relaunch')
    driver = webdriver.Edge(service = Service(EdgeChromiumDriverManager().install()), options=options)

driver.implicitly_wait(3)
action = webdriver.ActionChains(driver)
driver.get('https://www.koreabaseball.com/Schedule/GameCenter/Main.aspx')

for coming_day in [date.today() + timedelta(days=x) for x in range(0, 8)]:
    driver.execute_script("getGameDate('{}');".format(coming_day))
    time.sleep(0.3)
    coming_up = pd.DataFrame([[date.fromisoformat(x.get_attribute('g_dt')), x.get_attribute('away_nm'), x.get_attribute('home_nm')] for x in driver.find_elements(By.XPATH, '//li[@class="game-cont"]')], columns = ['date', 'away', 'home'])
    if len(coming_up):
        break

# 진행 중인 경기는 game-cont ing, 끝난 경기는 game-cont end, 취소된 경기는 game-cont cancel
last_gameday = game_df['date'].max() if isinstance(game_df['date'].max(), date) else date.today() - timedelta(days=1)
for current in [last_gameday + timedelta(days=x) for x in range(1, int((date.today() - last_gameday).days) + 1)]:
    driver.execute_script("getGameDate('{}');".format(current.strftime('%Y%m%d')))
    if current != date.fromisoformat(driver.find_element(By.CLASS_NAME, 'date-txt').text[:-3].replace('.', '-')):
        continue
    game_df = pd.concat([game_df, pd.DataFrame([[date.fromisoformat(x.get_attribute('g_dt')), x.get_attribute('away_nm'), x.get_attribute('home_nm'), int(x.find_element(By.XPATH, './/div[@class="team away"]/div[contains(@class, "score")]').get_attribute('innerText')), int(x.find_element(By.XPATH, './/div[@class="team home"]/div[contains(@class, "score")]').get_attribute('innerText')), x.find_element(By.XPATH, './/div[@class="score win"]/preceding-sibling::div[@class="emb"]/img').get_attribute('alt') if x.find_elements(By.CLASS_NAME, 'win') else 'draw'] for x in driver.find_elements(By.XPATH, '//li[@class="game-cont end"]') if x.get_attribute('away_nm') not in ['나눔', '드림']], columns = game_df.columns)])

game_df.reset_index(drop = True).to_pickle('data/completed_games.pkl')
coming_up.to_pickle('data/comingup_games.pkl')