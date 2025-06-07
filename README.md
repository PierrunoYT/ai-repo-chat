# RepoChat

Chat with any GitHub repository using AI. This tool clones a GitHub repository, indexes its content, and allows you to ask questions about the codebase using OpenAI's language models.

## Features

- Load and index any public GitHub repository
- Ask natural language questions about the codebase
- Get AI-powered responses based on the repository content
- Simple command-line interface

## Prerequisites

- Python 3.7+
- OpenAI API key
- GitHub token (for repository access)

## Installation

1. Clone this repository:
   ```bash
   git clone <your-repo-url>
   cd RepoChat
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your environment variables:
   ```bash
   cp .env.example .env
   ```
   
4. Edit `.env` and add your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   GITHUB_TOKEN=your_github_token_here
   ```

   **Getting a GitHub Token:**
   - Go to [GitHub Settings > Tokens](https://github.com/settings/tokens)
   - Click "Generate new token (classic)"
   - For public repositories, only select the `public_repo` scope
   - Copy the generated token and add it to your `.env` file

## Usage

### Interactive Mode (Recommended)
Simply run without arguments to enter interactive mode:
```bash
python repo_chat.py
# or
python repo_chat.py --interactive
# or
python repo_chat.py -i
```

### Command Line Mode
```bash
python repo_chat.py <repo_url> "<question>"
```

### Examples

```bash
# Interactive mode - prompts for input
python repo_chat.py

# Command line mode - direct execution
python repo_chat.py "https://github.com/owner/repo" "What does this repository do?"

# Ask about specific functions
python repo_chat.py "https://github.com/owner/repo" "How does the authentication work?"

# Force reindexing with command line
python repo_chat.py "https://github.com/owner/repo" "What changed?" --force-reindex
```

### Interactive Mode Features
- 🔍 **URL Validation**: Automatically validates GitHub repository URLs
- ✨ **Smart Input**: Auto-adds `https://` if missing from URLs
- 🔄 **Reindex Option**: Prompts whether to force reindexing
- ❌ **Error Handling**: Clear error messages and retry prompts
- 🎨 **User-Friendly**: Emoji-enhanced interface for better UX

## How it Works

1. **Repository Loading**: The tool uses LlamaIndex's `GithubRepositoryReader` to clone and load the repository content
2. **Content Indexing**: Creates a vector index of all repository files for efficient searching
3. **Index Persistence**: Saves indexes to disk and automatically detects repository updates
4. **AI Query**: Uses OpenAI's models to answer questions based on the indexed content
5. **Response**: Returns AI-generated answers based on the repository's actual code and documentation

## Testing

Run the test suite to verify functionality:

```bash
# Install test dependencies
pip install pytest pytest-mock coverage

# Run all tests
python -m pytest test_repo_chat.py -v

# Run tests with coverage
python -m pytest test_repo_chat.py --cov=repo_chat --cov-report=html

# Run specific test
python -m pytest test_repo_chat.py::TestRepoChat::test_get_latest_commit_sha_success -v
```

The test suite includes:
- Unit tests for all helper functions
- Mocked GitHub API calls
- Metadata persistence testing
- Integration tests for the complete workflow
- Error handling and edge case testing

## Requirements

- `llama-index` - For repository loading and vector indexing
- `python-dotenv` - For environment variable management
- `openai` - For AI model access

## Limitations

- Only works with public GitHub repositories
- Requires an OpenAI API key (costs may apply)
- Performance depends on repository size
- Only indexes the main branch by default

## License

MIT License