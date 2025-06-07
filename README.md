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
   
4. Edit `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

## Usage

```bash
python repo_chat.py <repo_url> "<question>"
```

### Examples

```bash
# Ask about the main functionality
python repo_chat.py "https://github.com/owner/repo" "What does this repository do?"

# Ask about specific functions
python repo_chat.py "https://github.com/owner/repo" "How does the authentication work?"

# Ask about architecture
python repo_chat.py "https://github.com/owner/repo" "What is the overall architecture of this project?"
```

## How it Works

1. **Repository Loading**: The tool uses LlamaIndex's `GithubRepositoryReader` to clone and load the repository content
2. **Content Indexing**: Creates a vector index of all repository files for efficient searching
3. **AI Query**: Uses OpenAI's models to answer questions based on the indexed content
4. **Response**: Returns AI-generated answers based on the repository's actual code and documentation

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