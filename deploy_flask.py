import flask
import plotly.graph_objects as go
from plotly.io import read_json
import pandas as pd
from datetime import date, timedelta
from dash import Dash, html, dcc, Input, Output, callback, dash_table, get_asset_url
from dash.dash_table.Format import Format, Scheme
import dash_bootstrap_components as dbc
import pickle

application = flask.Flask(__name__)
app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP], server = application)

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

navbar = dbc.NavbarSimple(
    children = [
        dbc.NavLink("리그 현황", href="/", active="exact"),
        dbc.NavLink("다음경기 분석", href="/comingup", active="exact"),
        dbc.NavLink("순위 분석", href="/standing", active="exact"),
        dbc.NavLink("도움말", href="/help", active='exact')
    ],
    fluid = True,
    brand='우승각',
    color='primary',
    dark = True,
    style = {
        "position": "fixed",
        'top': 0,
        'width': '100%',
        'zIndex': 100
    }
)

content = html.Div(id='page-content', style = {"margin-left": "0.5rem", "margin-right": "0.5rem", "padding-top": "60px"})

app.layout = html.Div([dcc.Location(id="url"), navbar, content])

# 팀별 순위변화 읽는 예시: standing.xs('한화', level = 1)
# 날짜별 순위표 읽는 예시: standing.loc[date(2023, 4, 15): date(2023, 4, 25)]
uniform_result = pd.read_pickle('data/2023/uniform_probability.pkl')
log5_result = pd.read_pickle('data/2023/log5_probability.pkl')
coming_li = pd.read_pickle('data/2023/li.pkl')
standing = pd.read_pickle('data/2023/standing.pkl')
coming = pd.read_pickle('data/2023/comingup_games.pkl')

days_list = sorted(uniform_result.index.get_level_values(0).drop_duplicates())

with open('fig/standing.pkl', 'rb') as fr:
    today_standing = pickle.load(fr)

with open('fig/comingup.pkl', 'rb') as fr:
    coming_games = pickle.load(fr)

now_championship_fig = read_json(file = 'fig/now_championship_fig.json', engine = 'json')
now_postseason_fig = read_json(file = 'fig/now_postseason_fig.json', engine = 'json')
future_championship_fig = read_json(file = 'fig/future_championship_fig.json', engine = 'json')
future_postseason_fig = read_json(file = 'fig/future_postseason_fig.json', engine = 'json')

