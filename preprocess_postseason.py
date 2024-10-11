import pandas as pd
import plotly.graph_objects as go
from plotly.io import write_json, read_json
from dash import dash_table
from dash.dash_table.Format import Format, Scheme
import pickle
import math
import os
import pandas as pd

team_color = {
    'LG':['#C30452', '#000000'],
    'KT':['#000000', '#EB1C24'],
    '두산':['#FFFFFF', '#131230'],
    'KIA':['#EA0029', '#06141F'],
    '삼성':['#C0C0C0', '#074CA1']
}

def log5(team_ratio: float, opponent_ratio: float) -> float:
    return team_ratio * (1-opponent_ratio) / (team_ratio * (1-opponent_ratio) + opponent_ratio * (1-team_ratio))

def postseason_ratio(winto, team_ratio, team_win = 0, opponent_win = 0):
    if team_win >= winto:
        return {(winto, opponent_win): 1.0}
    elif opponent_win >= winto:
        return {(team_win, winto): 1.0}
    opponent_ratio = 1 - team_ratio
    team_rest = winto - team_win
    opponent_rest = winto - opponent_win
    result = {(winto, opponent_win + x): team_ratio ** team_rest * opponent_ratio ** x * math.comb(team_rest + x - 1, team_rest - 1) for x in range(opponent_rest)}
    result.update({(team_win + x, winto): opponent_ratio ** opponent_rest * team_ratio ** x * math.comb(opponent_rest + x - 1, opponent_rest - 1) for x in range(team_rest)})
    return result


'''
po_fig = go.Figure(layout = go.Layout(hovermode = 'x'))
po_fig.update_xaxes(title_text = '게임 수', range = [0, 5], fixedrange = True, dtick = 1)
po_fig.update_yaxes(range = [0, 1], fixedrange = True, tickformat = ',.3%')
po_fig.update_layout(title_text = '진출 확률', margin_l=10, margin_r=10, margin_b=10, margin_t=50, plot_bgcolor='#D9F2D0', paper_bgcolor="#DFDFDF")
ks_fig = go.Figure(layout = go.Layout(hovermode = 'x'))
ks_fig.update_xaxes(title_text = '게임 수', range = [0, 7], fixedrange = True, dtick = 1)
ks_fig.update_yaxes(range = [0, 1], fixedrange = True, tickformat = ',.3%')
ks_fig.update_layout(title_text = '진출 확률', margin_l=10, margin_r=10, margin_b=10, margin_t=50, plot_bgcolor='#D9F2D0', paper_bgcolor="#DFDFDF")
'''

# Wildcard
wc_fig = go.Figure(layout = go.Layout(hovermode = 'x'))
wc_fig.update_xaxes(title_text = '게임 수', range = [0, 2], fixedrange = True, dtick = 1)
wc_fig.update_yaxes(range = [0, 1], fixedrange = True, tickformat = ',.3%')
wc_fig.update_layout(title_text = '진출 확률', margin_l=10, margin_r=10, margin_b=10, margin_t=50, plot_bgcolor='#D9F2D0', paper_bgcolor="#DFDFDF")

ds_gamewin = log5(74/142, 72/142)
wc_result = [(1,0), (1,1), (1,2)]
wc_fig.add_traces([
    go.Scatter(
        name = '두산', 
        x = list(range(len(wc_result))),
        y = [sum([b for a, b in postseason_ratio(2, ds_gamewin, x, y).items() if a[0] == 2]) 
        for x, y in wc_result],
        text = ['{}승 {}패'.format(x[0], x[1]) for x in wc_result],
        mode = 'lines', line = {'color': team_color['두산'][0], 'width' : 3, 'dash': 'solid'}, marker = {'color': team_color['두산'][1], 'size': 3},
        legendgroup = '두산',
        visible = 'legendonly'
    ),
    go.Scatter(
        name = 'kt', 
        x = list(range(len(wc_result))),
        y = [sum([b for a, b in postseason_ratio(2, ds_gamewin, x, y).items() if a[1] == 2]) 
        for x, y in wc_result],
        text = ['{}승 {}패'.format(x[1], x[0]) for x in wc_result],
        mode = 'lines', line = {'color': team_color['KT'][0], 'width' : 3, 'dash': 'solid'}, marker = {'color': team_color['KT'][1], 'size': 3},
        legendgroup = 'kt'
    )
])

