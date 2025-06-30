import json
import time

from github_utils import get_github_config, make_call


def get_repositories(org_name, token):
    repos = []
    has_next_page = True
    after = None
    print("Fetching repositories...")
    while has_next_page:
        paging = f', after: "{after}"' if after else ""
        query = f"""
        {{
          organization(login: "{org_name}") {{
            repositories(first: 100{paging}) {{
              pageInfo {{
                hasNextPage
                endCursor
              }}
              nodes {{
                name
                isArchived
              }}
            }}
          }}
        }}
        """
        data = make_call(query, token)
        repo_data = data["organization"]["repositories"]
        active_repos = [node["name"] for node in repo_data["nodes"] if not node["isArchived"]]
        repos.extend(active_repos)
        has_next_page = repo_data["pageInfo"]["hasNextPage"]
        after = repo_data["pageInfo"]["endCursor"]
    print(f"Found {len(repos)} active (non-archived) repositories.")
    return repos


def get_commits_for_repo(org_name, repo_name, token):
    commits = []
    has_next_page = True
    after = None
    print(f"Fetching commits for {repo_name}...")

    while has_next_page:
        paging = f', after: "{after}"' if after else ""
        query = f"""
        {{
          repository(owner: "{org_name}", name: "{repo_name}") {{
            defaultBranchRef {{
              target {{
                ... on Commit {{
                  history(first: 100{paging}) {{
                    pageInfo {{
                      hasNextPage
                      endCursor
                    }}
                    edges {{
                      node {{
                        oid
                        committedDate
                        messageHeadline
                        changedFiles
                        additions
                        deletions
                        url
                        author {{
                          name
                          email
                          date
                          user {{
                            login
                          }}
                        }}
                      }}
                    }}
                  }}
                }}
              }}
            }}
          }}
        }}
        """
        data = make_call(query, token)
        history = data.get("repository", {}).get("defaultBranchRef", {}).get("target", {}).get("history", None)
        if history is None:
            print(f"⚠️  Skipping {repo_name}: no commit history found.")
            return commits

        for edge in history["edges"]:
            node = edge["node"]
            author_info = node["author"]
            commits.append({
                "repository": repo_name,
                "commit_sha": node["oid"],
                "authored_date": author_info["date"],
                "committed_date": node["committedDate"],
                "author": author_info["user"]["login"] if author_info["user"] else author_info["name"],
                "author_email": author_info["email"],
                "message": node["messageHeadline"],
                "changed_files": node["changedFiles"],
                "additions": node["additions"],
                "deletions": node["deletions"],
                "url": node["url"]
            })

        has_next_page = history["pageInfo"]["hasNextPage"]
        after = history["pageInfo"]["endCursor"]
        if has_next_page:
            time.sleep(0.1)  # Respect GitHub API rate limits

    return commits


def main():
    config = get_github_config('github.ini')
    token = config['PersonalAccessToken']
    org_name = config['Organization']

    all_commits = []
    repositories = get_repositories(org_name, token)
    total_repos = len(repositories)

    for idx, repo in enumerate(repositories, 1):
        print(f"[{idx}/{total_repos}] Processing repository: {repo}")
        try:
            commits = get_commits_for_repo(org_name, repo, token)
            all_commits.extend(commits)
        except Exception as e:
            print(f"Error processing {repo}: {e}")

    with open('commits.json', 'w', encoding='utf-8') as f:
        json.dump(all_commits, f, indent=2)
    print(f"✅ Saved {len(all_commits)} commits to commits.json")


if __name__ == "__main__":
    main()
