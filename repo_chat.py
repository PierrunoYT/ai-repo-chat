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

def validate_github_url(url: str) -> bool:
    """Validate that the URL is a valid GitHub repository URL."""
    import re
    pattern = r'^https?://github\.com/[^/]+/[^/]+/?$'
    return bool(re.match(pattern, url.strip()))

def interactive_mode():
    """Run the application in interactive mode, prompting for input."""
    print("🤖 Welcome to RepoChat - Interactive Mode")
    print("=" * 50)
    
    # Get repository URL
    while True:
        repo_url = input("\n📁 Enter GitHub repository URL: ").strip()
        if not repo_url:
            print("❌ URL cannot be empty. Please try again.")
            continue
        
        # Add https:// if missing
        if not repo_url.startswith(('http://', 'https://')):
            repo_url = 'https://' + repo_url
        
        if validate_github_url(repo_url):
            break
        else:
            print("❌ Invalid GitHub repository URL. Please use format: https://github.com/owner/repo")
    
    # Get question
    while True:
        question = input("\n❓ What would you like to know about this repository? ").strip()
        if question:
            break
        print("❌ Question cannot be empty. Please try again.")
    
    # Ask about force reindex
    force_reindex = False
    reindex_input = input("\n🔄 Force reindex? (y/N): ").strip().lower()
    if reindex_input in ['y', 'yes']:
        force_reindex = True
    
    print(f"\n🚀 Processing repository: {repo_url}")
    print(f"❓ Question: {question}")
    if force_reindex:
        print("🔄 Force reindexing enabled")
    print("-" * 50)
    
    # Run the chat function
    try:
        chat_with_github_repo(repo_url, question, force_reindex)
    except KeyboardInterrupt:
        print("\n\n👋 Thanks for using RepoChat!")
    except Exception as e:
        print(f"\n❌ Error: {e}")

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

        # Create a query engine from the index with enhanced configuration
        query_engine = index.as_query_engine(
            response_mode="tree_summarize",  # Better for comprehensive responses
            similarity_top_k=10,  # Retrieve more relevant chunks
            streaming=False,
            verbose=True
        )

        # Enhanced prompt for better responses
        enhanced_question = f"""Based on the repository code and documentation, please provide a detailed answer to this question: {question}

Please include:
- Specific details found in the code
- Configuration options or parameters
- File names and locations where relevant information is found
- Any version numbers, model names, or technical specifications mentioned

Question: {question}"""

        # Query the engine with the enhanced question
        print("Asking the AI your question...")
        response = query_engine.query(enhanced_question)

        # Print the response
        print("\nAI Response:")
        print(response)

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Chat with a GitHub repository using AI.",
        epilog="Examples:\n"
               "  %(prog)s https://github.com/owner/repo \"What does this do?\"\n"
               "  %(prog)s --interactive\n"
               "  %(prog)s -i",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Add interactive mode argument
    parser.add_argument("-i", "--interactive", action="store_true", 
                       help="Run in interactive mode (prompts for input)")
    
    # Make positional arguments optional when in interactive mode
    parser.add_argument("repo_url", nargs="?", 
                       help="The URL of the GitHub repository (e.g., 'https://github.com/owner/repo')")
    parser.add_argument("question", nargs="?", 
                       help="The question you want to ask about the repository")
    parser.add_argument("--force-reindex", action="store_true", 
                       help="Force reindexing even if index exists and is up to date")

    # Parse arguments
    args = parser.parse_args()

    # Check if interactive mode or if no arguments provided
    if args.interactive or (not args.repo_url and not args.question):
        interactive_mode()
    else:
        # Validate that both repo_url and question are provided in non-interactive mode
        if not args.repo_url or not args.question:
            parser.error("Both repo_url and question are required when not using interactive mode")
        
        # Run the chat function
        chat_with_github_repo(args.repo_url, args.question, args.force_reindex)