for idx, (prev, next) in enumerate(zip(wc_result[:-1], wc_result[1:])):
    alt_next = (prev[0] + 1, prev[1]) if prev[0] == next[0] else (prev[0], prev[1] + 1)
    wc_fig.add_traces([
        go.Scatter(
            x = [idx, idx+1],
            y = [
                sum([b for a, b in postseason_ratio(2, ds_gamewin, prev[0], prev[1]).items() if a[0] == 2]), 
                sum([b for a, b in postseason_ratio(2, ds_gamewin, alt_next[0], alt_next[1]).items() if a[0] == 2])],
            mode = 'lines', line = {'color': team_color['두산'][0], 'width' : 3, 'dash': 'dash'}, marker = {'color': team_color['두산'][1], 'size': 3},
            legendgroup = '두산', hoverinfo='skip', showlegend= False, visible = 'legendonly'
        ),
        go.Scatter(
            x = [idx, idx+1],
            y = [
                sum([b for a, b in postseason_ratio(2, ds_gamewin, prev[0], prev[1]).items() if a[1] == 2]), 
                sum([b for a, b in postseason_ratio(2, ds_gamewin, alt_next[0], alt_next[1]).items() if a[1] == 2])],
            mode = 'lines', line = {'color': team_color['KT'][0], 'width' : 3, 'dash': 'dash'}, marker = {'color': team_color['KT'][1], 'size': 3},
            legendgroup = 'kt', hoverinfo='skip', showlegend= False
        )
    ])

if (wc_result[-1][0] != 2) and (wc_result[-1][1] != 2):
    wc_fig.add_traces([
        go.Scatter(
            x = [len(wc_result) - 1, len(wc_result)],
            y = [
                sum([b for a, b in postseason_ratio(2, ds_gamewin, wc_result[-1][0], wc_result[-1][1]).items() if a[0] == 2]), 
                sum([b for a, b in postseason_ratio(2, ds_gamewin, wc_result[-1][0] + 1, wc_result[-1][1]).items() if a[0] == 2])
            ],
            mode = 'lines', line = {'color': team_color['두산'][0], 'width' : 3, 'dash': 'dash'}, marker = {'color': team_color['두산'][1], 'size': 3},
            legendgroup = '두산', hoverinfo='skip', showlegend= False, visible = 'legendonly'
        ),
        go.Scatter(
            x = [len(wc_result) - 1, len(wc_result)],
            y = [
                sum([b for a, b in postseason_ratio(2, ds_gamewin, wc_result[-1][0], wc_result[-1][1]).items() if a[0] == 2]), 
                sum([b for a, b in postseason_ratio(2, ds_gamewin, wc_result[-1][0], wc_result[-1][1] + 1).items() if a[0] == 2])
            ],
            mode = 'lines', line = {'color': team_color['두산'][0], 'width' : 3, 'dash': 'dash'}, marker = {'color': team_color['두산'][1], 'size': 3},
            legendgroup = '두산', hoverinfo='skip', showlegend= False, visible = 'legendonly'
        ),
        go.Scatter(
            x = [len(wc_result) - 1, len(wc_result)],
            y = [
                sum([b for a, b in postseason_ratio(2, ds_gamewin, wc_result[-1][0], wc_result[-1][1]).items() if a[1] == 2]), 
                sum([b for a, b in postseason_ratio(2, ds_gamewin, wc_result[-1][0] + 1, wc_result[-1][1]).items() if a[1] == 2])
            ],
            mode = 'lines', line = {'color': team_color['KT'][0], 'width' : 3, 'dash': 'dash'}, marker = {'color': team_color['KT'][1], 'size': 3},
            legendgroup = 'kt', hoverinfo='skip', showlegend= False
        ),
        go.Scatter(
            x = [len(wc_result) - 1, len(wc_result)],
            y = [
                sum([b for a, b in postseason_ratio(2, ds_gamewin, wc_result[-1][0], wc_result[-1][1]).items() if a[1] == 2]), 
                sum([b for a, b in postseason_ratio(2, ds_gamewin, wc_result[-1][0], wc_result[-1][1] + 1).items() if a[1] == 2])
            ],
            mode = 'lines', line = {'color': team_color['KT'][0], 'width' : 3, 'dash': 'dash'}, marker = {'color': team_color['KT'][1], 'size': 3},
            legendgroup = 'kt', hoverinfo='skip', showlegend= False
        )
    ])

