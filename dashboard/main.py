from dash import Dash, html, dash_table, dcc, Input, Output, callback
import pandas as pd
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots

dir_path = './output'
inst_id = 'BTC-USDT'
df = pd.read_csv(f'{dir_path}/{inst_id}_bar_data.csv')
df_trades = pd.read_csv(f'{dir_path}/{inst_id}_trades.csv')
df_stats = pd.read_csv(f'{dir_path}/stats.csv')

# Initialize the app
app = Dash(__name__)

scat_fig = go.Figure(data=go.Scatter(x=df_stats['Return']*100, y=df_stats['Max Drawdown']*100, text=df_stats['ticker'], mode="markers"), layout={'title': {'text':'MDD/Return'}})
scat_fig_2 = go.Figure(data=go.Scatter(x=df_stats['Return']*100, y=df_stats['Win Rate']*100, text=df_stats['ticker'], mode="markers"), layout={'title': {'text':'Win Rate/Return'}})
scat_fig_3 = go.Figure(data=go.Scatter(x=df_stats['Return']*100, y=df_stats['Buy and Hold Return']*100, text=df_stats['ticker'], mode="markers"), layout={'title': {'text':'Buy & Hold Return/Return'}})

df['return'] = (df['close'] / df['close'].shift(1))-1
# stat_fig = go.Figure(data=[go.Histogram(x=df['return'])])
equity_curve_fig = go.Figure(data=[go.Line(x=df['ts'], y=df['account_equity_tf'])], layout={'title': {'text':'account_equity_tf'}})
# mdd_daily_fig = go.Figure(data=[go.Line(x=df['ts'], y=df['Daily Drawdown'])]) # , layout={'title': {'text':'Drawdown'}}


# App layout
fig = make_subplots(
    rows = 9,
    cols = 1,
    specs=[[{"secondary_y": True}],
           [{"secondary_y": True}], 
           [{"secondary_y": True}],
           [{"secondary_y": True}],
           [{"secondary_y": True}],
           [{"secondary_y": True}],
           [{"secondary_y": True}],
           [{"secondary_y": True}],
           [{"secondary_y": True}]],
           
    row_width=[0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 1, 1]
)

# Add traces

ohlc_trace = go.Candlestick(x=df['ts'],
                    open=df['open'],
                    high=df['high'],
                    low=df['low'],
                    close=df['close'],
                    increasing_line_color= 'cyan', 
                    decreasing_line_color= 'gray'
                    )
fig.add_trace(ohlc_trace, secondary_y=False, row=1, col=1)

ohlc_trace = go.Candlestick(x=df['ts'],
                    open=df['open'],
                    high=df['high'],
                    low=df['low'],
                    close=df['close'],
                    increasing_line_color= 'cyan', 
                    decreasing_line_color= 'gray'
                    )
fig.add_trace(ohlc_trace, secondary_y=False, row=2, col=1)

# return_trace = go.Line(x=df['ts'], y=df['atrp'], name='atrp')
# fig.add_trace(return_trace, secondary_y=False, row=3, col=1)
# return_trace = go.Line(x=df['ts'], y=df['atrp_5'], name='atrp_5')
# fig.add_trace(return_trace, secondary_y=False, row=4, col=1)
# return_trace = go.Line(x=df['ts'], y=df['atrp_percent_change'], name='atrp')
# fig.add_trace(return_trace, secondary_y=True, row=2, col=1)
try:
    return_trace_tf = go.Line(x=df['ts'], y=df['tree_frog_sum_log_returns'], name='sum_log_returns' )
    fig.add_trace(return_trace_tf, secondary_y=False, row=5, col=1)
except:
    pass

