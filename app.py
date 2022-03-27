from flask import Flask, render_template, request, jsonify
import pandas as pd
import json
import plotly
import plotly.express as px
import plotly.graph_objects as go
import dbt_runner
from utils import get_db_conn, get_jitsu_js_key
from user_matching import find_user_matches

app = Flask(__name__)


# Utilities


@app.route("/populate_cities_dropdown", methods=["POST", "GET"])
def populate_cities_dropdown() -> object:
    """
    Gets the value of the country selected in drop down list and generates a list of relevant cities to populate
    the cities dropdown list.
    :return: jsonified list of cities
    """
    if request.method == 'POST':
        country = request.form['country']
        print(country)
        conn = get_db_conn(app)
        country_df = pd.read_sql_query(f"select distinct city from countries where country = '{country}'", conn)
        return jsonify([{c[0]: c[1][0]} for c in zip(['city']*len(country_df.values), country_df.values.tolist())])


# Callbacks


@app.route('/search_horse', methods=['POST', 'GET'])
def search_horse_callback() -> object:
    """
    Takes the entered horse id value and gets all horse related information for displaying
    :return: jsonified plotly table
    """
    horse_id = request.args.get('horse_id')
    query = f'select * from horses where horse_id = {horse_id}'
    return show_horse_visuals(horse_id, 'table', query, None, None, 'Horse info')


@app.route('/show_start_gates', methods=['POST', 'GET'])
def show_start_gates_callback() -> object:
    """
    Generates figure upon show gates button press
    :return: jsonified plotly bar chart
    """
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
def show_places_callback() -> object:
    """
    Generates figure upon show places button press
    :return: jsonified plotly bar chart
    """
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
def show_classes_callback() -> object:
    """
    Generates figure upon show classes button press
    :return: jsonified plotly bar chart
    """
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
def show_distances_callback() -> object:
    """
    Generates figure upon show distances button press
    :return: jsonified plotly bar chart
    """
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
def show_earnings_callback() -> object:
    """
    Generates figure upon show earnings button press
    :return: jsonified plotly table
    """
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


@app.route('/search_race_info', methods=['POST', 'GET'])
def search_race_info_callback() -> object:
    """
    Extracts data from dropdown menus and generates table of races
    :return: jsonified plotly table
    """
    country = request.args.get('country')
    city = request.args.get('city')
    race_class = request.args.get('class')
    distance = request.args.get('distance')
    return show_race_info(country, city, race_class, distance)


@app.route('/search_race_result', methods=['POST', 'GET'])
def search_race_result_callback() -> object:
    """
    Takes searched race id and makes a table of race results
    :return: jsonified plotly table
    """
    race_id = request.args.get('race_id')
    return show_race_result(race_id)


@app.route('/match_user', methods=['POST', 'GET'])
def match_user_callback() -> object:
    """
    Get users IP address.
    Runs the dbt pipeline.
    Gets users who have similar interactions with the website.
    :return: plotly table
    """
    ip_addr = request.args.get('ip_address')
    dbt_runner.run(app)
    return find_user_matches(app, ip_addr)


# Pages


@app.route('/')
def index() -> object:
    """
    Renders the home page
    :return: rendered html
    """
    return render_template('index.html', jitsu_key=get_jitsu_js_key(app))


@app.route('/horses')
def horse_data() -> object:
    """
    Renders the horse info page
    :return: rendered html
    """
    horse_id = 91403
    query = f'select * from horses where horse_id = {horse_id}'
    return render_template('horses.html', summary_table=show_horse_visuals(horse_id, 'table', query,
                                                                           None, None, 'Horse info'),
                           jitsu_key=get_jitsu_js_key(app))


@app.route('/races')
def race_data() -> object:
    """
    Renders the race info page
    :return: rendered html
    """
    conn = get_db_conn(app)
    country_df = pd.read_sql_query('select distinct country from countries', conn)
    distance_df = pd.read_sql_query('select distinct distance from races_info', conn)
    race_df = pd.read_sql_query('select distinct class from races_info', conn)
    return render_template('races.html', countries=country_df.values.tolist(),
                           classes=race_df.values.tolist(),
                           distances=distance_df.values.tolist(), jitsu_key=get_jitsu_js_key(app))


@app.route('/user_matching')
def user_matching() -> object:
    """
    Renders the page for matching users
    :return: rendered html
    """
    return render_template('user_matching.html')


@app.route('/how_it_works')
def how_it_works() -> object:
    """
    Renders the flow chart page
    :return: rendered html
    """
    return render_template('how_it_works.html', jitsu_key=get_jitsu_js_key(app))

# Horse Visuals


def run_horse_query(horse_id: int, conn: object) -> pd.DataFrame:
    """
    Run query to get horse information
    :param horse_id: Id of the horse being searched
    :param conn: postgres connector
    :return: data frame of horse data
    """
    return pd.read_sql_query(f'select * from horses where horse_id = {horse_id}', conn)


def show_horse_visuals(horse_id: int, vis_type: str, query: str, x_col: str, y_col: str, fig_title: str) -> object:
    """
    Runs a query to extract the queries information then generates a plotly figure to display.

    :param horse_id: Id of the horse being searched
    :param vis_type: table or bar_chart
    :param query: Postgres query to get relevant info
    :param x_col: Name of the column to plot on x axis
    :param y_col: Name of the column to plot on y axis
    :param fig_title: title of the figure to display
    :return: jsonified visualisation object
    """
    horse_id = int(horse_id)
    assert (horse_id >= 0) and (horse_id <= 358847), 'Horse ID must be an integer between 0 and 358847'

    conn = get_db_conn(app)

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


def show_race_info(country: str, city: str, race_class: float, distance: float) -> object:
    """
    Takes the request race parameters, builds the postgres query and then generates table for visualising
    :param country: country queried
    :param city: city queried
    :param race_class: race class queried
    :param distance: race distance queried
    :return: jsonified visualisation object
    """
    conn = get_db_conn(app)

    query = f"""
        select
            *
        from races_info
        where True
    """
    if country != "":
        query = query + f"and country = '{country}'\n"
    if city != "":
        query = query + f"and city = '{city}'\n"
    if race_class != "":
        query = query + f"and class = '{race_class}'\n"
    if distance != "":
        query = query + f"and distance = '{distance}'\n"

    query = query + "limit 100"
    vis_df = pd.read_sql_query(query, conn)

    fig = go.Figure(data=[go.Table(
        header=dict(values=list(vis_df.columns),
                    fill_color='paleturquoise',
                    align='left'),
        cells=dict(values=[vis_df[c] for c in vis_df.columns],
                   fill_color='lavender',
                   align='left'))
    ])
    fig.update_layout(title=f'Showing 100 races in {country}, {city}', height=500)

    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


def show_race_result(race_id: str) -> object:
    """
    Takes the race ID searched, queries for information and returns table
    :param race_id: the race identifier
    :return: jsonified visualisation object
    """
    conn = get_db_conn(app)

    query = f"""
        select
            name
            , horse_id
            , stable_name
            , place
            , gate
        from race_results
        where True
            and race_id = '{race_id}'
        order by 4 asc
    """

    vis_df = pd.read_sql_query(query, conn)

    fig = go.Figure(data=[go.Table(
        header=dict(values=list(vis_df.columns),
                    fill_color='paleturquoise',
                    align='left'),
        cells=dict(values=[vis_df[c] for c in vis_df.columns],
                   fill_color='lavender',
                   align='left'))
    ])
    fig.update_layout(title=f'Showing race result for {race_id}')

    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
#%%
