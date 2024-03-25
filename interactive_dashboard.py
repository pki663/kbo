import flask
import plotly.graph_objects as go
from plotly.io import read_json
import pandas as pd
from datetime import date, timedelta
from dash import Dash, html, dcc, Input, Output, callback, dash_table, get_asset_url
from dash.dash_table.Format import Format, Scheme
import dash_bootstrap_components as dbc
import pickle
import json

team_color = {
    'LG':['#C30452', '#000000'],
    'KT':['#000000', '#EB1C24'],
    'SSG':['#CE0E2D', '#ffb81c'],
    'NC':['#071d3d', '#c7a079'],
    '두산':['#FFFFFF', '#131230'],
    'KIA':['#EA0029', '#06141F'],
    '롯데':['#6CACE4', '#D00F31'],
    '삼성':['#C0C0C0', '#074CA1'],
    '한화':['#f37321', '#25282a'],
    '키움':['#570514', '#B07F4A']
}

application = flask.Flask(__name__)
app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP], server = application, meta_tags=[
    {'property': 'og:type', 'content': 'website'},
    {'property': 'og:url', 'content': 'https://kbograph.com'},
    {'property': 'og:title', 'content': '크보그래프'},
    {'property': 'og:description', 'content': 'KBO 리그의 실시간 우승 및 포스트시즌 진출 확률 분석 사이트'},
    {'property': 'og:locale', 'content': 'ko_KR'},
    {'property': 'og:image', 'content': 'https://kbograph.com/assets/og_image.png'},
    {'property': 'og:image:width', 'content': '1200'},
    {'property': 'og:image:height', 'content': '630'}])
app._favicon = 'kbograph.ico'
app.title = 'KBOGraph'

navbar = dbc.NavbarSimple(
    children = [
        dbc.NavLink("리그 현황", href="/", active="exact"),
        dbc.NavLink("다음경기 분석", href="/comingup", active="exact"),
        dbc.NavLink("순위 분석", href="/standing", active="exact"),
        dbc.NavLink("도움말", href="/help", active='exact')
    ],
    fluid = True,
    brand='크보그래프',
    color='primary',
    dark = True,
    sticky = 'top',
    style = {
        'width': '100%',
        'zIndex': 100
    }
)

content = html.Div(id='page-content', style = {"padding-top": "10px", 'padding-left': '0.5rem', 'padding-right': '0.5rem'})
app.layout = html.Div([dcc.Location(id="url"), navbar, content])

# 팀별 순위변화 읽는 예시: standing.xs('한화', level = 1)
# 날짜별 순위표 읽는 예시: standing.loc[date(2023, 4, 15): date(2023, 4, 25)]

uniform_result = pd.read_pickle('data/uniform_probability.pkl')
log5_result = pd.read_pickle('data/log5_probability.pkl')
opponent_result = pd.read_pickle('data/opponent_probability.pkl')
coming_li = pd.read_pickle('data/li.pkl')
standing = pd.read_pickle('data/standing.pkl')
coming = pd.read_pickle('data/comingup_games.pkl')
completed_games = pd.read_pickle('data/completed_games.pkl')

days_list = sorted(uniform_result.index.get_level_values(0).drop_duplicates())
today = uniform_result.index.get_level_values(level = 0).max()

