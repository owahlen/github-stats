# github_utils.py

import configparser
import requests
from pprint import pprint

def get_github_config(config_file):
    parser = configparser.ConfigParser()
    parser.read(config_file)
    if 'GITHUB' not in parser:
        raise ValueError("Missing [GITHUB] section in config file")
    required_keys = ['PersonalAccessToken', 'Organization']
    for key in required_keys:
        if key not in parser['GITHUB']:
            raise ValueError(f"Missing key '{key}' in config file")
    return parser['GITHUB']


def make_call(query, token):
    response = requests.post(
        "https://api.github.com/graphql",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": query}
    )

    if response.status_code != 200:
        print(f"GitHub API error {response.status_code}")
        pprint(response.json())
        exit(-1)

    response_json = response.json()
    if 'errors' in response_json:
        print("GitHub response contains errors:")
        pprint(response_json['errors'])
        exit(-1)

    if "data" not in response_json:
        print("Unexpected GitHub API response:")
        pprint(response_json)
        exit(-1)

    return response_json["data"]
