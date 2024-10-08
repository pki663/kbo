import plotly.graph_objects as go
from plotly.io import write_json, read_json
import pandas as pd
from datetime import date, timedelta
from dash import dash_table
from dash.dash_table.Format import Format, Scheme
import pickle
import sys
import math
import os

team_color = {
    'LG':['#C30452', '#000000'],
    'KT':['#000000', '#EB1C24'],
    'SSG':['#ffb81c', '#CE0E2D'],
    'NC':['#c7a079', '#071d3d'],
    '두산':['#FFFFFF', '#131230'],
    'KIA':['#EA0029', '#06141F'],
    '롯데':['#6CACE4', '#D00F31'],
    '삼성':['#C0C0C0', '#074CA1'],
    '한화':['#f37321', '#25282a'],
    '키움':['#570514', '#B07F4A']
}

uniform_result = pd.read_pickle('data/uniform_probability.pkl')
log5_result = pd.read_pickle('data/log5_probability.pkl')
pythagorean_result = pd.read_pickle('data/pythagorean_probability.pkl')
coming_li = pd.read_pickle('data/li.pkl')
standing = pd.read_pickle('data/standing.pkl')
coming = pd.read_pickle('data/comingup_games.pkl')

days_list = sorted(uniform_result.index.get_level_values(0).drop_duplicates())

if os.path.isfile('fig/now_championship_fig.json'):
    prev = read_json(file = 'fig/now_championship_fig.json', engine = 'json')
    if prev.layout.xaxis.range[-1] == days_list[-1].isoformat():
        sys.exit(0)

now_championship_fig = go.Figure(layout = go.Layout(hovermode='x'))
now_postseason_fig = go.Figure(layout = go.Layout(hovermode='x'))
# if want rangeslider, add rangeslider = {'range' : [days_list[0], days_list[-1]]}
now_championship_fig.update_xaxes(title_text = '날짜', range = [min(days_list[0], days_list[-1] - timedelta(days = 7)), days_list[-1]], minallowed = min(days_list[0], days_list[-1] - timedelta(days = 7)), maxallowed = days_list[-1])
now_postseason_fig.update_xaxes(title_text = '날짜', range = [min(days_list[0], days_list[-1] - timedelta(days = 7)), days_list[-1]], minallowed = min(days_list[0], days_list[-1] - timedelta(days = 7)), maxallowed = days_list[-1])
now_championship_fig.update_yaxes(title_text = '확률', range = [max(0, math.floor(uniform_result.loc[:, 1].min() * 10) / 10), min(1, math.ceil(uniform_result.loc[:, 1].max() * 10) / 10)], fixedrange = True, tickformat = ',.2%')
now_postseason_fig.update_yaxes(title_text = '확률', range = [max(0, math.floor(uniform_result.loc[:, 1:5].sum(axis = 1).min() * 10) / 10), min(1, math.ceil(uniform_result.loc[:, 1:5].sum(axis = 1).max() * 10) / 10)], fixedrange = True, tickformat = ',.2%')
now_championship_fig.update_layout(title_text = 'KBO 팀별 우승확률', margin_l=10, margin_r=10, margin_b=10, margin_t=50, dragmode = 'pan', plot_bgcolor='#D9F2D0', paper_bgcolor="#DFDFDF")
now_postseason_fig.update_layout(title_text = 'KBO 팀별 포스트시즌 진출확률', margin_l=10, margin_r=10, margin_b=10, margin_t=50, dragmode = 'pan', plot_bgcolor='#D9F2D0', paper_bgcolor="#DFDFDF")
for team, color in team_color.items():
    now_championship_fig.add_trace(go.Scatter(x=days_list, y = uniform_result.xs(team, level = 1)[1], name = team, mode = 'lines+markers', line = {'color': color[0], 'width' : 3}, marker = {'color': color[1], 'size': 3}, hoverlabel = {'bgcolor': color[0], 'font_color': color[1]}))
    now_postseason_fig.add_trace(go.Scatter(x=days_list, y = uniform_result.xs(team, level = 1).loc[:, 1:5].sum(axis = 1), name = team, mode = 'lines+markers', line = {'color': color[0], 'width' : 3}, marker = {'color': color[1], 'size': 3}, hoverlabel = {'bgcolor': color[0], 'font_color': color[1]}))

