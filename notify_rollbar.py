import requests
import subprocess

from environs import Env

env = Env()
env.read_env()

git_process = subprocess.run(
    ['git', 'log', '-n', '1', '--pretty=format:%H'],
    capture_output=True,
    check=True
)
revision = git_process.stdout.decode()

response = requests.post(
    'https://api.rollbar.com/api/1/deploy/',
    json={
        'environment': env('ROLLBAR_ENV_LABEL', 'production'),
        'revision': revision,
    },
    headers={
        'X-Rollbar-Access-Token': env('ROLLBAR_TOKEN'),
    },
    timeout=3
)

response.raise_for_status()
