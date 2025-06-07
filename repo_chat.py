import os
import argparse
import json
from datetime import datetime
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage
from llama_index.readers.github import GithubRepositoryReader, GithubClient

def get_latest_commit_sha(github_token: str, owner: str, repo: str) -> str:
    """Get the latest commit SHA for the repository."""
    import requests
    url = f"https://api.github.com/repos/{owner}/{repo}/branches/main"
    headers = {"Authorization": f"token {github_token}"} if github_token else {}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()["commit"]["sha"]
        return None
    except Exception:
        return None

def needs_reindex(storage_dir: str, github_token: str, owner: str, repo: str) -> bool:
    """Check if repository needs reindexing based on latest commit."""
    metadata_file = os.path.join(storage_dir, "metadata.json")
    
    if not os.path.exists(metadata_file):
        return True
    
    try:
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        stored_sha = metadata.get("last_commit_sha")
        current_sha = get_latest_commit_sha(github_token, owner, repo)
        
        return stored_sha != current_sha
    except Exception:
        return True

def save_metadata(storage_dir: str, github_token: str, owner: str, repo: str):
    """Save repository metadata including latest commit SHA."""
    metadata = {
        "last_commit_sha": get_latest_commit_sha(github_token, owner, repo),
        "last_indexed": datetime.now().isoformat(),
        "owner": owner,
        "repo": repo
    }
    
    metadata_file = os.path.join(storage_dir, "metadata.json")
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)

def chat_with_github_repo(repo_url: str, question: str, force_reindex: bool = False):
    """
    Clones a GitHub repository, indexes its content, and answers a question
    about it using an AI model.

    Args:
        repo_url (str): The URL of the GitHub repository.
        question (str): The question to ask about the repository.
        force_reindex (bool): Force reindexing even if index exists.
    """
    # Load environment variables from .env file
    load_dotenv()

    # Check if the OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OpenAI API key not found. Please set it in your .env file.")

    # Get GitHub token (optional for public repos, but required by LlamaIndex)
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        raise ValueError(
            "GitHub token not found. Please set GITHUB_TOKEN in your .env file.\n"
            "You can create a token at: https://github.com/settings/tokens\n"
            "For public repos, you only need 'public_repo' scope."
        )

    try:
        # Extract owner and repo name from the URL
        owner, repo = repo_url.split("/")[-2:]

        # Initialize GitHub client with token
        github_client = GithubClient(github_token=github_token, verbose=False)

        # Create storage directory for this repository
        storage_dir = f"./storage/{owner}_{repo}"
        
        # Check if index needs to be created or updated
        should_reindex = force_reindex or not os.path.exists(storage_dir) or needs_reindex(storage_dir, github_token, owner, repo)
        
        if not should_reindex:
            print(f"Loading existing index for {owner}/{repo}...")
            # Load existing index
            storage_context = StorageContext.from_defaults(persist_dir=storage_dir)
            index = load_index_from_storage(storage_context)
            print("Index loaded from storage.")
        else:
            if os.path.exists(storage_dir):
                print(f"Repository {owner}/{repo} has been updated. Reindexing...")
            else:
                print(f"Creating new index for {owner}/{repo}...")

            # Instantiate the reader with the repository details
            loader = GithubRepositoryReader(
                github_client=github_client,
                owner=owner,
                repo=repo,
                use_parser=False,
                verbose=False,
            )

            # Load the repository data
            print(f"Loading repository: {repo_url}...")
            documents = loader.load_data(branch="main")
            print("Repository loaded successfully.")

            # Create an index from the loaded documents
            print("Creating index...")
            index = VectorStoreIndex.from_documents(documents)
            print("Index created successfully.")
            
            # Persist index to disk
            print("Saving index to storage...")
            os.makedirs(storage_dir, exist_ok=True)
            index.storage_context.persist(persist_dir=storage_dir)
            
            # Save metadata
            save_metadata(storage_dir, github_token, owner, repo)
            print(f"Index saved to {storage_dir}")

        # Create a query engine from the index
        query_engine = index.as_query_engine()

        # Query the engine with the user's question
        print("Asking the AI your question...")
        response = query_engine.query(question)

        # Print the response
        print("\nAI Response:")
        print(response)

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Chat with a GitHub repository using AI.")
    parser.add_argument("repo_url", help="The URL of the GitHub repository (e.g., 'https://github.com/owner/repo').")
    parser.add_argument("question", help="The question you want to ask about the repository.")
    parser.add_argument("--force-reindex", action="store_true", help="Force reindexing even if index exists and is up to date.")

    # Parse arguments
    args = parser.parse_args()

    # Run the chat function
    chat_with_github_repo(args.repo_url, args.question, args.force_reindex)