import os
import sys
from scipy.stats import binom
import pandas as pd
from datetime import date
import multiprocessing
import argparse
from tqdm import tqdm
pd.set_option('future.no_silent_downcasting', True)

parser = argparse.ArgumentParser()
parser.add_argument("-n", "--numsimulation", dest = 'simulation_try', action = 'store', type = int, default = 20000)
parser.add_argument("-p", "--processes", dest = 'process_num', action = 'store', type = int, default = 4)
parser.add_argument("--winratio", dest = 'winratio', action = 'store', type = str, default = 'uniform')
parser.add_argument('--game_path', dest = 'game_path', action = 'store', type = str, required = True)
parser.add_argument('--probability_path', dest = 'probability_path', action = 'store', type = str, default = False)
parser.add_argument('--standing_path', dest = 'standing_path', action = 'store', type = str, default = False)
parser.add_argument('--comingup_path', dest = 'comingup_path', action = 'store', type = str, default = False)
parser.add_argument('--cli_path', dest = 'cli_path', action = 'store', type = str, default = False)
parser.add_argument('--probability_output', dest = 'probability_output', action = 'store', type = str, default = 'prob_{}.pkl'.format(date.today().isoformat()))
parser.add_argument('--standing_output', dest = 'standing_output', action = 'store', type = str, default = 'standing_{}.pkl'.format(date.today().isoformat()))
parser.add_argument('--cli_output', dest = 'cli_output', action = 'store', type = str, default = 'cli_{}.pkl'.format(date.today().isoformat()))

args = parser.parse_args()

games_df = pd.read_pickle(args.game_path)
team_list = ['KIA', '삼성', 'LG', '두산', 'KT', 'SSG', '롯데', '한화', 'NC', '키움']
initial_table = pd.DataFrame(0, index = team_list, columns = team_list)

standing_probability = pd.read_pickle(args.probability_path) if args.probability_path else pd.DataFrame(
    index = pd.MultiIndex([[],[]], [[],[]], names = ['date', 'team']),
    columns = range(1,1 + len(team_list)))
standing = pd.read_pickle(args.standing_path) if args.standing_path else pd.DataFrame(
    index = pd.MultiIndex([[],[]], [[],[]], names = ['date', 'team']),
    columns = ['승', '패', '무', '승률', '승차'])
coming = pd.read_pickle(args.comingup_path) if args.comingup_path else False
if isinstance(args.winratio, str) and os.path.isfile(args.winratio):
    win_ratio = pd.read_pickle(args.winratio)
else:
    win_ratio = pd.DataFrame(0.5, index = team_list, columns = team_list)

def log5(team_ratio: float, opponent_ratio: float) -> float:
    return team_ratio * (1-opponent_ratio) / (team_ratio * (1-opponent_ratio) + opponent_ratio * (1-team_ratio))