@app.callback(Output("page-content", "children"), Input("url", "pathname"))
def render_page_content(pathname):
    if pathname == "/":
        return html.Div([
            html.H2(today.strftime('%m월 %d일') + " 경기 종료 후 상황"),
            html.Hr(),
            dcc.Tabs(id = 'cwp-psp', value = 'cwp', children = [
                dcc.Tab(label = '우승 확률', value = 'cwp'),
                dcc.Tab(label = '포스트시즌 진출 확률', value = 'psp')
            ]),
            dcc.RadioItems(id = 'now-ratio-type', options = [{'label': '승률을 0.5로 통일', 'value': 'uniform'}, {'label': '작년기반 Log5 확률 적용', 'value': 'log5'}, {'label': '작년 상대전적 적용', 'value': 'opponent'}], value = 'uniform'),
            dcc.Graph(id = 'now-fig', config={'modeBarButtonsToRemove': ['select', 'lasso2d', 'autoScale'], 'displayModeBar': True, 'toImageButtonOptions': {'format': 'webp'}}),
            dash_table.DataTable(id='standing', 
                style_data_conditional=[
                {'if': {'row_index': [idx for idx, x in enumerate(team_color.keys()) if uniform_result.loc[(standing.index.get_level_values(0).max(), x), 1:5].sum() >= 1.0]}, 'backgroundColor': '#BEF5CE'},
                {'if': {'row_index': [idx for idx, x in enumerate(team_color.keys()) if uniform_result.loc[(standing.index.get_level_values(0).max(), x), 1] >= 1.0]}, 'backgroundColor': '#F5F0AE'},
                {'if': {'row_index': [idx for idx, x in enumerate(team_color.keys()) if uniform_result.loc[(standing.index.get_level_values(0).max(), x), 6:10].sum() >= 1.0]}, 'backgroundColor': '#F5B2AF'},
                {'if': {'row_index': [idx for idx, x in enumerate(team_color.keys()) if uniform_result.loc[(standing.index.get_level_values(0).max(), x)].max() >= 1.0]},
                'border-bottom': '2px solid black'}],
                style_cell_conditional=[{'if': {'column_id': ['순위', '팀명']}, 'fontWeight': 'bold'}],
                style_table={'margin-left': 'auto', 'margin-right': 'auto', 'margin-bottom': '10px', 'width': '100%', 'max-width': '700px'}
            )
        ])
    elif pathname == "/comingup":
        return html.Div([
            html.H2("다음 경기 예고"),
            html.Hr(),
            dcc.Tabs(id = 'cwli-psli', value = 'cwli', children = [
                dcc.Tab(label = '우승 확률 변화', value = 'cwli'),
                dcc.Tab(label = '포스트시즌 진출 확률 변화', value = 'psli')
            ]),
            dcc.Graph(id = 'future-fig', config={'modeBarButtonsToRemove': ['select', 'lasso2d', 'autoScale'], 'displayModeBar': True, 'toImageButtonOptions': {'format': 'webp'}}),
            html.H2("다음 경기 요약"),
            html.H3(style={'text-align':'center'}, id = 'coming-date'),
            html.Div(id='coming-games')
        ])
    elif pathname == "/standing":
        return html.Div([
            html.H3("팀 별 시즌 중 순위 확률 변화 분석"),
            dcc.Dropdown(list(team_color.keys()), '', id = 'team-dropdown', placeholder='분석할 팀을 선택해주세요', style = {"margin-left": "0.5rem", 'width': '80%', 'border-width': '2px', 'border-color': 'gray'}, searchable = False),
            dcc.RadioItems(id = 'team-ratio-type', options = [{'label': '승률을 0.5로 통일', 'value': 'uniform'}, {'label': '작년기반 Log5 확률 적용', 'value': 'log5'}, {'label': '작년 상대전적 적용', 'value': 'opponent'}], value = 'uniform'),
            dcc.Graph(id = 'team-standing', config={'modeBarButtonsToRemove': ['select', 'lasso2d', 'autoScale'], 'displayModeBar': True, 'toImageButtonOptions': {'format': 'webp'}}),
            html.Hr(),
            html.H3("날짜별 순위별 확률 분석"),
            dcc.RadioItems(id = 'date-ratio-type', options = [{'label': '승률을 0.5로 통일', 'value': 'uniform'}, {'label': '작년기반 Log5 확률 적용', 'value': 'log5'}, {'label': '작년 상대전적 적용', 'value': 'opponent'}], value = 'uniform'),
            dcc.DatePickerSingle(id = 'calender', min_date_allowed=uniform_result.index.get_level_values(level = 0).min(), max_date_allowed=uniform_result.index.get_level_values(level = 0).max(), disabled_days=[x for x in pd.date_range(start = uniform_result.index.get_level_values(level = 0).min(), end = uniform_result.index.get_level_values(level = 0).max()).date if x not in uniform_result.index.get_level_values(level = 0)], placeholder='날짜 선택', display_format='YYYY-MM-DD', style = {"margin-left": "1rem", 'border' : '2px solid gray'}, initial_visible_month = uniform_result.index.get_level_values(level = 0).max()),
            dcc.Graph(id = 'date-team', config={'modeBarButtonsToRemove': ['select', 'lasso2d', 'autoScale'], 'displayModeBar': True, 'toImageButtonOptions': {'format': 'webp'}}),
            dcc.Graph(id = 'date-standing', config={'modeBarButtonsToRemove': ['select', 'lasso2d', 'autoScale'], 'displayModeBar': True, 'toImageButtonOptions': {'format': 'webp'}})
        ])
    elif pathname == '/help':
        return html.Div([
            html.H3("도움말"),
            dcc.Tabs(id = 'help-index', value = 'cli', children = [
                dcc.Tab(label = '우승 확률이란?', value = 'cli'),
                dcc.Tab(label = '리그 현황', value = 'now'),
                dcc.Tab(label = '다음경기 분석', value = 'future'),
                dcc.Tab(label = '순위 분석', value = 'standing')
            ]),
            html.Div(id = 'tutorial-contents', style = {'width': '100%'})
        ])
    # If the user tries to reach a different page, return a 404 message
    return html.Div(
        [
            html.H1("404: Not found", className="text-danger"),
            html.Hr(),
            html.P(f"잘못된 경로입니다."),
        ],
        className="p-3 bg-light rounded-3",
    )

