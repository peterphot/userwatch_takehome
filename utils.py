import psycopg2
import os


def get_jitsu_js_key(app: object) -> str:
    """
    Extract API secret from either local or prod
    :param app: web app object for determining whether or not it is running locally or in prod
    :return: the api key for jitsu integration
    """
    if app.debug:
        print(os.environ.get('jitsu_key'))
        return os.environ.get('jitsu_key')
    else:
        with open('/etc/secrets/JITSU_KEY') as f:
            jitsu_key = f.readlines()
        return jitsu_key[0]


def get_db_conn(app: object = None) -> object:
    """
    Gets PostgresDB connector
    :param app: web app object for determining whether or not it is running locally or in prod
    :return: Postgres connector
    """
    if app is None or app.debug:
        print('debug')
        return psycopg2.connect(host='singapore-postgres.render.com', database='zed_0t9u', user='zed_user',
                                password=os.environ.get('render_postgress_pw'))
    else:
        print('not debug')
        with open('/etc/secrets/POSTGRES_CONN_STRING') as f:
            con_string = f.readlines()
        return psycopg2.connect(con_string[0])
