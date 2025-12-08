# LangSmith Evaluation Dataset Creation

To implement **Step 1: Initial Data Analysis**, we need to create a dataset in LangSmith containing real input examples (commits) that we can run through our agent to generate traces for manual review.

## Dataset Strategy

We will create a script `create_dataset.py` that:
1.  **Source Data**: Fetches recent commits from:
    *   The **BlueStar** repository itself (self-reflection).
    *   Your **Personal Project** (external test case).
2.  **Format**: Converts these commits into the Key-Value format expected by our Agent's input schema:
    *   Input: `{"repo_identifier": "owner/repo", "commit_sha": "..."}`
    *   Reference (Optional): Can be empty for now, as we are doing *open coding* (exploratory analysis) first.
3.  **Upload**: Uses the `langsmith` client to create a Dataset named `BlueStar Evaluation Dataset`.

## Script Design (`evals/create_dataset.py`)

```python
import os
from langsmith import Client
from src.bluestar.tools.github_client import GitHubClient

# Configuration
DATASET_NAME = "BlueStar Evaluation Dataset"
TARGET_REPOS = [
    "yub/bluestar",       # This project
    "yub/your-other-repo" # Placeholder - update this
]
COMMIT_LIMIT = 10  # Number of commits per repo to fetch

def create_evaluation_dataset():
    client = Client()
    gh_client = GitHubClient()
    
    # 1. Create (or get) the dataset
    if client.has_dataset(dataset_name=DATASET_NAME):
        dataset = client.read_dataset(dataset_name=DATASET_NAME)
        print(f"Using existing dataset: {dataset.name}")
    else:
        dataset = client.create_dataset(
            dataset_name=DATASET_NAME,
            description="Real commits from BlueStar and personal projects for manual review."
        )
        print(f"Created new dataset: {dataset.name}")

    # 2. Fetch commits and add examples
    for repo_name in TARGET_REPOS:
        print(f"Fetching commits from {repo_name}...")
        try:
            # We need a method to list commits - currently GitHubClient fetches single commit
            # We might need to use raw GH API or add list_commits to GitHubClient
            # For now, assuming we can get a list of SHAs
            commits = gh_client.list_recent_commits(repo_name, limit=COMMIT_LIMIT)
            
            for commit in commits:
                client.create_example(
                    inputs={
                        "repo_identifier": repo_name,
                        "commit_sha": commit['sha']
                    },
                    dataset_id=dataset.id,
                    metadata={"source": "real_world", "repo": repo_name}
                )
                print(f"  Added commit {commit['sha'][:7]}")
                
        except Exception as e:
            print(f"Error fetching from {repo_name}: {e}")

    print("Dataset creation complete!")

if __name__ == "__main__":
    create_evaluation_dataset()
```

## Prerequisites Check

1.  **GitHubClient Capability**: Does our `GitHubClient` currently support *listing* commits?
    *   *Action*: I need to check `src/bluestar/tools/github_client.py`. If not, I will need to add a `list_commits` method or use a direct API call in the script.
2.  **Personal Project Name**: I will need the actual `owner/repo` name for your personal project to replace the placeholder.

## Next Actions

1.  Check `GitHubClient` for commit listing capability.
2.  Create the `evals/create_dataset.py` script.
3.  Ask you for the second repository name.