@app.callback(Output("now-fig", 'figure'), [Input("cwp-psp", 'value'), Input("now-ratio-type", 'value')])
def render_now_figure(fig_selection, ratio_selection):
    if ratio_selection == 'uniform':
        now_result = uniform_result
    elif ratio_selection == 'log5':
        now_result = log5_result
    elif ratio_selection == 'opponent':
        now_result = opponent_result
    fig = go.Figure(layout = go.Layout(hovermode='x'))
    fig.update_xaxes(title_text = '날짜', range = [min(days_list[0], days_list[-1] - timedelta(days = 7)), days_list[-1]], minallowed = min(days_list[0], days_list[-1] - timedelta(days = 7)), maxallowed = days_list[-1])
    fig.update_yaxes(title_text = '확률', range = [0, 1], fixedrange = True, tickformat = ',.3%')
    fig.update_layout(margin_l=10, margin_r=10, margin_b=10, margin_t=50, dragmode = 'pan', plot_bgcolor='#D9F2D0', paper_bgcolor="#DFDFDF")
    if fig_selection == 'cwp':
        fig.update_layout(title_text = 'KBO 팀별 우승확률')
        for team, color in team_color.items():
            fig.add_trace(go.Scatter(x=days_list, y = now_result.xs(team, level = 1)[1], name = team, mode = 'lines+markers', line = {'color': color[0], 'width' : 3}, marker = {'color': color[1], 'size': 3}, hoverlabel = {'bgcolor': color[0], 'font_color': color[1]}))
    elif fig_selection == 'psp':
        fig.update_layout(title_text = 'KBO 팀별 포스트시즌 진출확률')
        for team, color in team_color.items():
            fig.add_trace(go.Scatter(x=days_list, y = now_result.xs(team, level = 1).loc[:, 1:5].sum(axis = 1), name = team, mode = 'lines+markers', line = {'color': color[0], 'width' : 3}, marker = {'color': color[1], 'size': 3}, hoverlabel = {'bgcolor': color[0], 'font_color': color[1]}))
    return fig

@app.callback([Output("standing", 'data'), Output("standing", 'columns')], Input("now-fig", 'clickData'))
def show_standing(clicked):
    if clicked:
        today_standing = standing.loc[date.fromisoformat(clicked['points'][0]['x'])].reset_index(names = '팀명')
    else:
        today_standing = standing.loc[standing.index.get_level_values(0).max()].reset_index(names = '팀명')
    today_standing = pd.concat([today_standing['승률'].rank(method = 'min', ascending=False).astype(int).rename('순위'), today_standing], axis = 1)
    return today_standing.to_dict('records'), [{'name': i, 'id': i} if i != '승률' else {'name': i, 'id': i, 'type': 'numeric', 'format': Format(precision=3, scheme=Scheme.fixed)} for i in today_standing.columns.tolist()]