# Semi-Playoff
spo_fig = go.Figure(layout = go.Layout(hovermode = 'x'))
spo_fig.update_xaxes(title_text = '게임 수', range = [0, 5], fixedrange = True, dtick = 1)
spo_fig.update_yaxes(range = [0, 1], fixedrange = True, tickformat = ',.3%')
spo_fig.update_layout(title_text = '진출 확률', margin_l=10, margin_r=10, margin_b=10, margin_t=50, plot_bgcolor='#D9F2D0', paper_bgcolor="#DFDFDF")

lg_gamewin = log5(76/142, 72/142)
spo_result = [(0,0), (0,1), (1,1), (2,1), (2,2), (3,2)]
spo_fig.add_traces([
    go.Scatter(
        name = 'LG', 
        x = list(range(len(spo_result))),
        y = [sum([b for a, b in postseason_ratio(3, lg_gamewin, x, y).items() if a[0] == 3]) 
        for x, y in spo_result],
        text = ['{}승 {}패'.format(x[0], x[1]) for x in spo_result],
        mode = 'lines', line = {'color': team_color['LG'][0], 'width' : 3, 'dash': 'solid'}, marker = {'color': team_color['LG'][1], 'size': 3},
        legendgroup = 'LG'
    ),
    go.Scatter(
        name = 'kt', 
        x = list(range(len(spo_result))),
        y = [sum([b for a, b in postseason_ratio(3, lg_gamewin, x, y).items() if a[1] == 3]) 
        for x, y in spo_result],
        text = ['{}승 {}패'.format(x[1], x[0]) for x in spo_result],
        mode = 'lines', line = {'color': team_color['KT'][0], 'width' : 3, 'dash': 'solid'}, marker = {'color': team_color['KT'][1], 'size': 3},
        legendgroup = 'kt', visible = 'legendonly'
    )
])

for idx, (prev, next) in enumerate(zip(spo_result[:-1], spo_result[1:])):
    alt_next = (prev[0] + 1, prev[1]) if prev[0] == next[0] else (prev[0], prev[1] + 1)
    spo_fig.add_traces([
        go.Scatter(
            x = [idx, idx+1],
            y = [
                sum([b for a, b in postseason_ratio(3, lg_gamewin, prev[0], prev[1]).items() if a[0] == 3]), 
                sum([b for a, b in postseason_ratio(3, lg_gamewin, alt_next[0], alt_next[1]).items() if a[0] == 3])],
            mode = 'lines', line = {'color': team_color['LG'][0], 'width' : 3, 'dash': 'dash'}, marker = {'color': team_color['LG'][1], 'size': 3},
            legendgroup = 'LG', hoverinfo='skip', showlegend= False
        ),
        go.Scatter(
            x = [idx, idx+1],
            y = [
                sum([b for a, b in postseason_ratio(3, lg_gamewin, prev[0], prev[1]).items() if a[1] == 3]), 
                sum([b for a, b in postseason_ratio(3, lg_gamewin, alt_next[0], alt_next[1]).items() if a[1] == 3])],
            mode = 'lines', line = {'color': team_color['KT'][0], 'width' : 3, 'dash': 'dash'}, marker = {'color': team_color['KT'][1], 'size': 3},
            legendgroup = 'kt', hoverinfo='skip', showlegend= False, visible = 'legendonly'
        )
    ])

