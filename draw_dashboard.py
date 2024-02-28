#%%
import plotly.graph_objects as go
import pandas as pd
from datetime import date, timedelta

#%%
team_color = {
    '키움':['#570514', '#B07F4A'],
    '두산':['#131230', '#FFFFFF'],
    '롯데':['#041E42', '#D00F31'],
    '삼성':['#074CA1', '#C0C0C0'],
    '한화':['#FF6600', '#000000'],
    'KIA':['#EA0029', '#06141F'],
    'LG':['#C30452', '#000000'],
    'SSG':['#CE0E2D', '#ffb81c'],
    'NC':['#315288', '#AF917B'],
    'KT':['#000000', '#EB1C24']}
#%%
# 팀별 순위변화 읽는 예시: standing.xs('한화', level = 1)
# 날짜별 순위표 읽는 예시: standing.loc[date(2023, 4, 15): date(2023, 4, 25)]

#%%
uniform_result = pd.read_pickle('data/2023_uniform_prob.pkl')
log5_result = pd.read_pickle('data/2023_log5_prob.pkl')
li_july = pd.read_pickle('data/li_2023july.pkl')

#%%
# 우승확률 변화 그래프
fig = go.Figure(layout = go.Layout(title = go.layout.Title(text = '2023 시즌 KBO 팀별 우승확률'), hovermode='x'))
fig.update_xaxes(title_text = '날짜', range = [uniform_result.index.get_level_values(0).drop_duplicates()[0], uniform_result.index.get_level_values(0).drop_duplicates()[-1]])
fig.update_yaxes(title_text = '우승 확률', range = [0, 1], fixedrange = True)
for team, color in team_color.items():
    fig.add_trace(go.Scatter(x=uniform_result.index.get_level_values(0).drop_duplicates(), y = uniform_result.xs(team, level = 1)[1], name = team, mode = 'lines+markers', line = {'color': color[0]}, marker = {'color': color[1], 'size': 3}))

fig.show()

# %%
# 포스트시즌 진출 확률 변화 그래프
fig = go.Figure(layout = go.Layout(title = go.layout.Title(text = '2023 시즌 KBO 팀별 포스트시즌 진출확률'), hovermode='x'))
fig.update_xaxes(title_text = '날짜', range = [uniform_result.index.get_level_values(0).drop_duplicates()[0], uniform_result.index.get_level_values(0).drop_duplicates()[-1]])
fig.update_yaxes(title_text = '포스트시즌 확률', range = [0, 1], fixedrange = True)
for team, color in team_color.items():
    fig.add_trace(go.Scatter(x=uniform_result.index.get_level_values(0).drop_duplicates(), y = uniform_result.xs(team, level = 1).loc[:, 1:5].sum(axis = 1), name = team, mode = 'lines+markers', line = {'color': color[0]}, marker = {'color': color[1], 'size': 3}))

fig.show()

#%%
# cli 포함 그래프
until_june = uniform_result.loc[:li_july['date'].max() - timedelta(days=1)]

fig = go.Figure(layout = go.Layout(title = go.layout.Title(text = '2023 시즌 KBO 팀별 우승확률 (예측포함)'), hovermode='x'))
fig.update_xaxes(title_text = '날짜', range = [li_july['date'].max() - timedelta(days=7), li_july['date'].max()])
fig.update_yaxes(title_text = '우승 확률', range = [0, 1], fixedrange = True)
for team, color in team_color.items():
    fig.add_trace(go.Scatter(
        x=until_june.index.get_level_values(0).drop_duplicates(),
        y = until_june.xs(team, level = 1)[1],
        name = team, mode = 'lines+markers',
        line = {'color': color[0]}, marker = {'color': color[1], 'size': 3}))
    fig.add_trace(go.Scatter(
        x=[until_june.index.get_level_values(0).max(), li_july['date'].max()],
        y = [until_june.loc[(until_june.index.get_level_values(0).max(), team), 1], li_july.loc[team, 'cWin']],
        mode = 'lines+text', line = {'color': color[0], 'dash': 'dash'}, marker = {'color': color[1], 'size': 3}, showlegend=False, hoverinfo='skip',
        text=['', round(li_july.loc[team, 'cWin'], 3) if li_july.loc[team, 'cLI'] > 1 else ''], textposition='top left'))
    fig.add_trace(go.Scatter(
        x=[until_june.index.get_level_values(0).max(), li_july['date'].max()],
        y = [until_june.loc[(until_june.index.get_level_values(0).max(), team), 1], li_july.loc[team, 'cLose']],
        mode = 'lines+text', line = {'color': color[0], 'dash': 'dash'}, marker = {'color': color[1], 'size': 3}, showlegend=False, hoverinfo='skip',
        text=['', round(li_july.loc[team, 'cLose'], 3) if li_july.loc[team, 'cLI'] > 1 else ''], textposition='bottom left'))

fig.show()
# %%
# 각 팀별 순위 확률 그래프
july_result = uniform_result.loc[date(2023,7,1)]
fig = go.Figure(data = [
    go.Bar(name = str(rank) + '위', x = july_result.index, y = july_result[rank])
    for rank in range(10, 0, -1)
], layout = go.Layout(title = go.layout.Title(text = '2023년 7월 1일 각 팀별 순위확률'), 
    hovermode = 'x'))
fig.update_layout(barmode = 'stack')
fig.update_xaxes(fixedrange = True)
fig.update_yaxes(title_text = '해당 순위 확률', range = [0, 1], fixedrange = True)

fig.show()

# %%
# 각 순위별 팀 확률 그래프
july_result = uniform_result.loc[date(2023,7,1)]
fig = go.Figure(data = [
    go.Bar(name = team, x = [str(rank) + '위' for rank in range(1,11)], y = july_result.loc[team], marker_pattern_bgcolor = color[0], marker_pattern_fgcolor = color[1], marker_pattern_shape = '.', marker_pattern_size = 5)
    for team, color in team_color.items()
], layout = go.Layout(title = go.layout.Title(text = '2023년 7월 1일 각 순위별 확률'), 
    hovermode = 'x'))
fig.update_layout(barmode = 'stack')
fig.update_xaxes(fixedrange = True)
fig.update_yaxes(title_text = '해당 순위 확률', range = [0, 1], fixedrange = True)

fig.show()

# %%
# 특정팀 시즌 중 순위별 확률 변화
hanwha_result = uniform_result.xs('한화', level = 1)
fig = go.Figure(data = [
    go.Bar(name = str(rank) + '위', x = hanwha_result.index, y = hanwha_result[rank])
    for rank in range(10, 0, -1)
], layout = go.Layout(title = go.layout.Title(text = '한화 시즌 중 각 순위별 확률 변동'),
    hovermode = 'x'))
fig.update_layout(barmode = 'stack')
fig.update_yaxes(title_text = '해당 순위 확률', range = [0, 1], fixedrange = True)

fig.show()