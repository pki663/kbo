import plotly.graph_objects as go
import pandas as pd
from datetime import date, timedelta
from dash import Dash, html, dcc, Input, Output, callback, dash_table
from dash.dash_table.Format import Format, Scheme
import dash_bootstrap_components as dbc

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

sidebar = html.Div(
    [
        html.H2("우승각"),
        html.Hr(),
        html.P(
            "KBO 리그 각 팀들의 우승 및 포스트시즌 진출 확률 등 시즌 흐름에 대한 정보와 예측을 제공합니다.", className="lead", style = {'font-size': '14px'}
        ),
        dbc.Nav(
            [
                dbc.NavLink("리그 현황", href="/", active="exact"),
                dbc.NavLink("다음경기 분석", href="/comingup", active="exact"),
                dbc.NavLink("순위 분석", href="/standing", active="exact"),
            ],
            vertical=True,
            pills=True,
        ),
    ],
    style={
        "position": "fixed",
        "top": 0,
        "left": 0,
        "bottom": 0,
        "width": "16rem",
        "padding": "2rem 1rem",
        "background-color": "#f8f9fa",
    }
)

content = html.Div(id='page-content', style = {"margin-left": "18rem", "margin-right": "2rem", "padding": "2rem 1rem"})
# 팀별 순위변화 읽는 예시: standing.xs('한화', level = 1)
# 날짜별 순위표 읽는 예시: standing.loc[date(2023, 4, 15): date(2023, 4, 25)]

uniform_result = pd.read_pickle('data/uniform_probability.pkl')
log5_result = pd.read_pickle('data/log5_probability.pkl')
coming_li = pd.read_pickle('data/li.pkl')
standing = pd.read_pickle('data/standing.pkl')
coming = pd.read_pickle('data/comingup_games.pkl')

days_list = sorted(uniform_result.index.get_level_values(0).drop_duplicates())

def print_standing(target_date, standing_df):
    day_standing = standing_df.loc[target_date].reset_index(names = '팀명')
    day_standing = pd.concat([day_standing['승률'].rank(method = 'min', ascending=False).astype(int).rename('순위'), day_standing], axis = 1)
    return dash_table.DataTable(
        day_standing.to_dict('records'),
        [{'name': i, 'id': i} if i != '승률' else {'name': i, 'id': i, 'type': 'numeric', 'format': Format(precision=3, scheme=Scheme.fixed)} for i in day_standing.columns.tolist()],
        style_data_conditional=[
            {'if': {'row_index': [idx for idx, x in enumerate(day_standing['팀명']) if uniform_result.loc[(target_date, x), 1:5].sum() == 1.0]}, 'backgroundColor': '#BEF5CE'},
            {'if': {'row_index': [idx for idx, x in enumerate(day_standing['팀명']) if uniform_result.loc[(target_date, x), 1] == 1.0]}, 'backgroundColor': '#F5F0AE'},
            {'if': {'row_index': [idx for idx, x in enumerate(day_standing['팀명']) if uniform_result.loc[(target_date, x), 6:10].sum() == 1.0]}, 'backgroundColor': '#F5B2AF'},
            {'if': {'row_index': [idx for idx, x in enumerate(day_standing['팀명']) if uniform_result.loc[(target_date, x)].max() == 1.0]},
            'border-bottom': '2px solid black'}
        ],
        style_cell_conditional=[{'if': {'column_id': ['순위', '팀명']}, 'fontWeight': 'bold'}])

def print_coming(comingup, comingup_li):
    coming_games = []
    for idx in comingup.index:
        game_df = pd.DataFrame(
            data = comingup_li.loc[[(comingup.loc[idx, 'date'], comingup.loc[idx, 'away']), (comingup.loc[idx, 'date'], comingup.loc[idx, 'home'])]].astype(float).round(3).T.values,
            columns = [comingup.loc[idx, 'away'], comingup.loc[idx, 'home']]
        )
        game_df['VS'] = ['우승 중요도', '승리 시 우승 확률', '패배 시 우승 확률', '포스트시즌 진출 중요도', '승리 시 포스트시즌 진출 확률', '패배 시 포스트시즌 진출 확률']
        game_df = game_df[[comingup.loc[idx, 'away'], 'VS', comingup.loc[idx, 'home']]]
        coming_games.append(dash_table.DataTable(
            game_df.to_dict('records'),
            [{'name': i, 'id': i} for i in game_df.columns.tolist()],
            style_header = {'text-align': 'center', 'padding': '3px', 'fontWeight': 'bold'},
            style_data = {'text-align': 'center', 'padding': '3px'},
            style_table={'margin-left': 'auto', 'margin-right': 'auto', 'margin-bottom': '10px', 'width': '50%'},
            style_cell_conditional = [
                {
                    'if': {'column_id': team},
                    'backgroundColor': color[0],
                    'color': color[1]
                } for team, color in team_color.items()
            ]
        ))
    return coming_games
        