@app.callback(Output("future-fig", 'figure'), Input("cwli-psli", 'value'))
def render_future_figure(fig_selection):
    last_result = uniform_result.loc[:max([x for x in days_list if x < coming_li.index.get_level_values(0).max()])]
    fig = go.Figure(layout = go.Layout(hovermode='x'))
    fig.update_xaxes(title_text = '날짜', range = [coming_li.index.get_level_values(0).max() - timedelta(days = 7), coming_li.index.get_level_values(0).max()], dtick = 'D1')
    fig.update_yaxes(title_text = '확률', range = [0, 1], fixedrange = True, tickformat = ',.3%')
    fig.update_layout(margin_l=10, margin_r=10, margin_b=10, margin_t=50, plot_bgcolor='#D9F2D0', paper_bgcolor="#DFDFDF")
    if fig_selection == 'cwli':
        fig.update_layout(title_text = '팀 별 우승 확률 예측')
        for team, color in team_color.items():
            fig.add_trace(go.Scatter(
                x = last_result.index.get_level_values(0).drop_duplicates(),
                y = last_result.xs(team, level = 1)[1],
                name = team, mode = 'lines+markers',
                line = {'color': color[0], 'width' : 3}, marker = {'color': color[1], 'size': 3}, hoverlabel = {'bgcolor': color[0], 'font_color': color[1]}))
            if team in coming_li.loc[coming_li.index.get_level_values(0).max()].index:
                fig.add_trace(go.Scatter(
                    x=[last_result.index.get_level_values(0).max(), coming_li.index.get_level_values(0).max()],
                    y = [last_result.loc[(last_result.index.get_level_values(0).max(), team), 1], coming_li.xs(team, level = 1)['cWin'].iloc[-1]],
                    mode = 'lines', line = {'color': color[0], 'width' : 3, 'dash': 'dash'}, marker = {'color': color[1], 'size': 3}, showlegend=False, hoverinfo='skip'))
                fig.add_trace(go.Scatter(
                    x=[last_result.index.get_level_values(0).max(), coming_li.index.get_level_values(0).max()],
                    y = [last_result.loc[(last_result.index.get_level_values(0).max(), team), 1], coming_li.xs(team, level = 1)['cLose'].iloc[-1]],
                    mode = 'lines', line = {'color': color[0], 'width' : 3, 'dash': 'dash'}, marker = {'color': color[1], 'size': 3}, showlegend=False, hoverinfo='skip'))
                fig.add_trace(go.Scatter(name = team + '(승리)',
                    x = [coming_li.index.get_level_values(0).max()],
                    y = [coming_li.xs(team, level = 1)['cWin'].iloc[-1]],
                    mode = 'markers', marker = {'color': color[1], 'opacity': 0}, showlegend=False, hoverlabel = {'bgcolor': color[0], 'font_color': color[1]}))
                fig.add_trace(go.Scatter(name = team + '(패배)',
                    x = [coming_li.index.get_level_values(0).max()],
                    y = [coming_li.xs(team, level = 1)['cLose'].iloc[-1]],
                    mode = 'markers', marker = {'color': color[1], 'opacity': 0}, showlegend=False, hoverlabel = {'bgcolor': color[0], 'font_color': color[1]}))
    elif fig_selection == 'psli':
        fig.update_layout(title_text = '팀 별 포스트시즌 진출 확률 예측')
        for team, color in team_color.items():
            fig.add_trace(go.Scatter(
                x = last_result.index.get_level_values(0).drop_duplicates(),
                y = last_result.xs(team, level = 1).loc[:, 1:5].sum(axis = 1),
                name = team, mode = 'lines+markers',
                line = {'color': color[0], 'width' : 3}, marker = {'color': color[1], 'size': 3}, hoverlabel = {'bgcolor': color[0], 'font_color': color[1]}))
            if team in coming_li.loc[coming_li.index.get_level_values(0).max()].index:
                fig.add_trace(go.Scatter(
                    x=[last_result.index.get_level_values(0).max(), coming_li.index.get_level_values(0).max()],
                    y = [last_result.loc[(last_result.index.get_level_values(0).max(), team), 1:5].sum(), coming_li.xs(team, level = 1)['pWin'].iloc[-1]],
                    mode = 'lines', line = {'color': color[0], 'width' : 3, 'dash': 'dash'}, marker = {'color': color[1], 'size': 3}, showlegend=False, hoverinfo='skip'))
                fig.add_trace(go.Scatter(
                    x=[last_result.index.get_level_values(0).max(), coming_li.index.get_level_values(0).max()],
                    y = [last_result.loc[(last_result.index.get_level_values(0).max(), team), 1:5].sum(), coming_li.xs(team, level = 1)['pLose'].iloc[-1]],
                    mode = 'lines', line = {'color': color[0], 'width' : 3, 'dash': 'dash'}, marker = {'color': color[1], 'size': 3}, showlegend=False, hoverinfo='skip'))
                fig.add_trace(go.Scatter(name = team + '(승리)',
                    x = [coming_li.index.get_level_values(0).max()],
                    y = [coming_li.xs(team, level = 1)['pWin'].iloc[-1]],
                    mode = 'markers', marker = {'color': color[1], 'opacity': 0}, showlegend=False, hoverlabel = {'bgcolor': color[0], 'font_color': color[1]}))
                fig.add_trace(go.Scatter(name = team + '(패배)',
                    x = [coming_li.index.get_level_values(0).max()],
                    y = [coming_li.xs(team, level = 1)['pLose'].iloc[-1]],
                    mode = 'markers', marker = {'color': color[1], 'opacity': 0}, showlegend=False, hoverlabel = {'bgcolor': color[0], 'font_color': color[1]}))
    return fig

