import enum
import os
import time
import requests
from datetime import datetime, timedelta
import dateutil.parser as parser


def read_render_files(key_name: str) -> object:
    """
    Used for getting secrets from prod environment for authorising dbt api
    :param key_name: name of the key file
    :return: secret string
    """
    with open(f'/etc/secrets/{key_name}') as f:
        return f.readlines()[0]


def get_dbt_keys_ids(app: object = None) -> str | str | str:
    """
    Gets secrets for dbt auth from either local or prod
    :param app:
    :return:
    """
    if app is not None and not app.debug:
        api_key = read_render_files('DBT_API_KEY')
        account_id = read_render_files('DBT_ACCOUNT_ID')
        job_id = read_render_files('DBT_JOB_ID')
        return api_key, account_id, job_id
    else:
        api_key = os.environ.get('DBT_API_KEY')
        account_id = os.environ.get('DBT_ACCOUNT_ID')
        job_id = os.environ.get('DBT_JOB_ID')
        return api_key, account_id, job_id


class DbtJobRunStatus(enum.IntEnum):
    QUEUED = 1
    STARTING = 2
    RUNNING = 3
    SUCCESS = 10
    ERROR = 20
    CANCELLED = 30


def trigger_job(API_KEY: str, ACCOUNT_ID: int, JOB_ID: int) -> int:
    """
    Triggers a dbt job to run
    :param API_KEY: dbt api key
    :param ACCOUNT_ID: account id for relevant project
    :param JOB_ID: job id to trigger
    :return: id of the triggered run
    """
    res = requests.post(
        url=f"https://cloud.getdbt.com/api/v2/accounts/{ACCOUNT_ID}/jobs/{JOB_ID}/run/",
        headers={'Authorization': f"Token {API_KEY}"},
        json={
            'cause': f"Flask requested run",
        }
    )

    try:
        res.raise_for_status()
    except:
        print(f"API token (last four): ...{API_KEY[-4:]}")
        raise

    response_payload = res.json()
    return response_payload['data']['id']


def get_job_run_status(job_run_id: int, API_KEY: str, ACCOUNT_ID: int) -> str:
    """
    gets status of a run
    :param job_run_id: Id of the job run
    :param API_KEY: dbt api key
    :param ACCOUNT_ID: account id for relevant project
    :return: run status
    """
    res = requests.get(
        url=f"https://cloud.getdbt.com/api/v2/accounts/{ACCOUNT_ID}/runs/{job_run_id}/",
        headers={'Authorization': f"Token {API_KEY}"},
    )

    res.raise_for_status()
    response_payload = res.json()
    return response_payload['data']['status']


def get_runs(API_KEY: str, ACCOUNT_ID: int) -> list:
    """
    get dbt run history for account
    :param API_KEY: dbt api key
    :param ACCOUNT_ID: account id for relevant project
    :return: run history
    """
    res = requests.get(
        url=f"https://cloud.getdbt.com/api/v2/accounts/{ACCOUNT_ID}/runs/",
        headers={'Authorization': f"Token {API_KEY}"},
    )
    res.raise_for_status()
    response_payload = res.json()
    return response_payload['data']


def get_job_status(API_KEY: str, ACCOUNT_ID: int, JOB_ID: int) -> int:
    """
    gets current status of the job
    :param API_KEY: dbt api key
    :param ACCOUNT_ID: account id for relevant project
    :param JOB_ID: job id to trigger
    :return: current job state
    """
    res = requests.get(
        url=f"https://cloud.getdbt.com/api/v2/accounts/{ACCOUNT_ID}/jobs/{JOB_ID}/",
        headers={'Authorization': f"Token {API_KEY}"},
    )

    res.raise_for_status()
    response_payload = res.json()
    return response_payload['data']['state']


def run(app: object) -> str:
    """
    Checks the job isn't currently running and hasn't run recently.
    If criteria are satisfied runs dbt job and polls for status.
    :param app: web app object for determining whether or not it is running locally or in prod
    :return: success of run
    """
    api_key, account_id, job_id = get_dbt_keys_ids(app)
    run_log = get_runs(api_key, account_id)
    last_run_time = [i['finished_at'] for i in run_log][-1]

    if last_run_time is not None and (datetime.utcnow() - parser.parse(last_run_time).replace(tzinfo=None)).total_seconds()/60.0 < 5.0:
        return 'too soon'

    if last_run_time is None or get_job_status(api_key, account_id, job_id) in (DbtJobRunStatus.STARTING, DbtJobRunStatus.RUNNING):
        return 'currently running'

    job_run_id = trigger_job(api_key, account_id, job_id)
    print(f"job_run_id = {job_run_id}")

    while True:
        time.sleep(5)

        status = get_job_run_status(job_run_id, api_key, account_id)

        print(f"status = {status}")

        if status == DbtJobRunStatus.SUCCESS:
            return 'success'
        elif status == DbtJobRunStatus.ERROR or status == DbtJobRunStatus.CANCELLED:
            raise Exception("Failure!")


if __name__ == '__main__':
    run()

#%%