log5_championship_fig = go.Figure(layout = go.Layout(hovermode='x'))
log5_postseason_fig = go.Figure(layout = go.Layout(hovermode='x'))
# if want rangeslider, add rangeslider = {'range' : [days_list[0], days_list[-1]]}
log5_championship_fig.update_xaxes(title_text = '날짜', range = [min(days_list[0], days_list[-1] - timedelta(days = 7)), days_list[-1]], minallowed = min(days_list[0], days_list[-1] - timedelta(days = 7)), maxallowed = days_list[-1])
log5_postseason_fig.update_xaxes(title_text = '날짜', range = [min(days_list[0], days_list[-1] - timedelta(days = 7)), days_list[-1]], minallowed = min(days_list[0], days_list[-1] - timedelta(days = 7)), maxallowed = days_list[-1])
log5_championship_fig.update_yaxes(title_text = '확률', range = [max(0, math.floor(log5_result.loc[:, 1].min() * 10) / 10), min(1, math.ceil(log5_result.loc[:, 1].max() * 10) / 10)], fixedrange = True, tickformat = ',.3%')
log5_postseason_fig.update_yaxes(title_text = '확률', range = [max(0, math.floor(log5_result.loc[:, 1:5].sum(axis = 1).min() * 10) / 10), min(1, math.ceil(log5_result.loc[:, 1:5].sum(axis = 1).max() * 10) / 10)], fixedrange = True, tickformat = ',.3%')
log5_championship_fig.update_layout(title_text = 'KBO 팀별 우승확률', margin_l=10, margin_r=10, margin_b=10, margin_t=50, dragmode = 'pan', plot_bgcolor='#D9F2D0', paper_bgcolor="#DFDFDF")
log5_postseason_fig.update_layout(title_text = 'KBO 팀별 포스트시즌 진출확률', margin_l=10, margin_r=10, margin_b=10, margin_t=50, dragmode = 'pan', plot_bgcolor='#D9F2D0', paper_bgcolor="#DFDFDF")
for team, color in team_color.items():
    log5_championship_fig.add_trace(go.Scatter(x=days_list, y = log5_result.xs(team, level = 1)[1], name = team, mode = 'lines+markers', line = {'color': color[0], 'width' : 3}, marker = {'color': color[1], 'size': 3}, hoverlabel = {'bgcolor': color[0], 'font_color': color[1]}))
    log5_postseason_fig.add_trace(go.Scatter(x=days_list, y = log5_result.xs(team, level = 1).loc[:, 1:5].sum(axis = 1), name = team, mode = 'lines+markers', line = {'color': color[0], 'width' : 3}, marker = {'color': color[1], 'size': 3}, hoverlabel = {'bgcolor': color[0], 'font_color': color[1]}))

pythagorean_championship_fig = go.Figure(layout = go.Layout(hovermode='x'))
pythagorean_postseason_fig = go.Figure(layout = go.Layout(hovermode='x'))
# if want rangeslider, add rangeslider = {'range' : [days_list[0], days_list[-1]]}
pythagorean_championship_fig.update_xaxes(title_text = '날짜', range = [min(days_list[0], days_list[-1] - timedelta(days = 7)), days_list[-1]], minallowed = min(days_list[0], days_list[-1] - timedelta(days = 7)), maxallowed = days_list[-1])
pythagorean_postseason_fig.update_xaxes(title_text = '날짜', range = [min(days_list[0], days_list[-1] - timedelta(days = 7)), days_list[-1]], minallowed = min(days_list[0], days_list[-1] - timedelta(days = 7)), maxallowed = days_list[-1])
pythagorean_championship_fig.update_yaxes(title_text = '확률', range = [max(0, math.floor(pythagorean_result.loc[:, 1].min() * 10) / 10), min(1, math.ceil(pythagorean_result.loc[:, 1].max() * 10) / 10)], fixedrange = True, tickformat = ',.3%')
pythagorean_postseason_fig.update_yaxes(title_text = '확률', range = [max(0, math.floor(pythagorean_result.loc[:, 1:5].sum(axis = 1).min() * 10) / 10), min(1, math.ceil(pythagorean_result.loc[:, 1:5].sum(axis = 1).max() * 10) / 10)], fixedrange = True, tickformat = ',.3%')
pythagorean_championship_fig.update_layout(title_text = 'KBO 팀별 우승확률', margin_l=10, margin_r=10, margin_b=10, margin_t=50, dragmode = 'pan', plot_bgcolor='#D9F2D0', paper_bgcolor="#DFDFDF")
pythagorean_postseason_fig.update_layout(title_text = 'KBO 팀별 포스트시즌 진출확률', margin_l=10, margin_r=10, margin_b=10, margin_t=50, dragmode = 'pan', plot_bgcolor='#D9F2D0', paper_bgcolor="#DFDFDF")
for team, color in team_color.items():
    pythagorean_championship_fig.add_trace(go.Scatter(x=days_list, y = pythagorean_result.xs(team, level = 1)[1], name = team, mode = 'lines+markers', line = {'color': color[0], 'width' : 3}, marker = {'color': color[1], 'size': 3}, hoverlabel = {'bgcolor': color[0], 'font_color': color[1]}))
    pythagorean_postseason_fig.add_trace(go.Scatter(x=days_list, y = pythagorean_result.xs(team, level = 1).loc[:, 1:5].sum(axis = 1), name = team, mode = 'lines+markers', line = {'color': color[0], 'width' : 3}, marker = {'color': color[1], 'size': 3}, hoverlabel = {'bgcolor': color[0], 'font_color': color[1]}))