equity_curve_fig_1 = go.Line(x=df['ts'], y=df['account_equity_tf'], line={'color':'black'}, name='Equity Curve')
fig.add_trace(equity_curve_fig_1, secondary_y=False, row=6, col=1)
# equity_curve_fig_1 = go.Line(x=df['ts'], y=df['account_equity_tf MA'], name='MA')
# fig.add_trace(equity_curve_fig_1, secondary_y=False, row=7, col=1)
scat_fig_trace = go.Line(x=df['ts'], y=df['Daily Drawdown'], name='Drawdown')


fig.add_trace(scat_fig_trace, secondary_y=False, row=8, col=1)


return_trace_tf = go.Line(x=df['ts'], y=df['account_equity_mr'], name='EC ts')
fig.add_trace(return_trace_tf, secondary_y=False, row=9, col=1)

# return_trace_tf = go.Line(x=df['ts'], y=df['account_equity_tf TF MA'], name='MA')
# fig.add_trace(return_trace_tf, secondary_y=False, row=10, col=1)


scatter_lines = {
    'long_upper_bound' : 'blue',
    'long_lower_bound' : 'black',
    # 'short_upper_bound' : 'red',
    # 'short_lower_bound' : 'red'
}

for key, value in scatter_lines.items():
    trace = go.Scatter(x=df['ts'], 
                        y=df[key],
                        line=dict(color=value, width=3),
                        name=key)
    fig.add_trace(trace, secondary_y=False, row=1, col=1)


trades = []
for i, g in df_trades.groupby(df_trades.index // 2):
    try:
        trades += [{
            "date" : [g.iloc[0]['Trade Date'], g.iloc[1]['Trade Date']],
            "price" : [g.iloc[0]['Fill Price'], g.iloc[1]['Fill Price']],
            "position" : g.iloc[0]['Position'],
            "pnl" : g.iloc[1]['P&L'],
        }]
    except:
        continue

for f in trades:
    if f["position"].split()[1] == "Long" and f["pnl"] > 0:
        color = "lime"
    elif f["position"].split()[1] == "Long" and f["pnl"] < 0: 
        color = "red"
    elif f["position"].split()[1] == "Short" and f["pnl"] > 0: 
        color = "lime"
    else:
        color = "red"
    trace = go.Scatter(
        x=f["date"],
        y=f["price"],
        mode="markers+lines",
        marker_color=color,
        showlegend=False
    )
    fig.add_trace(trace)

fig.update_yaxes(type="log", row=1, col=1)
fig.update_xaxes(rangeslider_visible=False)


fig.update_layout(
    legend=dict(
        x=0,
        y=1,
        traceorder="normal",
        font=dict(
            family="sans-serif",
            size=12,
            color="black"
        ),
        bgcolor = 'rgba(0,0,0,0)',
    ),
)

app.layout = html.Div([
    dcc.Tabs(id="tabs", value='tab-2', children=[
        dcc.Tab(label=f'{inst_id}', value='tab-2'),
        dcc.Tab(label='Portfolio Analytics', value='tab-1'),
    ]),
    html.Div(id='content')
])

@callback(Output('content', 'children'),
              Input('tabs', 'value'))

def render_content(tab):
    if tab == 'tab-1':
        return html.Div([
            dcc.Graph(
                figure=scat_fig,
                style={
                    'height':'700px',
                    'width':'50%',
                    'display':'inline-block'
                }
            ),
             dcc.Graph(
                figure=scat_fig_2,
                style={
                    'height':'700px',
                    'width':'50%',
                    'display':'inline-block'
                }
            ),
             dcc.Graph(
                figure=scat_fig_3,
                style={
                    'height':'700px',
                    'width':'50%',
                    'display':'inline-block'
                }
            ),            
        ])
    if tab == 'tab-2':
        return html.Div([
            # html.H3(f'{inst_id}'),
            dcc.Graph(
                figure=fig,
                style={
                        'height':'3400px',
                        'width':'100%',
                        'display':'inline-block'
                        }
            ),
        ])

if __name__ == '__main__':
    print("Dash is running")
    app.run_server(debug=True)