import plotly.graph_objects as go
from plotly.io import write_json
import pandas as pd
from datetime import date, timedelta

team_color = {
    'LG':['#C30452', '#000000'],
    'KT':['#000000', '#EB1C24'],
    'SSG':['#CE0E2D', '#ffb81c'],
    'NC':['#315288', '#AF917B'],
    '두산':['#131230', '#FFFFFF'],
    'KIA':['#EA0029', '#06141F'],
    '롯데':['#041E42', '#D00F31'],
    '삼성':['#074CA1', '#C0C0C0'],
    '한화':['#FF6600', '#000000'],
    '키움':['#570514', '#B07F4A']
}

uniform_result = pd.read_pickle('data/2023/2023_uniform_prob.pkl')
log5_result = pd.read_pickle('data/2023/2023_log5_prob.pkl')
coming_li = pd.read_pickle('data/li.pkl')
standing = pd.read_pickle('data/2023/2023_standing.pkl')
coming = pd.read_pickle('data/comingup_games.pkl')

days_list = sorted(uniform_result.index.get_level_values(0).drop_duplicates())

now_championship_fig = go.Figure(layout = go.Layout(hovermode='x'))
now_postseason_fig = go.Figure(layout = go.Layout(hovermode='x'))
now_championship_fig.update_xaxes(title_text = '날짜', range = [days_list[0], days_list[-1]])
now_postseason_fig.update_xaxes(title_text = '날짜', range = [days_list[0], days_list[-1]])
now_championship_fig.update_yaxes(title_text = '확률', range = [0, 1], fixedrange = True)
now_postseason_fig.update_yaxes(title_text = '확률', range = [0, 1], fixedrange = True)
now_championship_fig.update_layout(title_text = 'KBO 팀별 우승확률')
now_postseason_fig.update_layout(title_text = 'KBO 팀별 포스트시즌 진출확률')
for team, color in team_color.items():
    now_championship_fig.add_trace(go.Scatter(x=days_list, y = uniform_result.xs(team, level = 1)[1], name = team, mode = 'lines+markers', line = {'color': color[0]}, marker = {'color': color[1], 'size': 3}))
    now_postseason_fig.add_trace(go.Scatter(x=days_list, y = uniform_result.xs(team, level = 1).loc[:, 1:5].sum(axis = 1), name = team, mode = 'lines+markers', line = {'color': color[0]}, marker = {'color': color[1], 'size': 3}))

last_result = uniform_result.loc[:max([x for x in days_list if x < coming_li.index.get_level_values(0).max()])]
future_championship_fig = go.Figure(layout = go.Layout(hovermode='x'))
future_championship_fig.update_xaxes(title_text = '날짜', range = [[x for x in days_list if x < coming_li.index.get_level_values(0).max()][-6], coming_li.index.get_level_values(0).max()], fixedrange = True)
future_championship_fig.update_yaxes(title_text = '확률', range = [0, 1], fixedrange = True)
future_postseason_fig = go.Figure(layout = go.Layout(hovermode='x'))
future_postseason_fig.update_xaxes(title_text = '날짜', range = [[x for x in days_list if x < coming_li.index.get_level_values(0).max()][-6], coming_li.index.get_level_values(0).max()], fixedrange = True)
future_postseason_fig.update_yaxes(title_text = '확률', range = [0, 1], fixedrange = True)
future_championship_fig.update_layout(title_text = '2023 시즌 KBO 팀별 우승 확률 예측')
future_postseason_fig.update_layout(title_text = '2023 시즌 KBO 팀별 포스트시즌 진출 확률 예측')

for team, color in team_color.items():
    future_championship_fig.add_trace(go.Scatter(
        x=last_result.index.get_level_values(0).drop_duplicates(),
        y = last_result.xs(team, level = 1)[1],
        name = team, mode = 'lines+markers',
        line = {'color': color[0]}, marker = {'color': color[1], 'size': 3}))
    if team in coming_li.loc[coming_li.index.get_level_values(0).max()].index:
        future_championship_fig.add_trace(go.Scatter(
            x=[last_result.index.get_level_values(0).max(), coming_li.index.get_level_values(0).max()],
            y = [last_result.loc[(last_result.index.get_level_values(0).max(), team), 1], coming_li.xs(team, level = 1)['cWin'].iloc[-1]],
            mode = 'lines+text', line = {'color': color[0], 'dash': 'dash'}, marker = {'color': color[1], 'size': 3}, showlegend=False, hoverinfo='skip',
            text=['', round(coming_li.xs(team, level = 1)['cWin'].iloc[-1], 3) if coming_li.xs(team, level = 1)['cLI'].iloc[-1] > 1 else ''], textposition='top left'))
        future_championship_fig.add_trace(go.Scatter(
            x=[last_result.index.get_level_values(0).max(), coming_li.index.get_level_values(0).max()],
            y = [last_result.loc[(last_result.index.get_level_values(0).max(), team), 1], coming_li.xs(team, level = 1)['cLose'].iloc[-1]],
            mode = 'lines+text', line = {'color': color[0], 'dash': 'dash'}, marker = {'color': color[1], 'size': 3}, showlegend=False, hoverinfo='skip',
            text=['', round(coming_li.xs(team, level = 1)['cLose'].iloc[-1], 3) if coming_li.xs(team, level = 1)['cLI'].iloc[-1] > 1 else ''], textposition='bottom left'))

    future_postseason_fig.add_trace(go.Scatter(
        x=last_result.index.get_level_values(0).drop_duplicates(),
        y = last_result.xs(team, level = 1).loc[:, 1:5].sum(axis = 1),
        name = team, mode = 'lines+markers',
        line = {'color': color[0]}, marker = {'color': color[1], 'size': 3}))
    if team in coming_li.loc[coming_li.index.get_level_values(0).max()].index:
        future_postseason_fig.add_trace(go.Scatter(
            x=[last_result.index.get_level_values(0).max(), coming_li.index.get_level_values(0).max()],
            y = [last_result.loc[(last_result.index.get_level_values(0).max(), team), 1:5].sum(), coming_li.xs(team, level = 1)['pWin'].iloc[-1]],
            mode = 'lines+text', line = {'color': color[0], 'dash': 'dash'}, marker = {'color': color[1], 'size': 3}, showlegend=False, hoverinfo='skip',
            text=['', round(coming_li.xs(team, level = 1)['pWin'].iloc[-1], 3) if coming_li.xs(team, level = 1)['pLI'].iloc[-1] > 1 else ''], textposition='top left'))
        future_postseason_fig.add_trace(go.Scatter(
            x=[last_result.index.get_level_values(0).max(), coming_li.index.get_level_values(0).max()],
            y = [last_result.loc[(last_result.index.get_level_values(0).max(), team), 1:5].sum(), coming_li.xs(team, level = 1)['pLose'].iloc[-1]],
            mode = 'lines+text', line = {'color': color[0], 'dash': 'dash'}, marker = {'color': color[1], 'size': 3}, showlegend=False, hoverinfo='skip',
            text=['', round(coming_li.xs(team, level = 1)['pLose'].iloc[-1], 3) if coming_li.xs(team, level = 1)['pLI'].iloc[-1] > 1 else ''], textposition='bottom left'))

write_json(now_championship_fig, file = 'data/now_championship_fig.json', engine = 'json')
write_json(now_postseason_fig, file = 'data/now_postseason_fig.json', engine = 'json')
write_json(future_championship_fig, file = 'data/future_championship_fig.json', engine = 'json')
write_json(future_postseason_fig, file = 'data/future_postseason_fig.json', engine = 'json')