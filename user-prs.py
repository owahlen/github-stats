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
    userQuery = """
    { 
      organization(login: "%s") {
        membersWithRole(%s) {
          pageInfo {
            startCursor
            hasNextPage
            endCursor
          }
          nodes {
            login
          }
        }
      }
    }
    """
    nodes = []
    membersWithRoleArgs = "first: 100"
    hasNextPage = True
    while hasNextPage:
        page = makeCall(userQuery % (org, membersWithRoleArgs), token)
        nodes.extend(page["organization"]["membersWithRole"]["nodes"])
        hasNextPage = page["organization"]["membersWithRole"]["pageInfo"]["hasNextPage"]
        endCursor = page["organization"]["membersWithRole"]["pageInfo"]["endCursor"]
        membersWithRoleArgs = 'first: 100, after: "%s"' % endCursor
    return nodes


def getUserPrHistory(org, users, token, n_months=12):
    pullRequestQuery = """
    %s: search(query: "org:%s author:%s type:pr is:merged merged:%s..%s", type: ISSUE) {
      issueCount
    } 
    """
    user_pr_history = {}
    thisMonth = date.today().replace(day=1)
    month_starts = [thisMonth + relativedelta(months=i - n_months + 1) for i in range(0, n_months + 1)]
    print("Start analyzing users:")
    for idx, user in enumerate(users):
        print("%s (%d/%d)" % (user["login"], idx + 1, len(users)))
        composedQuery = "".join([
            pullRequestQuery % (month_starts[i].strftime("_%Y_%m_%d"), org, user["login"], str(month_starts[i]),
                                str(month_starts[i + 1] + relativedelta(days=-1)))
            for i in range(0, n_months)
        ])
        monthly_prs = makeCall("{%s}" % composedQuery, token)
        user_pr_history[user["login"]] = [monthly_prs[month_starts[i].strftime("_%Y_%m_%d")]["issueCount"] for i in
                                          range(0, n_months)]
    return user_pr_history


config = getGithubConfig('github.ini')
pat = config['PersonalAccessToken']
org = config['Organization']
users = getOrgMembers(org, pat)
user_pr_history = getUserPrHistory(org, users, pat, 12)
with open('user-prs.json', 'w') as fp:
    json.dump(user_pr_history, fp)
