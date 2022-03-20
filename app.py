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
    horse_id = request.args.get('horse_id')
    query = f'select * from horses where horse_id = {horse_id}'
    return show_horse_visuals(horse_id, 'table', query, None, None, 'Horse info')


@app.route('/show_start_gates', methods=['POST', 'GET'])
def show_start_gates_callback():
    horse_id = request.args.get('horse_id')
    query = f"""
            select
                gate
                , number_of_starts
            from gate_summary
            where True
                and horse_id = {horse_id}
    """
    return show_horse_visuals(horse_id,
                              'bar_chart', query, 'gate',
                              'number_of_starts', 'Number of races started from each gate')


@app.route('/show_places', methods=['POST', 'GET'])
def show_places_callback():
    horse_id = request.args.get('horse_id')
    query = f"""
            select
                place
                , number_of_places
            from place_summary
            where True
                and horse_id = {horse_id}
            order by 1 asc
    """
    return show_horse_visuals(horse_id,
                              'bar_chart', query, 'place',
                              'number_of_places', 'Number of places')


@app.route('/show_classes', methods=['POST', 'GET'])
def show_classes_callback():
    horse_id = request.args.get('horse_id')
    query = f"""
        select
            class
            , n_races
        from class_summary
        where True
            and horse_id = {horse_id}
        order by 1 asc
    """
    return show_horse_visuals(horse_id,
                              'bar_chart', query, 'class',
                              'n_races', 'Number of races per class')


@app.route('/show_distances', methods=['POST', 'GET'])
def show_distances_callback():
    horse_id = request.args.get('horse_id')
    query = f"""
        select
            distance
            , n_races
        from distance_summary
        where True
            and horse_id = {horse_id}
        order by 1 asc
    """
    return show_horse_visuals(horse_id,
                              'bar_chart', query, 'distance',
                              'n_races', 'Number of races per distance')


@app.route('/show_earnings', methods=['POST', 'GET'])
def show_earnings_callback():
    horse_id = request.args.get('horse_id')
    query = f"""
        select
            horse_id
            , earnings
            , entry_fees
            , earnings - entry_fees as net_profit
        from earnings_summary
        where True
            and horse_id = {horse_id}
    """
    return show_horse_visuals(horse_id, 'table', query, None, None, 'Earnings summary (values are in ETH)')



# Pages


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/horses')
def horse_data():
    horse_id = 91403
    query = f'select * from horses where horse_id = {horse_id}'
    return render_template('horses.html', summary_table=show_horse_visuals(horse_id, 'table', query,
                                                                           None, None, 'Horse info'))


@app.route('/races')
def race_data():
    return render_template('races.html')  # ,  graphJSON=gm()


# Horse Visuals


def run_horse_query(horse_id, conn):
    return pd.read_sql_query(f'select * from horses where horse_id = {horse_id}', conn)


def show_horse_visuals(horse_id, vis_type, query, x_col, y_col, fig_title):
    horse_id = int(horse_id)
    assert (horse_id >= 0) and (horse_id <= 358847), 'Horse ID must be an integer between 0 and 358847'

    conn = get_db_conn()

    horse_df = run_horse_query(horse_id, conn)
    vis_df = pd.read_sql_query(query, conn)
    horse_name = horse_df.loc[0, 'name']

    if vis_type == 'table':
        fig = go.Figure(data=[go.Table(
            header=dict(values=list(vis_df.columns),
                        fill_color='paleturquoise',
                        align='left'),
            cells=dict(values=[vis_df[c] for c in vis_df.columns],
                       fill_color='lavender',
                       align='left'))
        ])
        fig.update_layout(title=f'{fig_title} for {horse_name} (horse_id:{horse_id})')
    elif vis_type == 'bar_chart':
        fig = px.bar(vis_df, x=x_col, y=y_col,
                     title=f'{fig_title} for {horse_name} (horse_id:{horse_id})',
                     # labels={
                     #     "gate": "Start gate",
                     #     "number_of_starts": "Number of Starts"}
                     )
        fig.update_xaxes(type='category')
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

#%%
