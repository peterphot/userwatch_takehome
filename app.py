from flask import Flask, config, render_template, request
import pandas as pd
import json
import plotly
import plotly.express as px
import plotly.graph_objects as go
import psycopg2
import os

app = Flask(__name__)


@app.route('/search_horse', methods=['POST', 'GET'])
def search_horse_callback():
    return show_horse_summary_table(request.args.get('data'))


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/horses')
def horse_data():
    return render_template('horses.html', graphJSON=show_horse_summary_table())


@app.route('/races')
def race_data():
    return render_template('races.html')  # ,  graphJSON=gm()


def run_horse_query(horse_id, conn):
    return pd.read_sql_query(f'select * from horses where horse_id = {horse_id}', conn)


def show_horse_summary_table(horse_id=91403):
    horse_id = int(horse_id)
    assert (horse_id >= 0) and (horse_id <= 358847), 'Horse ID must be an integer between 0 and 358847'

    if app.debug:
        print('debug')
        conn = psycopg2.connect(host='singapore-postgres.render.com', database='zed_0t9u', user='zed_user',
                                password=os.environ.get('render_postgress_pw'))
    else:
        print('not debug')
        with open('/etc/secrets/POSTGRES_CONN_STRING') as f:
            con_string = f.readlines()
        conn = psycopg2.connect(con_string[0])

    horse_df = run_horse_query(horse_id, conn)

    fig = go.Figure(data=[go.Table(
        header=dict(values=list(horse_df.columns),
                    fill_color='paleturquoise',
                    align='left'),
        cells=dict(values=[horse_df[c] for c in horse_df.columns],
                   fill_color='lavender',
                   align='left'))
    ])

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    # print(fig.data[0])
    # fig.data[0]['staticPlot']=True

    return graphJSON