app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server
app.layout = html.Div([dcc.Location(id="url"), sidebar, content])

@app.callback(Output("page-content", "children"), Input("url", "pathname"))
def render_page_content(pathname):
    if pathname == "/":
        return html.Div([
            html.H2(date.today().isoformat() + " 현재 리그 상황"),
            html.Hr(),
            dcc.Tabs(id = 'cwp-psp', value = 'cwp', children = [
                dcc.Tab(label = '우승 확률', value = 'cwp'),
                dcc.Tab(label = '포스트시즌 진출 확률', value = 'psp')
            ]),
            dcc.Graph(id = 'now-fig'),
            print_standing(standing.index.get_level_values(0).max(), standing)
        ])
    elif pathname == "/comingup":
        return html.Div([
            html.H2("다음 경기 예고"),
            html.Hr(),
            dcc.Tabs(id = 'cwli-psli', value = 'cwli', children = [
                dcc.Tab(label = '우승 확률 변화', value = 'cwli'),
                dcc.Tab(label = '포스트시즌 진출 확률 변화', value = 'psli')
            ]),
            dcc.Graph(id = 'future-fig'),
            html.H2("다음 경기 요약"),
            html.H3(coming['date'].iloc[0].isoformat(), style = {'text-align': 'center'}),
        ] + print_coming(coming, coming_li))
    elif pathname == "/standing":
        return html.Div([
            dcc.Dropdown(list(team_color.keys()), '', id = 'team-dropdown', placeholder='분석할 팀을 선택해주세요'),
            dcc.Graph(id = 'team-standing'),
            dcc.DatePickerSingle(id = 'calender', min_date_allowed=uniform_result.index.get_level_values(level = 0).min(), max_date_allowed=uniform_result.index.get_level_values(level = 0).max(), disabled_days=[x for x in pd.date_range(start = uniform_result.index.get_level_values(level = 0).min(), end = uniform_result.index.get_level_values(level = 0).max()).date if x not in uniform_result.index.get_level_values(level = 0)], date = uniform_result.index.get_level_values(level = 0).max()),
            dcc.Graph(id = 'date-team'),
            dcc.Graph(id = 'date-standing')
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
    fig = go.Figure(layout = go.Layout(hovermode='x'))
    fig.update_xaxes(title_text = '날짜', range = [days_list[0], days_list[-1]])
    fig.update_yaxes(title_text = '확률', range = [0, 1], fixedrange = True)
    if fig_selection == 'cwp':
        fig.update_layout(title_text = 'KBO 팀별 우승확률')
        for team, color in team_color.items():
            fig.add_trace(go.Scatter(x=days_list, y = uniform_result.xs(team, level = 1)[1], name = team, mode = 'lines+markers', line = {'color': color[0]}, marker = {'color': color[1], 'size': 3}))
    elif fig_selection == 'psp':
        fig.update_layout(title_text = 'KBO 팀별 포스트시즌 진출확률')
        for team, color in team_color.items():
            fig.add_trace(go.Scatter(x=days_list, y = uniform_result.xs(team, level = 1).loc[:, 1:5].sum(axis = 1), name = team, mode = 'lines+markers', line = {'color': color[0]}, marker = {'color': color[1], 'size': 3}))
    return fig

@app.callback(Output("future-fig", 'figure'), Input("cwli-psli", 'value'))
def render_future_figure(fig_selection):
    last_result = uniform_result.loc[:max([x for x in days_list if x < coming_li.index.get_level_values(0).max()])]
    fig = go.Figure(layout = go.Layout(hovermode='x'))
    fig.update_xaxes(title_text = '날짜', range = [coming_li.index.get_level_values(0).max() - timedelta(days = 7), coming_li.index.get_level_values(0).max()], fixedrange = True)
    fig.update_yaxes(title_text = '확률', range = [0, 1], fixedrange = True)
    if fig_selection == 'cwli':
        fig.update_layout(title_text = '2023 시즌 KBO 팀별 우승 확률 예측')
        for team, color in team_color.items():
            fig.add_trace(go.Scatter(
                x=last_result.index.get_level_values(0).drop_duplicates(),
                y = last_result.xs(team, level = 1)[1],
                name = team, mode = 'lines+markers',
                line = {'color': color[0]}, marker = {'color': color[1], 'size': 3}))
            if team in coming_li.loc[coming_li.index.get_level_values(0).max()].index:
                fig.add_trace(go.Scatter(
                    x=[last_result.index.get_level_values(0).max(), coming_li.index.get_level_values(0).max()],
                    y = [last_result.loc[(last_result.index.get_level_values(0).max(), team), 1], coming_li.xs(team, level = 1)['cWin'].iloc[-1]],
                    mode = 'lines+text', line = {'color': color[0], 'dash': 'dash'}, marker = {'color': color[1], 'size': 3}, showlegend=False, hoverinfo='skip',
                    text=['', round(coming_li.xs(team, level = 1)['cWin'].iloc[-1], 3) if coming_li.xs(team, level = 1)['cLI'].iloc[-1] > 1 else ''], textposition='top left'))
                fig.add_trace(go.Scatter(
                    x=[last_result.index.get_level_values(0).max(), coming_li.index.get_level_values(0).max()],
                    y = [last_result.loc[(last_result.index.get_level_values(0).max(), team), 1], coming_li.xs(team, level = 1)['cLose'].iloc[-1]],
                    mode = 'lines+text', line = {'color': color[0], 'dash': 'dash'}, marker = {'color': color[1], 'size': 3}, showlegend=False, hoverinfo='skip',
                    text=['', round(coming_li.xs(team, level = 1)['cLose'].iloc[-1], 3) if coming_li.xs(team, level = 1)['cLI'].iloc[-1] > 1 else ''], textposition='bottom left'))
    elif fig_selection == 'psli':
        fig.update_layout(title_text = '2023 시즌 KBO 팀별 포스트시즌 진출 확률 예측')
        for team, color in team_color.items():
            fig.add_trace(go.Scatter(
                x=last_result.index.get_level_values(0).drop_duplicates(),
                y = last_result.xs(team, level = 1).loc[:, 1:5].sum(axis = 1),
                name = team, mode = 'lines+markers',
                line = {'color': color[0]}, marker = {'color': color[1], 'size': 3}))
            if team in coming_li.loc[coming_li.index.get_level_values(0).max()].index:
                fig.add_trace(go.Scatter(
                    x=[last_result.index.get_level_values(0).max(), coming_li.index.get_level_values(0).max()],
                    y = [last_result.loc[(last_result.index.get_level_values(0).max(), team), 1:5].sum(), coming_li.xs(team, level = 1)['pWin'].iloc[-1]],
                    mode = 'lines+text', line = {'color': color[0], 'dash': 'dash'}, marker = {'color': color[1], 'size': 3}, showlegend=False, hoverinfo='skip',
                    text=['', round(coming_li.xs(team, level = 1)['pWin'].iloc[-1], 3) if coming_li.xs(team, level = 1)['pLI'].iloc[-1] > 1 else ''], textposition='top left'))
                fig.add_trace(go.Scatter(
                    x=[last_result.index.get_level_values(0).max(), coming_li.index.get_level_values(0).max()],
                    y = [last_result.loc[(last_result.index.get_level_values(0).max(), team), 1:5].sum(), coming_li.xs(team, level = 1)['pLose'].iloc[-1]],
                    mode = 'lines+text', line = {'color': color[0], 'dash': 'dash'}, marker = {'color': color[1], 'size': 3}, showlegend=False, hoverinfo='skip',
                    text=['', round(coming_li.xs(team, level = 1)['pLose'].iloc[-1], 3) if coming_li.xs(team, level = 1)['pLI'].iloc[-1] > 1 else ''], textposition='bottom left'))
    return fig

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

if __name__ == '__main__':
    app.run_server(debug = False, port = 8888, use_reloader = True)