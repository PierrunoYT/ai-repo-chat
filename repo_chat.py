import os
import argparse
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex
from llama_index.readers.github import GithubRepositoryReader

def chat_with_github_repo(repo_url: str, question: str):
    """
    Clones a GitHub repository, indexes its content, and answers a question
    about it using an AI model.

    Args:
        repo_url (str): The URL of the GitHub repository.
        question (str): The question to ask about the repository.
    """
    # Load environment variables from .env file
    load_dotenv()

    # Check if the OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OpenAI API key not found. Please set it in your .env file.")

    try:
        # Extract owner and repo name from the URL
        owner, repo = repo_url.split("/")[-2:]

        # Instantiate the reader with the repository details
        loader = GithubRepositoryReader(
            github_client=None,  # Uses default GitHub client
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

    # Parse arguments
    args = parser.parse_args()

    # Run the chat function
    chat_with_github_repo(args.repo_url, args.question)