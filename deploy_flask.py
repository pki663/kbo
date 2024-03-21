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
uniform_result = pd.read_pickle('data/2023/uniform_probability.pkl')
log5_result = pd.read_pickle('data/2023/log5_probability.pkl')
coming_li = pd.read_pickle('data/2023/li.pkl')
standing = pd.read_pickle('data/2023/standing.pkl')
coming = pd.read_pickle('data/2023/comingup_games.pkl')

days_list = sorted(uniform_result.index.get_level_values(0).drop_duplicates())
today = uniform_result.index.get_level_values(level = 0).max()

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
            html.H2(today.strftime('%m월 %d일') + " 경기 종료 후 상황"),
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
            html.H2("다음 경기 예고"),
            html.Hr(),
            dcc.Tabs(id = 'cwli-psli', value = 'cwli', children = [
                dcc.Tab(label = '우승 확률 변화', value = 'cwli'),
                dcc.Tab(label = '포스트시즌 진출 확률 변화', value = 'psli')
            ]),
            dcc.Graph(id = 'future-fig'),
            html.H2("다음 경기 요약"),
            html.H3(coming['date'].iloc[0].isoformat(), style={'text-align':'center'})
        ] + coming_games)
    elif pathname == "/standing":
        return html.Div([
            html.H3("팀 별 시즌 중 순위 확률 변화 분석"),
            dcc.Dropdown(list(team_color.keys()), '', id = 'team-dropdown', placeholder='분석할 팀을 선택해주세요', style = {"margin-left": "0.5rem", 'width': '80%', 'border-width': '2px', 'border-color': 'gray'}),
            dcc.Graph(id = 'team-standing'),
            html.Hr(),
            html.H3("날짜별 순위별 확률 분석"),
            dcc.DatePickerSingle(id = 'calender', min_date_allowed=uniform_result.index.get_level_values(level = 0).min(), max_date_allowed=uniform_result.index.get_level_values(level = 0).max(), disabled_days=[x for x in pd.date_range(start = uniform_result.index.get_level_values(level = 0).min(), end = uniform_result.index.get_level_values(level = 0).max()).date if x not in uniform_result.index.get_level_values(level = 0)], placeholder='날짜 선택', display_format='YYYY-MM-DD', style = {"margin-left": "1rem", 'border' : '2px solid gray'}),
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
    fig.update_layout(barmode = 'stack', margin_l=10, margin_r=10, margin_b=10, margin_t=40, dragmode = 'pan')
    fig.update_xaxes(range = [max(days_list[0], days_list[-1] - timedelta(days = 15)), days_list[-1]], minallowed = days_list[0], maxallowed = days_list[-1])
    fig.update_yaxes(title_text = '해당 순위 확률', range = [0, 1], fixedrange = True)
    return fig

@app.callback(Output("date-team", 'figure'), Input("calender", 'date'))
def render_dateteam_figure(date_selection):
    if pd.isna(date_selection):
        return go.Figure()
    date_result = uniform_result.loc[date.fromisoformat(date_selection)]
    fig = go.Figure(data = [
        go.Bar(name = str(rank) + '위', x = date_result.index, y = date_result[rank])
        for rank in range(10, 0, -1)
    ], layout = go.Layout(title = go.layout.Title(text = date_selection + ' 각 팀별 순위확률'), 
        hovermode = 'x'))
    fig.update_layout(barmode = 'stack', margin_l=10, margin_r=10, margin_b=10, margin_t=40)
    fig.update_xaxes(fixedrange = True)
    fig.update_yaxes(title_text = '해당 순위 확률', range = [0, 1], fixedrange = True)
    return fig

@app.callback(Output("date-standing", 'figure'), Input("calender", 'date'))
def render_datestanding_figure(date_selection):
    if pd.isna(date_selection):
        return go.Figure()
    date_result = uniform_result.loc[date.fromisoformat(date_selection)]
    fig = go.Figure(data = [
        go.Bar(name = team, x = [str(rank) + '위' for rank in range(1,11)], y = date_result.loc[team], marker_pattern_bgcolor = color[0], marker_pattern_fgcolor = color[1], marker_pattern_shape = '.', marker_pattern_size = 5)
        for team, color in team_color.items()
    ], layout = go.Layout(title = go.layout.Title(text = date_selection + ' 각 순위별 확률'), 
        hovermode = 'x'))
    fig.update_layout(barmode = 'stack', margin_l=10, margin_r=10, margin_b=10, margin_t=40)
    fig.update_xaxes(fixedrange = True)
    fig.update_yaxes(title_text = '해당 순위 확률', range = [0, 1], fixedrange = True)
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
    application.run()