last_result = uniform_result.loc[:max([x for x in days_list if x < coming_li.index.get_level_values(0).max()])]
future_championship_fig = go.Figure(layout = go.Layout(hovermode='x'))
future_championship_fig.update_xaxes(title_text = '날짜', range = [coming_li.index.get_level_values(0).max() - timedelta(days = 7), coming_li.index.get_level_values(0).max()], fixedrange = True, dtick = 'D1')
future_championship_fig.update_yaxes(title_text = '확률', range = [0, 1], fixedrange = True, tickformat = ',.3%')
future_postseason_fig = go.Figure(layout = go.Layout(hovermode='x'))
future_postseason_fig.update_xaxes(title_text = '날짜', range = [coming_li.index.get_level_values(0).max() - timedelta(days = 7), coming_li.index.get_level_values(0).max()], fixedrange = True, dtick = 'D1')
future_postseason_fig.update_yaxes(title_text = '확률', range = [0, 1], fixedrange = True, tickformat = ',.3%')
future_championship_fig.update_layout(title_text = '팀 별 우승 확률 예측', margin_l=10, margin_r=10, margin_b=10, margin_t=50, plot_bgcolor='#D9F2D0', paper_bgcolor="#DFDFDF")
future_postseason_fig.update_layout(title_text = '팀 별 포스트시즌 진출 확률 예측', margin_l=10, margin_r=10, margin_b=10, margin_t=50, plot_bgcolor='#D9F2D0', paper_bgcolor="#DFDFDF")

