import enum
import os
import time
import requests
from datetime import datetime, timedelta
import dateutil.parser as parser


def read_render_files(key_name):
    with open(f'/etc/secrets/{key_name}') as f:
        return f.readlines()[0]


def get_dbt_keys_ids(app=None):
    if app is not None and not app.debug:
        api_key = read_render_files('DBT_API_KEY')
        account_id = read_render_files('DBT_ACCOUNT_ID')
        job_id = read_render_files('DBT_JOB_ID')
        return api_key, account_id, job_id
    else:
        api_key = os.environ.get('DBT_API_KEY')
        account_id = 52946
            # os.environ.get('DBT_ACCOUNT_ID')
        job_id = 71371
            # os.environ.get('DBT_JOB_ID')
        return api_key, account_id, job_id


class DbtJobRunStatus(enum.IntEnum):
    QUEUED = 1
    STARTING = 2
    RUNNING = 3
    SUCCESS = 10
    ERROR = 20
    CANCELLED = 30


def trigger_job(API_KEY, ACCOUNT_ID, JOB_ID) -> int:
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


def get_job_run_status(job_run_id, API_KEY, ACCOUNT_ID):
    res = requests.get(
        url=f"https://cloud.getdbt.com/api/v2/accounts/{ACCOUNT_ID}/runs/{job_run_id}/",
        headers={'Authorization': f"Token {API_KEY}"},
    )

    res.raise_for_status()
    response_payload = res.json()
    return response_payload['data']['status']


def get_runs(API_KEY, ACCOUNT_ID):
    res = requests.get(
        url=f"https://cloud.getdbt.com/api/v2/accounts/{ACCOUNT_ID}/runs/",
        headers={'Authorization': f"Token {API_KEY}"},
    )

    res.raise_for_status()
    response_payload = res.json()
    return response_payload['data']


def get_job_status(API_KEY, ACCOUNT_ID, JOB_ID):
    res = requests.get(
        url=f"https://cloud.getdbt.com/api/v2/accounts/{ACCOUNT_ID}/jobs/{JOB_ID}/",
        headers={'Authorization': f"Token {API_KEY}"},
    )

    res.raise_for_status()
    response_payload = res.json()
    return response_payload['data']['state']


def run():
    api_key, account_id, job_id = get_dbt_keys_ids()
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