if (spo_result[-1][0] != 3) and (spo_result[-1][1] != 3):
    spo_fig.add_traces([
        go.Scatter(
            x = [len(spo_result) - 1, len(spo_result)],
            y = [
                sum([b for a, b in postseason_ratio(3, lg_gamewin, spo_result[-1][0], spo_result[-1][1]).items() if a[0] == 3]), 
                sum([b for a, b in postseason_ratio(3, lg_gamewin, spo_result[-1][0] + 1, spo_result[-1][1]).items() if a[0] == 3])
            ],
            mode = 'lines', line = {'color': team_color['LG'][0], 'width' : 3, 'dash': 'dash'}, marker = {'color': team_color['LG'][1], 'size': 3},
            legendgroup = 'LG', hoverinfo='skip', showlegend= False
        ),
        go.Scatter(
            x = [len(spo_result) - 1, len(spo_result)],
            y = [
                sum([b for a, b in postseason_ratio(3, lg_gamewin, spo_result[-1][0], spo_result[-1][1]).items() if a[0] == 3]), 
                sum([b for a, b in postseason_ratio(3, lg_gamewin, spo_result[-1][0], spo_result[-1][1] + 1).items() if a[0] == 3])
            ],
            mode = 'lines', line = {'color': team_color['LG'][0], 'width' : 3, 'dash': 'dash'}, marker = {'color': team_color['LG'][1], 'size': 3},
            legendgroup = 'LG', hoverinfo='skip', showlegend= False
        ),
        go.Scatter(
            x = [len(spo_result) - 1, len(spo_result)],
            y = [
                sum([b for a, b in postseason_ratio(3, lg_gamewin, spo_result[-1][0], spo_result[-1][1]).items() if a[1] == 3]), 
                sum([b for a, b in postseason_ratio(3, lg_gamewin, spo_result[-1][0] + 1, spo_result[-1][1]).items() if a[1] == 3])
            ],
            mode = 'lines', line = {'color': team_color['KT'][0], 'width' : 3, 'dash': 'dash'}, marker = {'color': team_color['KT'][1], 'size': 3},
            legendgroup = 'kt', hoverinfo='skip', showlegend= False, visible = 'legendonly'
        ),
        go.Scatter(
            x = [len(spo_result) - 1, len(spo_result)],
            y = [
                sum([b for a, b in postseason_ratio(3, lg_gamewin, spo_result[-1][0], spo_result[-1][1]).items() if a[1] == 3]), 
                sum([b for a, b in postseason_ratio(3, lg_gamewin, spo_result[-1][0], spo_result[-1][1] + 1).items() if a[1] == 3])
            ],
            mode = 'lines', line = {'color': team_color['KT'][0], 'width' : 3, 'dash': 'dash'}, marker = {'color': team_color['KT'][1], 'size': 3},
            legendgroup = 'kt', hoverinfo='skip', showlegend= False, visible = 'legendonly'
        )
    ])

# Playoff


# Korean Series


write_json(wc_fig, file = 'fig/wc_fig.json', engine = 'json')
write_json(spo_fig, file = 'fig/spo_fig.json', engine = 'json')
#write_json(po_fig, file = 'fig/po_fig.json', engine = 'json')
#write_json(ks_fig, file = 'fig/ks_fig.json', engine = 'json')