for team, color in team_color.items():
    future_championship_fig.add_trace(go.Scatter(
        x=last_result.index.get_level_values(0).drop_duplicates(),
        y = last_result.xs(team, level = 1)[1],
        name = team, mode = 'lines+markers',
        line = {'color': color[0], 'width' : 3}, marker = {'color': color[1], 'size': 3}, hoverlabel = {'bgcolor': color[0], 'font_color': color[1]}))
    if team in coming_li.loc[coming_li.index.get_level_values(0).max()].index:
        future_championship_fig.add_trace(go.Scatter(
            x=[last_result.index.get_level_values(0).max(), coming_li.index.get_level_values(0).max()],
            y = [last_result.loc[(last_result.index.get_level_values(0).max(), team), 1], coming_li.xs(team, level = 1)['cWin'].iloc[-1]],
            mode = 'lines', line = {'color': color[0], 'width' : 3, 'dash': 'dash'}, marker = {'color': color[1], 'size': 3}, showlegend=False, hoverinfo='skip'))
        future_championship_fig.add_trace(go.Scatter(
            x=[last_result.index.get_level_values(0).max(), coming_li.index.get_level_values(0).max()],
            y = [last_result.loc[(last_result.index.get_level_values(0).max(), team), 1], coming_li.xs(team, level = 1)['cLose'].iloc[-1]],
            mode = 'lines', line = {'color': color[0], 'width' : 3, 'dash': 'dash'}, marker = {'color': color[1], 'size': 3}, showlegend=False, hoverinfo='skip'))
        future_championship_fig.add_trace(go.Scatter(name = team + '(승리)',
            x=[coming_li.index.get_level_values(0).max()],
            y = [coming_li.xs(team, level = 1)['cWin'].iloc[-1]],
            mode = 'markers', marker = {'color': color[1], 'opacity': 0}, showlegend=False, hoverlabel = {'bgcolor': color[0], 'font_color': color[1]}))
        future_championship_fig.add_trace(go.Scatter(name = team + '(패배)',
            x=[coming_li.index.get_level_values(0).max()],
            y = [coming_li.xs(team, level = 1)['cLose'].iloc[-1]],
            mode = 'markers', marker = {'color': color[1], 'opacity': 0}, showlegend=False, hoverlabel = {'bgcolor': color[0], 'font_color': color[1]}))

    future_postseason_fig.add_trace(go.Scatter(
        x=last_result.index.get_level_values(0).drop_duplicates(),
        y = last_result.xs(team, level = 1).loc[:, 1:5].sum(axis = 1),
        name = team, mode = 'lines+markers',
        line = {'color': color[0], 'width' : 3}, marker = {'color': color[1], 'size': 3}, hoverlabel = {'bgcolor': color[0], 'font_color': color[1]}))
    if team in coming_li.loc[coming_li.index.get_level_values(0).max()].index:
        future_postseason_fig.add_trace(go.Scatter(
            x=[last_result.index.get_level_values(0).max(), coming_li.index.get_level_values(0).max()],
            y = [last_result.loc[(last_result.index.get_level_values(0).max(), team), 1:5].sum(), coming_li.xs(team, level = 1)['pWin'].iloc[-1]],
            mode = 'lines', line = {'color': color[0], 'width' : 3, 'dash': 'dash'}, marker = {'color': color[1], 'size': 3}, showlegend=False, hoverinfo='skip'))
        future_postseason_fig.add_trace(go.Scatter(
            x=[last_result.index.get_level_values(0).max(), coming_li.index.get_level_values(0).max()],
            y = [last_result.loc[(last_result.index.get_level_values(0).max(), team), 1:5].sum(), coming_li.xs(team, level = 1)['pLose'].iloc[-1]],
            mode = 'lines', line = {'color': color[0], 'width' : 3, 'dash': 'dash'}, marker = {'color': color[1], 'size': 3}, showlegend=False, hoverinfo='skip'))
        future_postseason_fig.add_trace(go.Scatter(name = team + '(승리)',
            x=[coming_li.index.get_level_values(0).max()],
            y = [coming_li.xs(team, level = 1)['pWin'].iloc[-1]],
            mode = 'markers', marker = {'color': color[1], 'opacity': 0}, showlegend=False, hoverlabel = {'bgcolor': color[0], 'font_color': color[1]}))
        future_postseason_fig.add_trace(go.Scatter(name = team + '(패배)',
            x=[coming_li.index.get_level_values(0).max()],
            y = [coming_li.xs(team, level = 1)['pLose'].iloc[-1]],
            mode = 'markers', marker = {'color': color[1], 'opacity': 0}, showlegend=False, hoverlabel = {'bgcolor': color[0], 'font_color': color[1]}))

today_standing = standing.loc[standing.index.get_level_values(0).max()].reset_index(names = '팀명')
today_standing = pd.concat([today_standing['승률'].rank(method = 'min', ascending=False).astype(int).rename('순위'), today_standing], axis = 1)
today_standing = dash_table.DataTable(
    today_standing.to_dict('records'),
    [{'name': i, 'id': i} if i not in ['승률', '기대승률'] else {'name': i, 'id': i, 'type': 'numeric', 'format': Format(precision=3, scheme=Scheme.fixed)} for i in today_standing.columns.tolist()],
    style_data_conditional=[
        {'if': {'row_index': [idx for idx, x in enumerate(today_standing['팀명']) if uniform_result.loc[(standing.index.get_level_values(0).max(), x), 1:5].sum() >= 1.0]}, 'backgroundColor': '#BEF5CE'},
        {'if': {'row_index': [idx for idx, x in enumerate(today_standing['팀명']) if uniform_result.loc[(standing.index.get_level_values(0).max(), x), 1] >= 1.0]}, 'backgroundColor': '#F5F0AE'},
        {'if': {'row_index': [idx for idx, x in enumerate(today_standing['팀명']) if uniform_result.loc[(standing.index.get_level_values(0).max(), x), 6:10].sum() >= 1.0]}, 'backgroundColor': '#F5B2AF'},
        {'if': {'row_index': [idx for idx, x in enumerate(today_standing['팀명']) if uniform_result.loc[(standing.index.get_level_values(0).max(), x)].max() >= 1.0]},
        'border-bottom': '2px solid black'}
    ],
    style_cell_conditional=[{'if': {'column_id': ['순위', '팀명']}, 'fontWeight': 'bold'}],
    style_table={'margin-left': 'auto', 'margin-right': 'auto', 'margin-bottom': '10px', 'width': '100%', 'max-width': '700px'},)