@app.callback([Output("coming-date", 'children'), Output("coming-games", 'children')], Input("future-fig", 'clickData'))
def show_comingup(clicked):
    coming_games = []
    if clicked:
        selected_date = date.fromisoformat(clicked['points'][0]['x']) if date.fromisoformat(clicked['points'][0]['x']) >= completed_games['date'].min() else completed_games['date'].min()
    else:
        selected_date = coming_li.index.get_level_values(0).max()
    li_df = coming if selected_date >= coming_li.index.get_level_values(0).max() else completed_games.loc[completed_games['date'] == selected_date]
    prev_cwp = uniform_result.loc[max([x for x in days_list if x < selected_date]), 1]
    prev_psp = uniform_result.loc[max([x for x in days_list if x < selected_date]), 1:5].sum(axis = 1)
    for idx in li_df.index:
        game_df = pd.DataFrame(
            data = coming_li.loc[[(selected_date, li_df.loc[idx, 'away']), (selected_date, li_df.loc[idx, 'home'])]].astype(float).T.values,
            columns = [li_df.loc[idx, 'away'], li_df.loc[idx, 'home']]
        )
        game_df = pd.concat([game_df.iloc[:2].T, (game_df.loc[1] - prev_cwp.loc[game_df.columns]).to_frame(), game_df.iloc[2].to_frame(), (game_df.loc[2] - prev_cwp.loc[game_df.columns]).to_frame(), game_df.iloc[3:5].T, (game_df.loc[4] - prev_psp.loc[game_df.columns]).to_frame(), game_df.iloc[5].to_frame(), (game_df.loc[5] - prev_psp.loc[game_df.columns]).to_frame()], axis = 1, ignore_index=True).T.astype(object)
        for stat_idx in [0,5]:
            game_df.loc[stat_idx] = game_df.loc[stat_idx].apply(lambda x: f'{x:.3f}')
        for stat_idx in [1,3,6,8]:
            game_df.loc[stat_idx] = game_df.loc[stat_idx].apply(lambda x: f'{x:.2%}')
        for stat_idx in [2,4,7,9]:
            game_df.loc[stat_idx] = game_df.loc[stat_idx].apply(lambda x: '(' + f'{x:+.2%}' + 'p)')
        game_df['VS'] = ['우승 중요도', '승리 시 우승 확률', '(변화량)', '패배 시 우승 확률', '(변화량)', '포스트시즌 진출 중요도', '승리 시 포스트시즌 확률', '(변화량)', '패배 시 포스트시즌 확률', '(변화량)']
        game_df = game_df[[li_df.loc[idx, 'away'], 'VS', li_df.loc[idx, 'home']]]
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
    return selected_date.isoformat(), coming_games

@app.callback(Output("team-standing", 'figure'), [Input("team-dropdown", 'value'), Input('team-ratio-type', 'value')])
def render_team_figure(team_selection, ratio_selection):
    if not team_selection:
        return go.Figure()
    if ratio_selection == 'uniform':
        team_result = uniform_result.xs(team_selection, level = 1)
    elif ratio_selection == 'log5':
        team_result = log5_result.xs(team_selection, level = 1)
    elif ratio_selection == 'opponent':
        team_result = opponent_result.xs(team_selection, level = 1)
    else:
        return go.Figure()
    fig = go.Figure(data = [
        go.Bar(name = str(rank) + '위', x = team_result.index, y = team_result[rank])
        for rank in range(10, 0, -1)
    ], layout = go.Layout(title = go.layout.Title(text = team_selection + ' 시즌 중 각 순위별 확률 변동'),
        hovermode = 'x'))
    fig.update_layout(barmode = 'stack', margin_l=10, margin_r=10, margin_b=10, margin_t=40, dragmode = 'pan', plot_bgcolor='#D9F2D0', paper_bgcolor="#DFDFDF")
    fig.update_xaxes(range = [min(days_list[0], days_list[-1] - timedelta(days = 7)), days_list[-1]], minallowed = min(days_list[0], days_list[-1] - timedelta(days = 7)), maxallowed = days_list[-1])
    fig.update_yaxes(title_text = '해당 순위 확률', range = [0, 1], fixedrange = True, tickformat = ',.3%')
    return fig

