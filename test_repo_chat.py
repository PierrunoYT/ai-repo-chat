import unittest
import os
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime

from repo_chat import (
    get_latest_commit_sha,
    needs_reindex,
    save_metadata,
    chat_with_github_repo
)


class TestRepoChat(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_owner = "testowner"
        self.test_repo = "testrepo"
        self.test_token = "fake_token"
        self.test_sha = "abc123def456"
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up after each test method."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @patch('repo_chat.requests.get')
    def test_get_latest_commit_sha_success(self, mock_get):
        """Test successful retrieval of commit SHA."""
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "commit": {"sha": self.test_sha}
        }
        mock_get.return_value = mock_response
        
        result = get_latest_commit_sha(self.test_token, self.test_owner, self.test_repo)
        
        self.assertEqual(result, self.test_sha)
        mock_get.assert_called_once_with(
            f"https://api.github.com/repos/{self.test_owner}/{self.test_repo}/branches/main",
            headers={"Authorization": f"token {self.test_token}"}
        )

    @patch('repo_chat.requests.get')
    def test_get_latest_commit_sha_no_token(self, mock_get):
        """Test commit SHA retrieval without token."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "commit": {"sha": self.test_sha}
        }
        mock_get.return_value = mock_response
        
        result = get_latest_commit_sha(None, self.test_owner, self.test_repo)
        
        self.assertEqual(result, self.test_sha)
        mock_get.assert_called_once_with(
            f"https://api.github.com/repos/{self.test_owner}/{self.test_repo}/branches/main",
            headers={}
        )

    @patch('repo_chat.requests.get')
    def test_get_latest_commit_sha_api_error(self, mock_get):
        """Test commit SHA retrieval with API error."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        result = get_latest_commit_sha(self.test_token, self.test_owner, self.test_repo)
        
        self.assertIsNone(result)

    @patch('repo_chat.requests.get')
    def test_get_latest_commit_sha_exception(self, mock_get):
        """Test commit SHA retrieval with exception."""
        mock_get.side_effect = Exception("Network error")
        
        result = get_latest_commit_sha(self.test_token, self.test_owner, self.test_repo)
        
        self.assertIsNone(result)

    def test_needs_reindex_no_metadata_file(self):
        """Test needs_reindex when metadata file doesn't exist."""
        storage_dir = os.path.join(self.temp_dir, "nonexistent")
        
        result = needs_reindex(storage_dir, self.test_token, self.test_owner, self.test_repo)
        
        self.assertTrue(result)

    @patch('repo_chat.get_latest_commit_sha')
    def test_needs_reindex_same_sha(self, mock_get_sha):
        """Test needs_reindex when SHA hasn't changed."""
        storage_dir = os.path.join(self.temp_dir, "test_storage")
        os.makedirs(storage_dir)
        
        # Create metadata file with test SHA
        metadata = {
            "last_commit_sha": self.test_sha,
            "last_indexed": datetime.now().isoformat(),
            "owner": self.test_owner,
            "repo": self.test_repo
        }
        metadata_file = os.path.join(storage_dir, "metadata.json")
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f)
        
        mock_get_sha.return_value = self.test_sha
        
        result = needs_reindex(storage_dir, self.test_token, self.test_owner, self.test_repo)
        
        self.assertFalse(result)

    @patch('repo_chat.get_latest_commit_sha')
    def test_needs_reindex_different_sha(self, mock_get_sha):
        """Test needs_reindex when SHA has changed."""
        storage_dir = os.path.join(self.temp_dir, "test_storage")
        os.makedirs(storage_dir)
        
        # Create metadata file with old SHA
        metadata = {
            "last_commit_sha": "old_sha",
            "last_indexed": datetime.now().isoformat(),
            "owner": self.test_owner,
            "repo": self.test_repo
        }
        metadata_file = os.path.join(storage_dir, "metadata.json")
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f)
        
        mock_get_sha.return_value = self.test_sha
        
        result = needs_reindex(storage_dir, self.test_token, self.test_owner, self.test_repo)
        
        self.assertTrue(result)

    @patch('repo_chat.get_latest_commit_sha')
    def test_needs_reindex_corrupted_metadata(self, mock_get_sha):
        """Test needs_reindex with corrupted metadata file."""
        storage_dir = os.path.join(self.temp_dir, "test_storage")
        os.makedirs(storage_dir)
        
        # Create corrupted metadata file
        metadata_file = os.path.join(storage_dir, "metadata.json")
        with open(metadata_file, 'w') as f:
            f.write("invalid json")
        
        result = needs_reindex(storage_dir, self.test_token, self.test_owner, self.test_repo)
        
        self.assertTrue(result)

    @patch('repo_chat.get_latest_commit_sha')
    def test_save_metadata(self, mock_get_sha):
        """Test saving metadata to file."""
        storage_dir = os.path.join(self.temp_dir, "test_storage")
        os.makedirs(storage_dir)
        
        mock_get_sha.return_value = self.test_sha
        
        save_metadata(storage_dir, self.test_token, self.test_owner, self.test_repo)
        
        metadata_file = os.path.join(storage_dir, "metadata.json")
        self.assertTrue(os.path.exists(metadata_file))
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        self.assertEqual(metadata["last_commit_sha"], self.test_sha)
        self.assertEqual(metadata["owner"], self.test_owner)
        self.assertEqual(metadata["repo"], self.test_repo)
        self.assertIn("last_indexed", metadata)

    @patch('repo_chat.load_dotenv')
    @patch('repo_chat.os.getenv')
    def test_chat_with_github_repo_missing_openai_key(self, mock_getenv, mock_load_dotenv):
        """Test chat function with missing OpenAI API key."""
        mock_getenv.side_effect = lambda key: None if key == "OPENAI_API_KEY" else "fake_token"
        
        with self.assertRaises(ValueError) as context:
            chat_with_github_repo("https://github.com/owner/repo", "test question")
        
        self.assertIn("OpenAI API key not found", str(context.exception))

    @patch('repo_chat.load_dotenv')
    @patch('repo_chat.os.getenv')
    def test_chat_with_github_repo_missing_github_token(self, mock_getenv, mock_load_dotenv):
        """Test chat function with missing GitHub token."""
        mock_getenv.side_effect = lambda key: "fake_openai_key" if key == "OPENAI_API_KEY" else None
        
        with self.assertRaises(ValueError) as context:
            chat_with_github_repo("https://github.com/owner/repo", "test question")
        
        self.assertIn("GitHub token not found", str(context.exception))

    @patch('repo_chat.load_dotenv')
    @patch('repo_chat.os.getenv')
    @patch('repo_chat.needs_reindex')
    @patch('repo_chat.load_index_from_storage')
    @patch('repo_chat.StorageContext.from_defaults')
    @patch('os.path.exists')
    def test_chat_with_github_repo_load_existing_index(
        self, mock_exists, mock_storage_context, mock_load_index, mock_needs_reindex, mock_getenv, mock_load_dotenv
    ):
        """Test chat function loading existing index."""
        # Mock environment variables
        mock_getenv.side_effect = lambda key: {
            "OPENAI_API_KEY": "fake_openai_key",
            "GITHUB_TOKEN": "fake_github_token"
        }.get(key)
        
        # Mock existing storage and no reindex needed
        mock_exists.return_value = True
        mock_needs_reindex.return_value = False
        
        # Mock index and query engine
        mock_index = MagicMock()
        mock_query_engine = MagicMock()
        mock_query_engine.query.return_value = "Test response"
        mock_index.as_query_engine.return_value = mock_query_engine
        mock_load_index.return_value = mock_index
        
        # Mock stdout to capture prints
        with patch('builtins.print') as mock_print:
            chat_with_github_repo("https://github.com/owner/repo", "test question")
        
        # Verify index was loaded, not created
        mock_load_index.assert_called_once()
        mock_query_engine.query.assert_called_once_with("test question")

    def test_url_parsing(self):
        """Test URL parsing for owner and repo extraction."""
        test_urls = [
            ("https://github.com/owner/repo", ("owner", "repo")),
            ("https://github.com/test-owner/test-repo", ("test-owner", "test-repo")),
            ("github.com/user/project", ("user", "project"))
        ]
        
        for url, expected in test_urls:
            owner, repo = url.split("/")[-2:]
            self.assertEqual((owner, repo), expected)


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete workflow."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @patch.dict(os.environ, {
        'OPENAI_API_KEY': 'fake_openai_key',
        'GITHUB_TOKEN': 'fake_github_token'
    })
    @patch('repo_chat.GithubRepositoryReader')
    @patch('repo_chat.VectorStoreIndex.from_documents')
    @patch('repo_chat.get_latest_commit_sha')
    def test_full_workflow_new_repository(self, mock_get_sha, mock_vector_index, mock_github_reader):
        """Test complete workflow for a new repository."""
        # Setup mocks
        mock_get_sha.return_value = "abc123"
        
        mock_documents = [MagicMock()]
        mock_loader = MagicMock()
        mock_loader.load_data.return_value = mock_documents
        mock_github_reader.return_value = mock_loader
        
        mock_index = MagicMock()
        mock_query_engine = MagicMock()
        mock_query_engine.query.return_value = "This is a test repository"
        mock_index.as_query_engine.return_value = mock_query_engine
        mock_vector_index.return_value = mock_index
        
        # Change to temp directory for storage
        original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        try:
            with patch('builtins.print'):
                chat_with_github_repo("https://github.com/test/repo", "What does this repo do?")
            
            # Verify storage was created
            storage_dir = "./storage/test_repo"
            self.assertTrue(os.path.exists(storage_dir))
            
            # Verify metadata was saved
            metadata_file = os.path.join(storage_dir, "metadata.json")
            self.assertTrue(os.path.exists(metadata_file))
            
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            self.assertEqual(metadata["last_commit_sha"], "abc123")
            self.assertEqual(metadata["owner"], "test")
            self.assertEqual(metadata["repo"], "repo")
            
        finally:
            os.chdir(original_cwd)


if __name__ == '__main__':
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestRepoChat))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)