coming_games = []
prev_cwp = uniform_result.loc[uniform_result.index.get_level_values(0).max(), 1]
prev_psp = uniform_result.loc[uniform_result.index.get_level_values(0).max(), 1:5].sum(axis = 1)
for idx in coming.drop_duplicates().index:
    game_df = pd.DataFrame(
        data = coming_li.loc[[(coming.loc[idx, 'date'], coming.loc[idx, 'away']), (coming.loc[idx, 'date'], coming.loc[idx, 'home'])]].astype(float).T.values,
        columns = [coming.loc[idx, 'away'], coming.loc[idx, 'home']]
    )
    game_df = pd.concat([game_df.iloc[:2].T, (game_df.loc[1] - prev_cwp.loc[game_df.columns]).to_frame(), game_df.iloc[2].to_frame(), (game_df.loc[2] - prev_cwp.loc[game_df.columns]).to_frame(), game_df.iloc[3:5].T, (game_df.loc[4] - prev_psp.loc[game_df.columns]).to_frame(), game_df.iloc[5].to_frame(), (game_df.loc[5] - prev_psp.loc[game_df.columns]).to_frame()], axis = 1, ignore_index=True).T.astype(object)

    for stat_idx in [0,5]:
        game_df.loc[stat_idx] = game_df.loc[stat_idx].apply(lambda x: f'{x:.3f}')
    for stat_idx in [1,3,6,8]:
        game_df.loc[stat_idx] = game_df.loc[stat_idx].apply(lambda x: f'{x:.2%}')
    for stat_idx in [2,4,7,9]:
        game_df.loc[stat_idx] = game_df.loc[stat_idx].apply(lambda x: '(' + f'{x:+.2%}' + 'p)')
    game_df['VS'] = ['우승 중요도', '승리 시 우승 확률', '(변화량)', '패배 시 우승 확률', '(변화량)', '포스트시즌 진출 중요도', '승리 시 포스트시즌 확률', '(변화량)', '패배 시 포스트시즌 확률', '(변화량)']
    game_df = game_df[[coming.loc[idx, 'away'], 'VS', coming.loc[idx, 'home']]]
    coming_games.append(dash_table.DataTable(
        game_df.to_dict('records'),
        [{'name': i, 'id': i} for i in game_df.columns.tolist()],
        style_header = {'text-align': 'center', 'padding': '3px', 'fontWeight': 'bold'},
        style_data = {'text-align': 'center', 'padding': '3px'},
        style_table={'margin-left': 'auto', 'margin-right': 'auto', 'margin-bottom': '10px', 'width': '100%', 'max-width': '370px'},
        style_cell_conditional = [
            {
                'if': {'column_id': team},
                'backgroundColor': color[0],
                'color': color[1]
            } for team, color in team_color.items()
        ],
        style_data_conditional = [
            {
                'if': {'row_index': [2, 4, 7, 9]},
                'border-top': ' 0px solid black',
                'font-size': '12px'
            }
        ]
    ))

write_json(now_championship_fig, file = 'fig/now_championship_fig.json', engine = 'json')
write_json(now_postseason_fig, file = 'fig/now_postseason_fig.json', engine = 'json')
write_json(log5_championship_fig, file = 'fig/log5_championship_fig.json', engine = 'json')
write_json(log5_postseason_fig, file = 'fig/log5_postseason_fig.json', engine = 'json')
write_json(pythagorean_championship_fig, file = 'fig/pythagorean_championship_fig.json', engine = 'json')
write_json(pythagorean_postseason_fig, file = 'fig/pythagorean_postseason_fig.json', engine = 'json')
write_json(future_championship_fig, file = 'fig/future_championship_fig.json', engine = 'json')
write_json(future_postseason_fig, file = 'fig/future_postseason_fig.json', engine = 'json')
with open('fig/standing.pkl', 'wb') as fw:
    pickle.dump(obj = today_standing, file = fw)
with open('fig/comingup.pkl', 'wb') as fw:
    pickle.dump(obj = coming_games, file = fw)