@app.callback(Output("date-team", 'figure'), [Input("calender", 'date'), Input('date-ratio-type', 'value')])
def render_dateteam_figure(date_selection, ratio_selection):
    if pd.isna(date_selection):
        return go.Figure()
    if ratio_selection == 'uniform':
        date_result = uniform_result.loc[date.fromisoformat(date_selection)]
    elif ratio_selection == 'log5':
        date_result = log5_result.loc[date.fromisoformat(date_selection)]
    elif ratio_selection == 'opponent':
        date_result = opponent_result.loc[date.fromisoformat(date_selection)]
    else:
        return go.Figure()
    fig = go.Figure(data = [
        go.Bar(name = str(rank) + '위', x = date_result.index, y = date_result[rank])
        for rank in range(10, 0, -1)
    ], layout = go.Layout(title = go.layout.Title(text = date_selection + ' 각 팀별 순위확률'), 
        hovermode = 'x'))
    fig.update_layout(barmode = 'stack', margin_l=10, margin_r=10, margin_b=10, margin_t=40, plot_bgcolor='#D9F2D0', paper_bgcolor="#DFDFDF")
    fig.update_xaxes(fixedrange = True)
    fig.update_yaxes(title_text = '해당 순위 확률', range = [0, 1], fixedrange = True, tickformat = ',.3%')
    return fig

@app.callback(Output("date-standing", 'figure'), [Input("calender", 'date'), Input('date-ratio-type', 'value')])
def render_datestanding_figure(date_selection, ratio_selection):
    if pd.isna(date_selection):
        return go.Figure()
    if ratio_selection == 'uniform':
        date_result = uniform_result.loc[date.fromisoformat(date_selection)]
    elif ratio_selection == 'log5':
        date_result = log5_result.loc[date.fromisoformat(date_selection)]
    elif ratio_selection == 'opponent':
        date_result = opponent_result.loc[date.fromisoformat(date_selection)]
    else:
        return go.Figure()
    fig = go.Figure(data = [
        go.Bar(name = team, x = [str(rank) + '위' for rank in range(1,11)], y = date_result.loc[team], marker_pattern_bgcolor = color[0], marker_pattern_fgcolor = color[1], marker_pattern_shape = '.', marker_pattern_size = 5, hoverlabel = {'bgcolor': color[0], 'font_color': color[1]})
        for team, color in team_color.items()
    ], layout = go.Layout(title = go.layout.Title(text = date_selection + ' 각 순위별 확률'), 
        hovermode = 'x'))
    fig.update_layout(barmode = 'stack', margin_l=10, margin_r=10, margin_b=10, margin_t=40, plot_bgcolor='#D9F2D0', paper_bgcolor="#DFDFDF")
    fig.update_xaxes(fixedrange = True)
    fig.update_yaxes(title_text = '해당 순위 확률', range = [0, 1], fixedrange = True, tickformat = ',.3%')
    return fig

