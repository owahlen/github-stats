import configparser
import pprint

import requests

config = configparser.ConfigParser()
config.read('github.ini')

token = config['GITHUB']['PersonalAccessToken']
org = config['GITHUB']['Organization']


def batch(iterable, n=1):
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx:min(ndx + n, l)]


def makeCall(query):
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
        pprint.pprint(json['errors'])
        exit(-1)
    else:
        return json["data"]


def getOrgMembers(org):
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
        page = makeCall(userQuery % (org, membersWithRoleArgs))
        nodes.extend(page["organization"]["membersWithRole"]["nodes"])
        hasNextPage = page["organization"]["membersWithRole"]["pageInfo"]["hasNextPage"]
        endCursor = page["organization"]["membersWithRole"]["pageInfo"]["endCursor"]
        membersWithRoleArgs = 'first: 100, after: "%s"' % endCursor
    return nodes


def getPrCountDict(org, users):
    pullRequestQuery = """
    %s: search(query: "org:%s author:%s type:pr is:merged created:>=2022-03-01 created:<2022-04-01", type: ISSUE) {
      issueCount
    } 
    """
    keyDict = {}
    for idx, user in enumerate(users):
        keyDict[f"user{idx}"] = user["login"]

    keys = list(keyDict.keys())
    for keyBatch in batch(keys, 10):
        composedQuery = "".join([
            pullRequestQuery % (t, org, keyDict[t])
            for t in keyBatch
        ])
        result = makeCall("{%s}" % composedQuery)
        print(result)


users = getOrgMembers(org)
prCounts = getPrCountDict(org, users)

# match the original user login
# stats = {}
# for it in result.keys():
#     stats[keyList[it]] = result[it]["issueCount"]
#
# print(stats)
