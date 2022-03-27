import json
import plotly
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from scipy.spatial.distance import euclidean
from math import log2, sqrt
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from utils import get_db_conn
import plotly.express as px
import plotly.graph_objects as go


def cross_entropy(p, q):
    return -sum([q[i]*log2(q[i]/p[i]) for i in range(len(q))])


def find_user_matches(app, ip_addr):
    conn = get_db_conn(app)
    vec_means_df = pd.read_sql_query('select * from detect.vector_means', conn)
    vec_means_df = vec_means_df.set_index('cluster_id')
    match_vec_query = f"""
                        select
                          *
                        from (
                            select
                              *
                              , row_number() over(partition by source_ip order by session_start_local_time desc) rn
                          from detect.array_vectors
                          where true
                              and source_ip = '{ip_addr}'
                        )p
                        where true
                          and rn = 1
    """
    matching_df = pd.read_sql_query(match_vec_query, conn)

    matching_df['prop_vector'] = matching_df['prop_vector'].apply(lambda x: np.asarray(x, dtype=float))
    matching_df['n_vector'] = matching_df['n_vector'].apply(lambda x: np.asarray(x, dtype=float))
    closest_clusters = [np.argmax(cosine_similarity(row['prop_vector'].reshape(1,-1), vec_means_df.to_numpy())) for i, row in matching_df.iterrows()]
    matching_df['closest_cluster'] = closest_clusters
    search_ci = matching_df.loc[0, 'closest_cluster']
    population_query = f"""
                        select
                            av.session_id
                            , av.source_ip
                            , av.event_name_vector
                            , av.prop_vector
                            , av.n_vector
                            , av.session_start_local_time
                        from detect.array_vectors av
                        where True
    """
    population_df = pd.read_sql_query(population_query, conn)
    population_df['prop_vector'] = population_df['prop_vector'].apply(lambda x: np.asarray(x, dtype=float))
    population_df['n_vector'] = population_df['n_vector'].apply(lambda x: np.asarray(x, dtype=float))

    entropies = []
    similarities = []
    seshes = []

    for i, row in matching_df.iterrows():
        scaler = MinMaxScaler()
        scaled_pop_n_vec = scaler.fit_transform(population_df['n_vector'].tolist())

        entropies.append([cross_entropy(a+0.00000000001, row['prop_vector']+0.00000000001) for a in population_df['prop_vector'].to_numpy()])
        similarities.append([euclidean(a.reshape(1,-1), scaler.transform(row['n_vector'].reshape(1,-1))) for a in scaled_pop_n_vec])
        seshes.append(population_df['session_id'].to_numpy())

    matches = []
    for uu, sim, ent in zip(seshes[0], similarities[0], entropies[0]):
        if sim <= 0.5 and ent <= 0.6:
            matches.append(uu)

    vis_df = population_df[population_df['session_id'].isin(matches)]
    fig = go.Figure(data=[go.Table(
        header=dict(values=list(vis_df.columns),
                    fill_color='paleturquoise',
                    align='left'),
        cells=dict(values=[vis_df[c] for c in vis_df.columns],
                   fill_color='lavender',
                   align='left'))
    ])
    cnt = vis_df.shape[0]
    fig.update_layout(title=f'Your ({ip_addr}) most recent session matches with the following {cnt} other user sessions')

    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