# 표 제작
# Wildcard
wc_dict = {'(두산-kt)': '확률'}
wc_dict.update({'-'.join(list(map(str, x))): format(y, ".3%") for x, y in postseason_ratio(2, ds_gamewin, 1, 0).items()})
wc_dict['두산 진출'] = format(sum([y for x, y in postseason_ratio(2, ds_gamewin, 1, 0).items() if x[0] == 2]), '.3%')
wc_dict['kt 진출'] = format(sum([y for x, y in postseason_ratio(2, ds_gamewin, 1, 0).items() if x[1] == 2]), '.3%')

wc_probability = dash_table.DataTable([wc_dict],
[{'name': i, 'id': i} for i in ['(두산-kt)', '2-0', '2-1', '두산 진출', '1-2', 'kt 진출']],
style_cell_conditional=[
    {'if': {'column_id': ['1-2', 'kt 진출']}, 'fontWeight': 'bold', 'backgroundColor': '#BEF5CE'},
    {'if': {'column_id': ['두산 진출', 'kt 진출']}, 'border-left': '2px solid black' , 'border-right': '4px solid black'},
    {'if': {'column_id': ['(두산-kt)']}, 'border-right': '4px solid black'}],
style_header = {'text-align': 'center', 'fontWeight': 'bold'},
style_data = {'text-align': 'center', 'padding': '3px'},
style_table={'margin-left': 'auto', 'margin-right': 'auto', 'margin-top': '10px', 'margin-bottom': '10px', 'width': '100%', 'max-width': '600px', 'overflowX': 'auto'})

# Semi-Playoff
spo_dict = {'(LG-kt)': '확률'}
spo_dict.update({'-'.join(list(map(str, x))): format(y, ".3%") for x, y in postseason_ratio(3, lg_gamewin, 0, 0).items()})
spo_dict['LG 진출'] = format(sum([y for x, y in postseason_ratio(3, lg_gamewin, 0, 0).items() if x[0] == 3]), '.3%')
spo_dict['kt 진출'] = format(sum([y for x, y in postseason_ratio(3, lg_gamewin, 0, 0).items() if x[1] == 3]), '.3%')

spo_probability = dash_table.DataTable([spo_dict],
    [{'name': i, 'id': i} for i in ['(LG-kt)', '3-0', '3-1', '3-2', 'LG 진출', '0-3', '1-3', '2-3', 'kt 진출']],
    style_cell_conditional=[
    {'if': {'column_id': ['3-2', 'LG 진출']}, 'fontWeight': 'bold', 'backgroundColor': '#BEF5CE'},
    {'if': {'column_id': ['LG 진출', 'kt 진출']}, 'border-left': '2px solid black' , 'border-right': '4px solid black'},
    {'if': {'column_id': ['(LG-kt)']}, 'border-right': '4px solid black'}],
    style_header = {'text-align': 'center', 'fontWeight': 'bold'},
    style_data = {'text-align': 'center', 'padding': '3px'},
    style_table={'margin-left': 'auto', 'margin-right': 'auto', 'margin-top': '10px', 'margin-bottom': '10px', 'width': '100%', 'max-width': '800px', 'overflowX': 'auto'}
)

# Playoff
po_initial = {'(삼성-LG)': '시리즈 초기'}
po_initial.update({'-'.join(list(map(str, x))): format(y, ".3%") for x, y in postseason_ratio(3, log5(78/142, 76/142), 0, 0).items()})
po_initial['삼성 진출'] = format(sum([y for x, y in postseason_ratio(3, log5(78/142, 76/142), 0, 0).items() if x[0] == 3]), '.3%')
po_initial['LG 진출'] = format(sum([y for x, y in postseason_ratio(3, log5(78/142, 76/142), 0, 0).items() if x[1] == 3]), '.3%')

