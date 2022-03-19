from flask import Flask, config, render_template, request
import pandas as pd
import json
import plotly
import plotly.express as px
import plotly.graph_objects as go
import psycopg2
import os

app = Flask(__name__)


# Utilities


def get_db_conn():
    if app.debug:
        print('debug')
        return psycopg2.connect(host='singapore-postgres.render.com', database='zed_0t9u', user='zed_user',
                                password=os.environ.get('render_postgress_pw'))
    else:
        print('not debug')
        with open('/etc/secrets/POSTGRES_CONN_STRING') as f:
            con_string = f.readlines()
        return psycopg2.connect(con_string[0])


# Callbacks


@app.route('/search_horse', methods=['POST', 'GET'])
def search_horse_callback():
    return show_horse_summary_table(request.args.get('horse_id'))


@app.route('/show_start_gates', methods=['POST', 'GET'])
def show_start_gates_callback():
    return show_start_gates(request.args.get('horse_id'))


# Pages


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/horses')
def horse_data():
    return render_template('horses.html', summary_table=show_horse_summary_table())#, selectedHorseVis=show_start_gates()


@app.route('/races')
def race_data():
    return render_template('races.html')  # ,  graphJSON=gm()


# Horse Visuals


def run_horse_query(horse_id, conn):
    return pd.read_sql_query(f'select * from horses where horse_id = {horse_id}', conn)


def show_horse_summary_table(horse_id=91403):
    horse_id = int(horse_id)
    assert (horse_id >= 0) and (horse_id <= 358847), 'Horse ID must be an integer between 0 and 358847'

    conn = get_db_conn()

    horse_df = run_horse_query(horse_id, conn)

    fig = go.Figure(data=[go.Table(
        header=dict(values=list(horse_df.columns),
                    fill_color='paleturquoise',
                    align='left'),
        cells=dict(values=[horse_df[c] for c in horse_df.columns],
                   fill_color='lavender',
                   align='left'))
    ])

    summary_table = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    # print(fig.data[0])
    # fig.data[0]['staticPlot']=True
    print('sum done')
    return summary_table


def show_start_gates(horse_id=91403):
    horse_id = int(horse_id)
    assert (horse_id >= 0) and (horse_id <= 358847), 'Horse ID must be an integer between 0 and 358847'

    conn = get_db_conn()

    horse_df = run_horse_query(horse_id, conn)

    query = f"""
    with gates as (
        select distinct
            gate
        from races
    )
    
    select
        gates.gate
        , count(races.gate) as number_of_starts
    from gates
    left join (select * from races where horse_id = {horse_id}) races
        on gates.gate = races.gate
    where True
    group by 1
    limit 100
    """
    gate_df = pd.read_sql_query(query, conn)

    horse_name = horse_df.loc[0, 'name']

    fig = px.bar(gate_df, x='gate', y='number_of_starts',
                 title=f'Number of races started from each gate for {horse_name} (horse_id:{horse_id})',
                 labels={
                     "gate": "Start gate",
                     "number_of_starts": "Number of Starts"})
    fig.update_xaxes(type='category')

    startGateVis = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    print('gate done')
    return startGateVis