@app.callback(Output("page-content", "children"), Input("url", "pathname"))
def render_page_content(pathname):
    if pathname == "/":
        return html.Div([
            html.H2("2023년 KBO 리그 페넌트레이스 최종결과"),
            html.Hr(),
            dcc.Tabs(id = 'cwp-psp', value = 'cwp', children = [
                dcc.Tab(label = '우승 확률', value = 'cwp'),
                dcc.Tab(label = '포스트시즌 진출 확률', value = 'psp')
            ]),
            dcc.Graph(id = 'now-fig'),
            today_standing
        ])
    elif pathname == "/comingup":
        return html.Div([
            html.H2("다음 경기 예고 (2023년 7월 1일 테스트 버전)"),
            html.Hr(),
            dcc.Tabs(id = 'cwli-psli', value = 'cwli', children = [
                dcc.Tab(label = '우승 확률 변화', value = 'cwli'),
                dcc.Tab(label = '포스트시즌 진출 확률 변화', value = 'psli')
            ]),
            dcc.Graph(id = 'future-fig'),
            html.H2("다음 경기 요약"),
            html.H3(coming['date'].iloc[0].isoformat(), style = {'text-align': 'center'}),
        ] + coming_games)
    elif pathname == "/standing":
        return html.Div([
            html.H3("팀 별 시즌 중 순위 확률 변화 분석"),
            dcc.Dropdown(list(team_color.keys()), '', id = 'team-dropdown', placeholder='분석할 팀을 선택해주세요', style = {"margin-left": "0.5rem", 'width': '50%'}),
            dcc.Graph(id = 'team-standing'),
            html.Hr(),
            html.H3("날짜별 순위별 확률 분석"),
            dcc.DatePickerSingle(id = 'calender', min_date_allowed=uniform_result.index.get_level_values(level = 0).min(), max_date_allowed=uniform_result.index.get_level_values(level = 0).max(), disabled_days=[x for x in pd.date_range(start = uniform_result.index.get_level_values(level = 0).min(), end = uniform_result.index.get_level_values(level = 0).max()).date if x not in uniform_result.index.get_level_values(level = 0)], date = uniform_result.index.get_level_values(level = 0).max(), style = {"margin-left": "1rem"}),
            dcc.Graph(id = 'date-team'),
            dcc.Graph(id = 'date-standing')
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
            html.Div(id = 'tutorial-contents')
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

@app.callback(Output("now-fig", 'figure'), Input("cwp-psp", 'value'))
def render_now_figure(fig_selection):
    if fig_selection == 'cwp':
        return now_championship_fig
    elif fig_selection == 'psp':
        return now_postseason_fig

@app.callback(Output("future-fig", 'figure'), Input("cwli-psli", 'value'))
def render_future_figure(fig_selection):
    if fig_selection == 'cwli':
        return future_championship_fig
    elif fig_selection == 'psli':
        return future_postseason_fig

@app.callback(Output("team-standing", 'figure'), Input("team-dropdown", 'value'))
def render_team_figure(team_selection):
    if not team_selection:
        return go.Figure()
    team_result = uniform_result.xs(team_selection, level = 1)
    fig = go.Figure(data = [
        go.Bar(name = str(rank) + '위', x = team_result.index, y = team_result[rank])
        for rank in range(10, 0, -1)
    ], layout = go.Layout(title = go.layout.Title(text = team_selection + ' 시즌 중 각 순위별 확률 변동'),
        hovermode = 'x'))
    fig.update_layout(barmode = 'stack')
    fig.update_yaxes(title_text = '해당 순위 확률', range = [0, 1], fixedrange = True)
    return fig

@app.callback(Output("date-team", 'figure'), Input("calender", 'date'))
def render_dateteam_figure(date_selection):
    date_result = uniform_result.loc[date.fromisoformat(date_selection)]
    fig = go.Figure(data = [
        go.Bar(name = str(rank) + '위', x = date_result.index, y = date_result[rank])
        for rank in range(10, 0, -1)
    ], layout = go.Layout(title = go.layout.Title(text = date_selection + ' 각 팀별 순위확률'), 
        hovermode = 'x'))
    fig.update_layout(barmode = 'stack')
    fig.update_xaxes(fixedrange = True)
    fig.update_yaxes(title_text = '해당 순위 확률', range = [0, 1], fixedrange = True)
    return fig

@app.callback(Output("date-standing", 'figure'), Input("calender", 'date'))
def render_datestanding_figure(date_selection):
    date_result = uniform_result.loc[date.fromisoformat(date_selection)]
    fig = go.Figure(data = [
        go.Bar(name = team, x = [str(rank) + '위' for rank in range(1,11)], y = date_result.loc[team], marker_pattern_bgcolor = color[0], marker_pattern_fgcolor = color[1], marker_pattern_shape = '.', marker_pattern_size = 5)
        for team, color in team_color.items()
    ], layout = go.Layout(title = go.layout.Title(text = date_selection + ' 각 순위별 확률'), 
        hovermode = 'x'))
    fig.update_layout(barmode = 'stack')
    fig.update_xaxes(fixedrange = True)
    fig.update_yaxes(title_text = '해당 순위 확률', range = [0, 1], fixedrange = True)
    return fig

@app.callback(Output("tutorial-contents", 'children'), Input("help-index", 'value'))
def show_tutorial(request_index):
    if request_index == 'cli':
        return [html.H4('그래그래 설명이 없어서 미안해')]
    elif request_index == 'now':
        return [html.Img(src=get_asset_url('basic_1.png')), html.Img(src=get_asset_url('draganddrop.png'))]
    elif request_index == 'future':
        return [html.Img(src=get_asset_url('basic_2.png'))]
    elif request_index == 'standing':
        return [html.Img(src=get_asset_url('basic_3.png')), html.Img(src=get_asset_url('basic_4.png'))]
    else:
        return []

if __name__ == '__main__':
    application.debug = True
    application.run()