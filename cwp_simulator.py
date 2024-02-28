#%%
import os
import sys
from scipy.stats import bernoulli
import pandas as pd
from datetime import date, timedelta
import multiprocessing
import argparse
from tqdm import tqdm
pd.set_option('future.no_silent_downcasting', True)

#%%
parser = argparse.ArgumentParser()
parser.add_argument("-n", "--numsimulation", dest = 'simulation_try', action = 'store', type = int, default = 25000)
parser.add_argument("-p", "--processes", dest = 'process_num', action = 'store', type = int, default = 4)
parser.add_argument("--winratio", dest = 'winratio', action = 'store', type = str, default = 'uniform')
parser.add_argument('--game_path', dest = 'game_path', action = 'store', type = str, required = True)
parser.add_argument('--probability_path', dest = 'probability_path', action = 'store', type = str, default = False)
parser.add_argument('--standing_path', dest = 'standing_path', action = 'store', type = str, default = False)
parser.add_argument('--comingup_path', dest = 'comingup_path', action = 'store', type = str, default = False)
parser.add_argument('--probability_output', dest = 'probability_output', action = 'store', type = str, default = 'prob_{}.pkl'.format(date.today().isoformat()))
parser.add_argument('--standing_output', dest = 'standing_output', action = 'store', type = str, default = 'standing_{}.pkl'.format(date.today().isoformat()))
parser.add_argument('--cli_output', dest = 'cli_output', action = 'store', type = str, default = 'cli_{}.pkl'.format(date.today().isoformat()))

args = parser.parse_args()

games_df = pd.read_pickle(args.game_path)
team_list = [x for x in games_df['home'].drop_duplicates().tolist() if x not in ['드림', '나눔']]
initial_table = pd.DataFrame(0, index = team_list, columns = team_list)

standing_probability = pd.read_pickle(args.probability_path) if args.probability_path else pd.DataFrame(
    index = pd.MultiIndex([[], []], [[],[]], names = ['date', 'team']),
    columns = range(1,1 + len(team_list)))
standing = pd.read_pickle(args.standing_path) if args.standing_path else pd.DataFrame(
    index = pd.MultiIndex([[], []], [[],[]], names = ['date', 'team']),
    columns = ['승', '패', '무', '승률', '승차'])
coming = pd.read_pickle(args.comingup_path) if args.comingup_path else False
if isinstance(args.winratio, str) and os.path.isfile(args.winratio):
    win_ratio = pd.read_pickle(args.winratio)
else:
    win_ratio = pd.DataFrame(0.5, index = team_list, columns = team_list)

#%%
def log5(team_ratio: float, opponent_ratio: float) -> float:
    return team_ratio * (1-opponent_ratio) / (team_ratio * (1-opponent_ratio) + opponent_ratio * (1-team_ratio))

