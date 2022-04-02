import configparser
import json
from datetime import date
from pprint import pprint

import requests
from dateutil.relativedelta import relativedelta


def getGithubConfig(config_file):
    config = configparser.ConfigParser()
    config.read(config_file)
    return config['GITHUB']


def makeCall(query, token):
    response = requests.post("https://api.github.com/graphql",
                             headers={
                                 "Authorization": f"Bearer {token}"
                             },
                             json={
                                 "query": query
                             }
                             )
    json = response.json()
    if 'errors' in json:
        print("Github response contains errors:")
        pprint(json['errors'])
        exit(-1)
    else:
        return json["data"]


def getOrgMembers(org, token):
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
    pagingArgs = "first: 100"
    hasNextPage = True
    while hasNextPage:
        page = makeCall(identity_query % (org, pagingArgs), token)
        external_identities = page["organization"]["samlIdentityProvider"]["externalIdentities"]
        nodes.extend(external_identities["nodes"])
        hasNextPage = external_identities["pageInfo"]["hasNextPage"]
        endCursor = external_identities["pageInfo"]["endCursor"]
        pagingArgs = 'first: 100, after: "%s"' % endCursor
    filtered_nodes = [node for node in nodes if node["user"] is not None and "@" in node["samlIdentity"]["nameId"]]
    filtered_nodes.sort(key=lambda node: node["samlIdentity"]["nameId"])
    return filtered_nodes


def getUserPrHistory(org, identities, token, n_months=12):
    pullRequestQuery = """
    %s: search(query: "org:%s author:%s type:pr is:merged merged:%s..%s", type: ISSUE) {
      issueCount
    } 
    """
    user_pr_history = []
    thisMonth = date.today().replace(day=1)
    month_starts = [thisMonth + relativedelta(months=i - n_months + 1) for i in range(0, n_months + 1)]
    print("Start analyzing users:")
    for idx, identity in enumerate(identities):
        github_login = identity["user"]["login"]
        saml_email = identity["samlIdentity"]["nameId"]
        print("%s (%d/%d)" % (saml_email, idx + 1, len(identities)))
        composedQuery = "".join([
            pullRequestQuery % (month_starts[i].strftime("_%Y_%m_%d"), org, github_login, str(month_starts[i]),
                                str(month_starts[i + 1] + relativedelta(days=-1)))
            for i in range(0, n_months)
        ])
        monthly_prs = makeCall("{%s}" % composedQuery, token)
        user_pr_history.append({
            "saml_email": saml_email,
            "github_login": github_login,
            "pr_history": [{
                "month": month_starts[i].strftime("%Y-%m-%d"),
                "n_merged": monthly_prs[month_starts[i].strftime("_%Y_%m_%d")]["issueCount"]
            } for i in range(0, n_months)]
        })
    return user_pr_history


config = getGithubConfig('github.ini')
pat = config['PersonalAccessToken']
org = config['Organization']
identities = getOrgMembers(org, pat)
user_pr_history = getUserPrHistory(org, identities, pat, 12)
with open('user-prs.json', 'w') as fp:
    json.dump(user_pr_history, fp)
