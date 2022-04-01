import requests
import configparser
import pprint

config = configparser.ConfigParser()
config.read('github.ini')

token = config['GITHUB']['PersonalAccessToken']
org = config['GITHUB']['Organization']

userQuery = """
{ 
  organization(login: "%s"){
    membersWithRole(first: 1000){
      nodes {
        login
      }
    }
  }
}
"""
pullRequestQuery = """
  %s: search(query: "org:%s author:%s type:pr is:merged", type: ISSUE){
    issueCount
  } 
"""

def makeCall(query):
    response = requests.post("https://api.github.com/graphql",
        headers = {
            "Authorization": f"Bearer {token}"
        },
        json = {
            "query": query
        }
    )
    json = response.json()
    if json['errors']:
        pprint.pprint(json['errors'])
        exit(-1)
    else:
        return json["data"]

userList = makeCall(userQuery % org)

#build a list of keys matching user (user0: johndoe ....)
keyList = {}
for idx, user in enumerate(userList["organization"]["membersWithRole"]["nodes"]):
    keyList[f"user{idx}"] = user["login"]

#build the query
builtQuery = "".join([
    pullRequestQuery % (t, org, keyList[t]) 
    for t in keyList.keys()
])
result = makeCall("{%s}" % builtQuery)

#match the original user login
stats = {}
for it in result.keys():
    stats[keyList[it]] = result[it]["issueCount"]

print(stats)
