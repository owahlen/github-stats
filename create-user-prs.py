import configparser
import json
from datetime import date
from pprint import pprint

import requests
from dateutil.relativedelta import relativedelta

def get_github_config(config_file):
    parser = configparser.ConfigParser()
    parser.read(config_file)
    return parser['GITHUB']

def make_call(query, token):
    response = requests.post("https://api.github.com/graphql",
                             headers={
                                 "Authorization": f"Bearer {token}"
                             },
                             json={
                                 "query": query
                             }
                             )
    response_json = response.json()
    if 'errors' in response_json:
        print("GitHub response contains errors:")
        pprint(response_json['errors'])
        exit(-1)

    if "data" not in response_json:
        print("Unexpected GitHub API response:")
        pprint(response_json)  # Print the full response for debugging
        exit(-1)

    return response_json["data"]

def get_org_members(org_name, token):
    identity_query = """
    { 
      organization(login: "%s") {
        samlIdentityProvider {
          ssoUrl
          externalIdentities(%s) {
            pageInfo {
              startCursor
              hasNextPage
              endCursor
            }
            nodes {
              guid
              samlIdentity {
                nameId
              }
              user {
                login
              }
            }
          }
        }
      }
    }
    """
    nodes = []
    paging_args = "first: 100"
    has_next_page = True
    while has_next_page:
        page = make_call(identity_query % (org_name, paging_args), token)
        external_identities = page["organization"]["samlIdentityProvider"]["externalIdentities"]
        nodes.extend(external_identities["nodes"])
        has_next_page = external_identities["pageInfo"]["hasNextPage"]
        end_cursor = external_identities["pageInfo"]["endCursor"]
        paging_args = 'first: 100, after: "%s"' % end_cursor
    filtered_nodes = [node for node in nodes if node["user"] is not None and "@" in node["samlIdentity"]["nameId"]]
    filtered_nodes.sort(key=lambda node: node["samlIdentity"]["nameId"])
    return filtered_nodes

def get_user_pr_history(org_name, member_identities, token, n_months=12):
    pull_request_query = """
    %s: search(query: "org:%s author:%s type:pr is:merged merged:%s..%s", type: ISSUE) {
      issueCount
    } 
    """
    pr_history_data = []
    this_month = date.today().replace(day=1)
    month_starts = [this_month + relativedelta(months=i - n_months + 1) for i in range(0, n_months + 1)]
    print("Start analyzing users:")
    for idx, identity in enumerate(member_identities):
        github_login = identity["user"]["login"]
        saml_email = identity["samlIdentity"]["nameId"]
        print("%s (%d/%d)" % (saml_email, idx + 1, len(member_identities)))
        composed_query = "".join([
            pull_request_query % (month_starts[i].strftime("_%Y_%m_%d"), org_name, github_login, str(month_starts[i]),
                                str(month_starts[i + 1] + relativedelta(days=-1)))
            for i in range(0, n_months)
        ])
        monthly_prs = make_call("{" + composed_query + "}", token)
        pr_history_data.append({
            "saml_email": saml_email,
            "github_login": github_login,
            "pr_history": [{
                "month": month_starts[i].strftime("%Y-%m-%d"),
                "n_merged": monthly_prs[month_starts[i].strftime("_%Y_%m_%d")]["issueCount"]
            } for i in range(0, n_months)]
        })
    return pr_history_data

config = get_github_config('github.ini')
pat = config['PersonalAccessToken']
org = config['Organization']
identities = get_org_members(org, pat)
user_pr_history = get_user_pr_history(org, identities, pat, 12)

with open('user-prs.json', 'w', encoding='utf-8') as fp:
    json.dump(user_pr_history, fp)