po_now = {'(삼성-LG)': '현재'}
po_now.update({'-'.join(list(map(str, x))): format(y, ".3%") for x, y in postseason_ratio(3, log5(78/142, 76/142), 0, 0).items()})
po_now['삼성 진출'] = format(sum([y for x, y in postseason_ratio(3, log5(78/142, 76/142), 0, 0).items() if x[0] == 3]), '.3%')
po_now['LG 진출'] = format(sum([y for x, y in postseason_ratio(3, log5(78/142, 76/142), 0, 0).items() if x[1] == 3]), '.3%')

po_probability = dash_table.DataTable([po_initial, po_now],
    [{'name': i, 'id': i} for i in ['(삼성-LG)', '3-0', '3-1', '3-2', '삼성 진출', '0-3', '1-3', '2-3', 'LG 진출']],
    style_cell_conditional=[
        {'if': {'column_id': ['삼성 진출', 'LG 진출']}, 'border-left': '2px solid black' , 'border-right': '4px solid black'},
        {'if': {'column_id': ['(삼성-???)']}, 'border-right': '4px solid black'}],
    style_header = {'text-align': 'center', 'fontWeight': 'bold'},
    style_data = {'text-align': 'center', 'padding': '3px'},
    style_table={'margin-left': 'auto', 'margin-right': 'auto', 'margin-top': '10px', 'margin-bottom': '10px', 'width': '100%', 'max-width': '800px', 'overflowX': 'auto'}
)

# Korean Series
ks_ss = {'(KIA-???)': '삼성'}
ks_ss.update({'-'.join(list(map(str, x))): format(y, ".3%") for x, y in postseason_ratio(4, log5(87/142, 78/142), 0, 0).items()})
ks_ss['KIA 우승'] = format(sum([y for x, y in postseason_ratio(4, log5(87/142, 78/142), 0, 0).items() if x[0] == 4]), '.3%')
ks_ss['상대팀 우승'] = format(sum([y for x, y in postseason_ratio(4, log5(87/142, 78/142), 0, 0).items() if x[1] == 4]), '.3%')

ks_lg = {'(KIA-???)': 'LG'}
ks_lg.update({'-'.join(list(map(str, x))): format(y, ".3%") for x, y in postseason_ratio(4, log5(87/142, 76/142), 0, 0).items()})
ks_lg['KIA 우승'] = format(sum([y for x, y in postseason_ratio(4, log5(87/142, 76/142), 0, 0).items() if x[0] == 4]), '.3%')
ks_lg['상대팀 우승'] = format(sum([y for x, y in postseason_ratio(4, log5(87/142, 76/142), 0, 0).items() if x[1] == 4]), '.3%')

ks_probability = dash_table.DataTable([ks_ss, ks_lg],
    [{'name': i, 'id': i} for i in ['(KIA-???)', '4-0', '4-1', '4-2', '4-3', 'KIA 우승', '0-4', '1-4', '2-4', '3-4', '상대팀 우승']],
    style_cell_conditional=[
        {'if': {'column_id': ['KIA 우승', '상대팀 우승']}, 'border-left': '2px solid black' , 'border-right': '4px solid black'},
        {'if': {'column_id': ['(KIA-???)']}, 'border-right': '4px solid black'}],
    style_header = {'text-align': 'center', 'fontWeight': 'bold'},
    style_data = {'text-align': 'center', 'padding': '3px'},
    style_table={'margin-left': 'auto', 'margin-right': 'auto', 'margin-top': '10px', 'margin-bottom': '10px', 'width': '100%', 'max-width': '800px', 'overflowX': 'auto'}
)

with open('fig/wc_table.pkl', 'wb') as fw:
    pickle.dump(obj = wc_probability, file = fw)
with open('fig/spo_table.pkl', 'wb') as fw:
    pickle.dump(obj = spo_probability, file = fw)
with open('fig/po_table.pkl', 'wb') as fw:
    pickle.dump(obj = po_probability, file = fw)
with open('fig/ks_table.pkl', 'wb') as fw:
    pickle.dump(obj = ks_probability, file = fw)