def season_simulation(simulation_games, win_table, draw_table, win_ratio, num_attempts = args.simulation_try // args.process_num):
    simulation_result = pd.DataFrame(0, index = team_list, columns = range(1, 11))
    for _ in range(num_attempts):
        simulation_wins = initial_table.copy()
        for idx in simulation_games.index:
            for col in simulation_games.columns[simulation_games.index.get_loc(idx)+1:]:
                simulation_wins.loc[idx, col] = sum(bernoulli.rvs(size=simulation_games.loc[idx,col], p=win_ratio.loc[idx, col]).astype(bool))
                simulation_wins.loc[col, idx] = simulation_games.loc[idx,col] - simulation_wins.loc[idx, col]
        simulation_standing = ((simulation_wins + win_table).sum(axis = 1) / ((16 - draw_table).sum(axis = 1) - 16)).rank(method = 'min', ascending=False).astype(int)
        for idx in simulation_standing.index:
            simulation_result.loc[idx, simulation_standing[idx]] += 1
    return simulation_result

# %%
if __name__ == '__main__':
    for cwp_date in tqdm(sorted([x for x in games_df['date'].drop_duplicates() if x not in set([x[0] for x in standing_probability.index])])):
        # 현재 전적 산출
        win_table = initial_table.copy(deep=True)
        draw_table = initial_table.copy(deep=True)
        for idx in games_df.loc[games_df['date'] <= cwp_date].index:
            if games_df.loc[idx, 'win'] == 'draw':
                draw_table.loc[games_df.loc[idx, 'home'], games_df.loc[idx, 'away']] += 1
                draw_table.loc[games_df.loc[idx, 'away'], games_df.loc[idx, 'home']] += 1
            else:
                opposite = games_df.loc[idx, 'home'] if games_df.loc[idx, 'home'] != games_df.loc[idx, 'win'] else games_df.loc[idx, 'away']
                win_table.loc[games_df.loc[idx, 'win'], opposite] += 1
        simulation_games = 16 - (win_table + win_table.T + draw_table)
        # 현재 순위표 작성
        if cwp_date not in standing.index:
            current_standing = pd.DataFrame([win_table.sum(axis = 1), win_table.T.sum(axis = 1), draw_table.sum(axis = 1)], index = ['승', '패', '무']).T
            current_standing['승률'] = current_standing['승'] / (current_standing['승'] + current_standing['패'])
            current_standing.sort_values('승률', ascending=False, inplace = True)
            current_standing['승차'] = [pd.NA] + [((current_standing.loc[current_standing.index[0], '승'] - current_standing.loc[current_standing.index[0], '패']) - (current_standing.loc[following, '승'] - current_standing.loc[following, '패'])) /2 for following in current_standing.index[1:]]
            current_standing.index = pd.MultiIndex.from_tuples(zip([cwp_date] * 10 , current_standing.index))
            standing = pd.concat([standing, current_standing])
            standing.to_pickle(args.standing_output)
        # 시뮬레이션 시행
        pool = multiprocessing.Pool(processes = args.process_num)
        output_list = pool.starmap(season_simulation, [(simulation_games, win_table, draw_table, win_ratio, args.simulation_try // args.process_num)] * args.process_num)
        pool.close()
        pool.join()
        simulation_summary = sum(output_list) / args.simulation_try
        # 시뮬레이션 결과 저장
        simulation_summary.index = pd.MultiIndex.from_tuples(zip([cwp_date] * 10, simulation_summary.index))
        standing_probability = pd.concat([standing_probability, simulation_summary])
        standing_probability.to_pickle(args.probability_output)
    # cLI 시뮬레이션 시행
    if not isinstance(coming, pd.DataFrame):
        sys.exit()
    cli = pd.DataFrame(columns = ['date', 'cLI', 'cWin', 'cLose', 'pLI', 'pWin', 'pLose'])
    for coming_idx in coming.index:
        win_table = initial_table.copy(deep=True)
        draw_table = initial_table.copy(deep=True)
        for idx in games_df.loc[games_df['date'] < coming.loc[coming_idx, 'date']].index:
            if games_df.loc[idx, 'win'] == 'draw':
                draw_table.loc[games_df.loc[idx, 'home'], games_df.loc[idx, 'away']] += 1
                draw_table.loc[games_df.loc[idx, 'away'], games_df.loc[idx, 'home']] += 1
            else:
                opposite = games_df.loc[idx, 'home'] if games_df.loc[idx, 'home'] != games_df.loc[idx, 'win'] else games_df.loc[idx, 'away']
                win_table.loc[games_df.loc[idx, 'win'], opposite] += 1
        # 홈팀이 승리한 경우
        win_if_homewin = win_table.copy()
        win_if_homewin.loc[coming.loc[coming_idx, 'home'], coming.loc[coming_idx, 'away']] += 1
        pool = multiprocessing.Pool(processes = args.process_num)
        output_list = pool.starmap(season_simulation, [(16 - (win_if_homewin + win_if_homewin.T + draw_table), win_if_homewin, draw_table, win_ratio, args.simulation_try // args.process_num)] * args.process_num)
        pool.close()
        pool.join()
        homewin_simulation_summary = sum(output_list) / args.simulation_try
        # 원정팀이 승리한 경우
        pool = multiprocessing.Pool(processes = args.process_num)
        output_list = pool.starmap(season_simulation, [(16 - (win_if_homewin.T + win_if_homewin + draw_table), win_if_homewin.T, draw_table, win_ratio, args.simulation_try // args.process_num)] * args.process_num)
        pool.close()
        pool.join()
        awaywin_simulation_summary = sum(output_list) / args.simulation_try
        # cLI 계산
        cli.loc[coming.loc[coming_idx, 'home'], 'cWin'] = homewin_simulation_summary.loc[coming.loc[coming_idx, 'home'], 1]
        cli.loc[coming.loc[coming_idx, 'home'], 'cLose'] = awaywin_simulation_summary.loc[coming.loc[coming_idx, 'home'], 1]
        cli.loc[coming.loc[coming_idx, 'away'], 'cWin'] = awaywin_simulation_summary.loc[coming.loc[coming_idx, 'away'], 1]
        cli.loc[coming.loc[coming_idx, 'away'], 'cLose'] = homewin_simulation_summary.loc[coming.loc[coming_idx, 'away'], 1]
        cli.loc[coming.loc[coming_idx, 'home'], 'pWin'] = homewin_simulation_summary.loc[coming.loc[coming_idx, 'home'], :5].sum()
        cli.loc[coming.loc[coming_idx, 'home'], 'pLose'] = awaywin_simulation_summary.loc[coming.loc[coming_idx, 'home'], :5].sum()
        cli.loc[coming.loc[coming_idx, 'away'], 'pWin'] = awaywin_simulation_summary.loc[coming.loc[coming_idx, 'away'], :5].sum()
        cli.loc[coming.loc[coming_idx, 'away'], 'pLose'] = homewin_simulation_summary.loc[coming.loc[coming_idx, 'away'], :5].sum()
        cli.loc[coming.loc[coming_idx, ['away', 'home']].tolist(), 'date'] = coming.loc[coming_idx, 'date']

        cli['cLI'] = (cli['cWin'] - cli['cLose']) / 0.02954
        cli['pLI'] = (cli['pWin'] - cli['pLose']) / 0.06363
    cli.to_pickle(args.cli_output)