@app.callback(Output("tutorial-contents", 'children'), Input("help-index", 'value'))
def show_tutorial(request_index):
    if request_index == 'cli':
        return [
            html.H3('우승 확률(Championship Win Probability)이란?'),
            html.P('cWP(Championship Win Probability)란 이름 그대로, 어떤 팀이 리그에서 우승할 확률을 의미합니다. 이 스탯의 산출방법을 활용하면 팀이 특정 순위 안에 들 확률도 구할 수 있습니다. (예: 팀이 5위안에 들어서 포스트시즌에 진출할 확률)'),
            html.H4('보편적인 계산방법 (coin-toss simulation)'),
            html.Div(children = [
                '저명한 메이저리그 야구 기록 사이트인 ',
                html.A('Baseball Reference에 따르면', href = 'https://www.baseball-reference.com/about/wpa.shtml', target = '_blank', rel = 'noreferrer noopener'),
                ', 우승확률은 계산 기점에서 아직 치르지 않은 경기들에 대해 coin-toss simulation, 즉, 각 팀의 승리확률이 50%라고 가정한 시뮬레이션 리그를 25,000회 치러 그 결과 우승한 확률로 계산됩니다. 일종의 ',
                html.A('몬테카를로 방법', href = 'https://ko.wikipedia.org/wiki/%EB%AA%AC%ED%85%8C%EC%B9%B4%EB%A5%BC%EB%A1%9C_%EB%B0%A9%EB%B2%95', target = '_blank', rel = 'noreferrer noopener'),
                '라고 할 수 있죠!']),
            html.P('예를 들어, 25,000번 시뮬레이션을 한 결과 그 중 A팀이 우승한 횟수가 5,000번이었다면 A팀의 우승확률은 5,000/25,000 = 0.2 = 20%가 되는 것입니다.'),
            html.H4('이 프로젝트에서 추가로 제공하는 계산방법 (향후에)'),
            html.P('그러나, 기존의 계산 방법은 각 경기의 승리확률이 50%로 고정되어 각 팀의 전력 차이를 반영하지 못한다는 한계점이 있습니다. 이에 착안하여, 본 프로젝트는 두 가지의 경기별 승률 보정을 제공합니다.'),
            html.Ol([
                html.P(['1. 전년도 상대전적을 활용한 시뮬레이션', html.Br(), html.Div('이 방식에서는 시뮬레이션에서 각 경기의 승리확률로 전년도의 상대전적을 사용합니다.'), html.Div('예를 들어, 2023시즌 LG 트윈스는 두산 베어스와의 경기에서 11승 5패로 상대승률 0.779를 기록했습니다. 이를 반영하여 LG 트윈스와 두산 베어스의 경기에서는 LG의 승리확률을 0.779로 적용하여 시뮬레이션을 진행하는 방식입니다.')]),
                html.P(['2. Log5 방법을 활용한 시뮬레이션', html.Br(), html.Div(['Log5는 양 팀의 리그 승률을 기반으로 두 팀 간의 맞대결 기대승률을 계산하는 방법입니다. (구체적인 설명은 ', html.A('FreeRedbird씨께서 작성하신 설명글', href = 'https://birdsnest.tistory.com/347', target = '_blank', rel = 'noreferrer noopener'), '을 읽어봐주세요.)']), html.Div('이 방식에서 승률이 a인 A팀이 승률이 b인 B팀을 상대로 이길 확률은 다음 수식과 같습니다.'), html.Img(src = get_asset_url('log5.png')), html.Div('시뮬레이션 상에서는 위 식의 승률에 전년도의 리그 승률을 대입하여 각 경기의 승리확률에 적용합니다. 예를 들어, 작년 LG의 승률이 0.606이고, 키움의 승률은 0.521이었는데 이걸 위 식에 대입하면 LG가 키움과의 경기에서 승리할 확률은 0.586이 됩니다. 그리고 이 확률을 LG-키움 간의 경기에 일괄 적용하는 것입니다.')])
            ]),
            html.H3('Championship Leverage Index(cLI)'),
            html.P('일반적인 Leverage Index(LI)가 한 경기 내에서 특정 타석의 중요도를 승리 확률의 변화량(Win Probability Added)을 통하여 평가하는 것이라면, cLI는 `한 시즌 내에서 특정 경기의 중요도를 우승 확률의 변화량을 통하여 평가하는 것`입니다.'),
            html.H4('cLI의 기준점'),
            html.P('중요도는 주관적인 척도입니다. 따라서, 중요도를 수치로 정의하기 위하여 `기준이 되는 경기와 비교했을 때 몇 배나 중요한 경기인가?`로 cLI를 정의합니다. 이 때 기준이 되는 경기는 바로 개막전 경기입니다. 즉, 어떤 경기의 cLI가 2.0이라는 것은 그 경기가 우승에 있어 개막전에 비해 두 배 중요한 경기라는 뜻이 됩니다.'),
            html.H4('cLI의 계산 방법'),
            html.P([
                html.Div('cLI의 계산은 두 번의 우승 확률 시뮬레이션을 통하여 이루어집니다. 한 번은 계산하고자 하는 경기를 승리했다고 가정하고 시뮬레이션하며, 다른 한 번은 동일한 경기를 패배했다고 가정하고 시뮬레이션합니다. 위의 우승 확률 시뮬레이션과 마찬가지로 각 시뮬레이션은 25,000회씩 실시됩니다.'),
                html.Div('이렇게 시뮬레이션한 결과, 두 시뮬레이션의 우승 확률 차이가 cLI 계산의 척도가 됩니다. 위 단락에서 언급한 기준점인 개막전 경기는 승리했을 때와 패배했을 때의 우승 확률차이가 대략 0.02954(2.954%p)인 것으로 계산됩니다. (144경기 단일리그 체제 기준, coin-toss simulation 사용)'),
                html.Div('이해를 돕기위해 (SSG 팬들에겐 죄송하지만) 2019년 두산의 우승을 사례로 cLI 계산을 해보겠습니다.'),
                html.Div('시뮬레이션을 할 것도 없이, 당시 두산의 최종전에서 우승 확률 변화는 간단합니다. 이기면 우승 확률 100%(우승 확정), 지면 우승 확률 0%(우승 실패). 이 케이스에서 승패에 따른 우승 확률 변화는 1.0-0.0 = 1.0입니다. 위에서 언급했듯이 개막전에서 승패에 따른 우승 확률의 변화가 0.02954이므로, 이 경기의 cLI는 1.0/0.02954 = 33.852에 달합니다. 즉, 이 경기는 개막전에 비해 우승에 미치는 중요도가 33.8배나 되는 경기인 것입니다.')
            ])
        ]
    elif request_index == 'now':
        return [
            html.Img(src=get_asset_url('basic_1.png'), style = {'width': '90%', 'max-width': '700px'}),
            html.P([
                html.Div('① 상단의 탭에서 표시할 그래프를 선택할 수 있습니다.'),
                html.Div('② 그래프 위에 커서를 올리면 커서가 위치한 날짜의 구체적인 확률값을 확인할 수 있습니다.'),
                html.Div('③ 그래프 우측 상단의 버튼을 통해 그래프 확대/축소, 범위 초기화, 그래프 저장 등을 할 수 있습니다.'),
                html.Div('④ 우측 범례를 통해 그래프의 각 요소가 어떤 팀을 의미하는지 확인할 수 있습니다. 각 범례를 클릭하면 그래프에서 보여줄 지 여부를 설정할 수 있습니다.'),
                html.Div([html.Div('⑤ 현재 시점의 순위표입니다.'), html.Div('노란색으로 칠해진 칸은 우승확정, 초록색으로 칠해진 칸은 포스트시즌 확정, 붉은색으로 칠해진 칸은 포스트시즌 탈락 확정을 의미합니다.'), html.Div('밑줄이 쳐진 칸은 해당 순위가 확정되었음을 의미합니다.')])
            ]),
            html.Img(src=get_asset_url('draganddrop.png'), style = {'width': '90%', 'max-width': '700px'}),
            html.P(['그래프 위에서 자세히 보고 싶은 범위를 드래그 앤 드롭으로 지정하면 확대할 수 있습니다.'
            ])
        ]
    elif request_index == 'future':
        return [
            html.Img(src=get_asset_url('basic_2.png'), style = {'width': '90%', 'max-width': '700px'}),
            html.P([
                html.Div('① 상단의 탭에서 표시할 그래프를 선택할 수 있습니다.'),
                html.Div('② 실선은 현재까지 각 날짜별 확률을 의미합니다.'),
                html.Div([html.Div('③ 점선은 다음 경기 결과에 따른 확률 변화를 표시합니다.'), html.Div('위쪽으로 뻗는 점선은 다음 경기를 승리할 경우 확률 변화입니다. 아래쪽으로 뻗는 점선은 다음 경기를 패배할 경우 확률 변화입니다.'), html.Div('단, 실제 확률 변화는 타 팀 경기 결과에 따라 다를 수 있습니다.')]),
                html.Div([html.Div('④ 하단의 표는 다음 경기의 정보를 표시합니다.'), html.Div([html.B('우승/포스트시즌 진출 중요도'), ': 경기가 해당 팀의 우승 또는 포스트시즌 진출 확률에 개막전 대비 몇 배나 중요한 경기인지 나타냅니다.']), html.P([html.B('승리/패배 시 우승/포스트시즌 진출 확률'), ': 해당 팀이 이 경기를 승리/패배할 시 예상되는 확률을 의미합니다.'])])
            ])
        ]
    elif request_index == 'standing':
        return [
            html.Img(src=get_asset_url('basic_3.png'), style = {'width': '90%', 'max-width': '700px'}),
            html.P([
                html.Div('① 상단에서 분석할 팀을 선택합니다.'),
                html.Div('② 이 그래프는 시즌 기간 중 선택한 팀이 최종적으로 각 순위를 기록할 확률을 나타냅니다.'),
                html.Div('③ 그래프 위에 커서를 올리면 커서가 위치한 날짜의 구체적인 확률값을 확인할 수 있습니다.'),
                html.Div('④ 우측 범례를 통해 그래프의 각 색깔이 몇 위를 의미하는지 확인할 수 있습니다. 각 범례를 클릭하면 그래프에서 보여줄 지 여부를 설정할 수 있습니다.')
            ]),
            html.Img(src=get_asset_url('basic_4.png'), style = {'width': '90%', 'max-width': '700px'}),
            html.P([
                html.Div('① 상단에서 분석할 날짜를 선택합니다.'),
                html.Div('② 이 그래프는 선택한 날짜의 각 팀의 최종 순위 확률 분포를 나타냅니다.'),
                html.Div('③ 이 그래프는 선택한 날짜에서 각 순위의 팀별 확률을 나타냅니다.'),
                html.Div('④ 우측 범례를 통해 그래프의 각 색깔이 몇 위 또는 어떤 팀을 의미하는지 확인할 수 있습니다. 각 범례를 클릭하면 그래프에서 보여줄 지 여부를 설정할 수 있습니다.')
            ])
        ]
    else:
        return []

if __name__ == '__main__':
    application.run(debug = True)