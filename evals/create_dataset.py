import os
import subprocess
from typing import List, Optional
from langsmith import Client
from dotenv import load_dotenv

# Load environment variables (for LANGCHAIN_API_KEY)
# Point to the .env file in the project root
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path=env_path)

# Ensure LANGCHAIN_API_KEY is set from LANGSMITH_API_KEY if needed
if not os.getenv("LANGCHAIN_API_KEY") and os.getenv("LANGSMITH_API_KEY"):
    os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGSMITH_API_KEY")
    print(f"ℹ️  Mapped LANGSMITH_API_KEY to LANGCHAIN_API_KEY")

DATASET_NAME = "BlueStar Evaluation Dataset"
COMMIT_LIMIT = 10

# Configuration: Local Path -> Repo Identifier
# We use local git commands to fetch commits directly, avoiding GitHub API rate limits for this step.
REPO_MAPPING = {
    # ".": "domini04/bluestar",  # Skipping BlueStar for now
    "../reverse-turing": "domini04/AI-Imposter"  # Only fetching AI-Imposter
}


def get_local_commits(repo_path: str, limit: int = 10) -> List[str]:
    try:
        # Expand relative paths to absolute
        abs_path = os.path.abspath(repo_path)
        
        if not os.path.exists(abs_path):
            print(f"⚠️  Path not found: {abs_path} (Skipping)")
            return []

        # Run git log
        result = subprocess.run(
            ["git", "-C", abs_path, "log", "-n", str(limit), "--pretty=format:%H"],
            capture_output=True,
            text=True,
            check=True
        )
        commits = result.stdout.strip().split('\n')
        # Filter empty strings if any
        return [c.strip() for c in commits if c.strip()]
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running git log in {repo_path}: {e}")
        return []
    except Exception as e:
        print(f"❌ Unexpected error processing {repo_path}: {e}")
        return []

def main():
    print(f"🚀 Initializing LangSmith Client...")
    try:
        client = Client()
    except Exception as e:
        print(f"❌ Failed to initialize LangSmith client. Please ensure LANGCHAIN_API_KEY is set.")
        print(f"   Error: {e}")
        return

    # 1. Create (or get) the dataset
    if client.has_dataset(dataset_name=DATASET_NAME):
        dataset = client.read_dataset(dataset_name=DATASET_NAME)
        print(f"✅ Found existing dataset: '{dataset.name}' (ID: {dataset.id})")
    else:
        dataset = client.create_dataset(
            dataset_name=DATASET_NAME,
            description="Real-world commits from BlueStar and AI-Imposter for manual review & binary evaluation."
        )
        print(f"✅ Created new dataset: '{dataset.name}' (ID: {dataset.id})")

    # 2. Fetch and Upload
    total_added = 0
    
    for local_path, repo_id in REPO_MAPPING.items():
        print(f"\n📂 Processing {repo_id} (from local path: {local_path})...")
        commits = get_local_commits(local_path, limit=COMMIT_LIMIT)
        
        if not commits:
            print(f"   No commits found or path inaccessible.")
            continue
            
        print(f"   Found {len(commits)} commits. Uploading to LangSmith...")
        
        for sha in commits:
            try:
                # Check if example already exists to avoid duplicates (optional but good practice)
                # For simplicity in this script, we'll just append. LangSmith handles unique example IDs,
                # but inputs can be duplicated. We'll rely on the review process to handle dupes if they occur,
                # or the user can delete the dataset to regenerate.
                
                client.create_example(
                    inputs={
                        "repo_identifier": repo_id,
                        "commit_sha": sha
                    },
                    dataset_id=dataset.id,
                    metadata={
                        "source": "local_git_extraction", 
                        "repo": repo_id,
                        "original_path": local_path,
                        "ingestion_strategy": "manual_script"
                    }
                )
                print(f"   - Added: {sha[:7]}")
                total_added += 1
            except Exception as e:
                print(f"   ❌ Failed to add {sha[:7]}: {e}")

    print(f"\n✨ Done! Added {total_added} examples to dataset '{DATASET_NAME}'.")
    print(f"👉 View dataset at: https://smith.langchain.com/datasets/{dataset.id}")

if __name__ == "__main__":
    main()