def season_simulation(simulation_games, win_table, draw_table, win_ratio, num_attempts = args.simulation_try // args.process_num):
    simulation_result = pd.DataFrame(0, index = team_list, columns = range(1, 11))
    for _ in range(num_attempts):
        simulation_wins = initial_table.copy()
        for idx in simulation_games.index:
            for col in simulation_games.columns[simulation_games.index.get_loc(idx)+1:]:
                simulation_wins.at[idx, col] = binom.rvs(n=simulation_games.at[idx,col], p=win_ratio.at[idx, col], size = 1)[0]
                simulation_wins.at[col, idx] = simulation_games.at[idx,col] - simulation_wins.at[idx, col]
        simulation_standing = ((simulation_wins + win_table).sum(axis = 1) / ((16 - draw_table).sum(axis = 1) - 16)).rank(method = 'min', ascending=False).astype(int)
        for idx in simulation_standing.index:
            simulation_result.at[idx, simulation_standing[idx]] += 1
    return simulation_result

if __name__ == '__main__':
    for cwp_date in tqdm(sorted([x for x in games_df['date'].drop_duplicates() if x not in set([x[0] for x in standing_probability.index])]), desc='cWP calculation'):
        # 현재 전적 산출
        win_table = initial_table.copy(deep=True)
        draw_table = initial_table.copy(deep=True)
        for k, v in games_df.loc[(games_df['date'] <= cwp_date) & (games_df['home'] == games_df['win'])].value_counts(subset = ['home', 'away']).items():
            win_table.at[k] += v
        for k, v in games_df.loc[(games_df['date'] <= cwp_date) & (games_df['away'] == games_df['win'])].value_counts(subset = ['away', 'home']).items():
            win_table.at[k] += v
        for k, v in games_df.loc[(games_df['date'] <= cwp_date) & (games_df['win'] == 'draw')].value_counts(subset=['home', 'away']).items():
            draw_table.at[k] += v
            draw_table.at[k[::-1]] += v
        simulation_games = 16 - (win_table + win_table.T + draw_table)
        # 피타고리안 기대승률 계산
        scores = pd.DataFrame(index = team_list, columns = ['run_scored', 'run_allowed'])
        for team in team_list:
            scores.loc[team] = [games_df.loc[(games_df['home'] == team) & (games_df['date'] <= cwp_date), 'home_score'].sum() + games_df.loc[(games_df['away'] == team) & (games_df['date'] <= cwp_date), 'away_score'].sum(), games_df.loc[(games_df['home'] == team) & (games_df['date'] <= cwp_date), 'away_score'].sum() + games_df.loc[(games_df['away'] == team) & (games_df['date'] <= cwp_date), 'home_score'].sum()]
        scores['기대승률'] = 1 / (1 + (scores['run_allowed'] / scores['run_scored'])**1.83)
        if args.winratio == 'pythagorean':
            for team_idx in team_list:
                for team_col in team_list[team_list.index(team_idx) + 1:]:
                    win_ratio.at[team_idx, team_col] = log5(scores.at[team_idx, '기대승률'], scores.at[team_col, '기대승률'])
                    win_ratio.at[team_col, team_idx] = 1 - win_ratio.at[team_idx, team_col]
        # 현재 순위표 작성
        if cwp_date not in standing.index:
            current_standing = pd.DataFrame([win_table.sum(axis = 1), win_table.T.sum(axis = 1), draw_table.sum(axis = 1)], index = ['승', '패', '무']).T
            current_standing['승률'] = current_standing['승'] / (current_standing['승'] + current_standing['패'])
            current_standing.sort_values('승률', ascending=False, inplace = True)
            current_standing['승차'] = [((current_standing.at[current_standing.index[0], '승'] - current_standing.at[current_standing.index[0], '패']) - (current_standing.at[following, '승'] - current_standing.at[following, '패'])) /2 if current_standing['승률'].max() != current_standing.at[following, '승률'] else pd.NA for following in current_standing.index]
            current_standing = current_standing.merge(scores['기대승률'], left_index=True, right_index=True)
            current_standing.sort_values(['승률', '승차'], ascending=[False, True], inplace = True)
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
        simulation_summary = simulation_summary.round(5)
        simulation_summary.index = pd.MultiIndex.from_tuples(list(zip(*[[cwp_date]*10, team_list])))
        standing_probability = pd.concat([standing_probability, simulation_summary])
        standing_probability.to_pickle(args.probability_output)
    # cLI 시뮬레이션 시행
    if not isinstance(coming, pd.DataFrame):
        sys.exit()
    cli = pd.read_pickle(args.cli_path) if args.cli_path else pd.DataFrame(
    index = pd.MultiIndex([[],[]], [[],[]], names = ['date', 'team']),
    columns = ['cLI', 'cWin', 'cLose', 'pLI', 'pWin', 'pLose'])
    for coming_idx in tqdm([x for x in coming.drop_duplicates(subset = ['away', 'home']).index if coming.at[x, 'date'] not in cli.index.get_level_values(0)], desc='CLI calculation'):
        win_table = initial_table.copy(deep=True)
        draw_table = initial_table.copy(deep=True)
        for k, v in games_df.loc[(games_df['date'] < coming.at[coming_idx, 'date']) & (games_df['home'] == games_df['win'])].value_counts(subset = ['home', 'away']).items():
            win_table.at[k] += v
        for k, v in games_df.loc[(games_df['date'] < coming.at[coming_idx, 'date']) & (games_df['away'] == games_df['win'])].value_counts(subset = ['away', 'home']).items():
            win_table.at[k] += v
        for k, v in games_df.loc[(games_df['date'] < coming.at[coming_idx, 'date']) & (games_df['win'] == 'draw')].value_counts(subset=['home', 'away']).items():
            draw_table.at[k] += v
            draw_table.at[k[::-1]] += v
        # 홈팀이 승리한 경우
        win_if_homewin = win_table.copy()
        win_if_homewin.at[coming.at[coming_idx, 'home'], coming.at[coming_idx, 'away']] += 1
        pool = multiprocessing.Pool(processes = args.process_num)
        output_list = pool.starmap(season_simulation, [(16 - (win_if_homewin + win_if_homewin.T + draw_table), win_if_homewin, draw_table, win_ratio, args.simulation_try // args.process_num)] * args.process_num)
        pool.close()
        pool.join()
        homewin_simulation_summary = sum(output_list) / args.simulation_try
        # 원정팀이 승리한 경우
        win_if_awaywin = win_table.copy()
        win_if_awaywin.at[coming.at[coming_idx, 'away'], coming.at[coming_idx, 'home']] += 1
        pool = multiprocessing.Pool(processes = args.process_num)
        output_list = pool.starmap(season_simulation, [(16 - (win_if_awaywin + win_if_awaywin.T + draw_table), win_if_awaywin, draw_table, win_ratio, args.simulation_try // args.process_num)] * args.process_num)
        pool.close()
        pool.join()
        awaywin_simulation_summary = sum(output_list) / args.simulation_try
        # cLI 계산
        cli.at[(coming.at[coming_idx, 'date'], coming.at[coming_idx, 'home']), 'cWin'] = homewin_simulation_summary.at[coming.at[coming_idx, 'home'], 1]
        cli.at[(coming.at[coming_idx, 'date'], coming.at[coming_idx, 'home']), 'cLose'] = awaywin_simulation_summary.at[coming.at[coming_idx, 'home'], 1]
        cli.at[(coming.at[coming_idx, 'date'], coming.at[coming_idx, 'away']), 'cWin'] = awaywin_simulation_summary.at[coming.at[coming_idx, 'away'], 1]
        cli.at[(coming.at[coming_idx, 'date'], coming.at[coming_idx, 'away']), 'cLose'] = homewin_simulation_summary.at[coming.at[coming_idx, 'away'], 1]
        cli.at[(coming.at[coming_idx, 'date'], coming.at[coming_idx, 'home']), 'pWin'] = homewin_simulation_summary.loc[coming.at[coming_idx, 'home'], :5].sum()
        cli.at[(coming.at[coming_idx, 'date'], coming.at[coming_idx, 'home']), 'pLose'] = awaywin_simulation_summary.loc[coming.at[coming_idx, 'home'], :5].sum()
        cli.at[(coming.at[coming_idx, 'date'], coming.at[coming_idx, 'away']), 'pWin'] = awaywin_simulation_summary.loc[coming.at[coming_idx, 'away'], :5].sum()
        cli.at[(coming.at[coming_idx, 'date'], coming.at[coming_idx, 'away']), 'pLose'] = homewin_simulation_summary.loc[coming.at[coming_idx, 'away'], :5].sum()

        cli['cLI'] = (cli['cWin'] - cli['cLose']) / 0.02954
        cli['pLI'] = (cli['pWin'] - cli['pLose']) / 0.06363
    cli.to_pickle(args.cli_output)