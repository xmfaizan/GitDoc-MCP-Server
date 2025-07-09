import requests
import base64
import os
import re
from datetime import datetime
from typing import List, Optional, Dict, Any
from github import Github
from ..config import settings
from ..models import FileInfo

class GitHubService:
    def __init__(self):
        self.github_token = settings.GITHUB_TOKEN
        self.github = Github(self.github_token, timeout=30) if self.github_token else None
        self.session = requests.Session()
        self.session.timeout = 30
        if self.github_token:
            self.session.headers.update({
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            })

    def _extract_repo_info(self, repo_url: str) -> tuple[str, str]:
        patterns = [
            r'github\.com/([^/]+)/([^/]+?)(?:\.git)?(?:/.*)?$',
            r'github\.com:([^/]+)/([^/]+?)(?:\.git)?$'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, repo_url)
            if match:
                return match.group(1), match.group(2)
        
        raise ValueError(f"Invalid GitHub repository URL: {repo_url}")

    async def get_repo_info(self, repo_url: str) -> Dict[str, Any]:
        try:
            owner, repo_name = self._extract_repo_info(repo_url)
            
            if self.github:
                repo = self.github.get_repo(f"{owner}/{repo_name}")
                
                # Safely get license information
                license_name = None
                try:
                    if hasattr(repo, 'license') and repo.license:
                        license_name = getattr(repo.license, 'name', None)
                except Exception:
                    license_name = None
                
                # Safely get topics
                topics = []
                try:
                    if hasattr(repo, 'get_topics'):
                        topics = repo.get_topics()
                except Exception:
                    topics = []
                
                return {
                    "name": getattr(repo, 'name', 'Unknown'),
                    "full_name": getattr(repo, 'full_name', 'Unknown'),
                    "description": getattr(repo, 'description', None) or "No description available",
                    "language": getattr(repo, 'language', None) or "Unknown",
                    "stars": getattr(repo, 'stargazers_count', 0),
                    "forks": getattr(repo, 'forks_count', 0),
                    "size": getattr(repo, 'size', 0),
                    "default_branch": getattr(repo, 'default_branch', 'main'),
                    "topics": topics,
                    "created_at": getattr(repo, 'created_at', datetime.now()).isoformat(),
                    "updated_at": getattr(repo, 'updated_at', datetime.now()).isoformat(),
                    "clone_url": getattr(repo, 'clone_url', ''),
                    "homepage": getattr(repo, 'homepage', None) or '',
                    "license": license_name
                }
            else:
                url = f"https://api.github.com/repos/{owner}/{repo_name}"
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                # Safely get license from API response
                license_name = None
                if data.get("license") and isinstance(data["license"], dict):
                    license_name = data["license"].get("name")
                
                return {
                    "name": data.get("name", "Unknown"),
                    "full_name": data.get("full_name", "Unknown"),
                    "description": data.get("description") or "No description available",
                    "language": data.get("language") or "Unknown",
                    "stars": data.get("stargazers_count", 0),
                    "forks": data.get("forks_count", 0),
                    "size": data.get("size", 0),
                    "default_branch": data.get("default_branch", "main"),
                    "topics": data.get("topics", []),
                    "created_at": data.get("created_at", ""),
                    "updated_at": data.get("updated_at", ""),
                    "clone_url": data.get("clone_url", ""),
                    "homepage": data.get("homepage") or "",
                    "license": license_name
                }
                
        except requests.exceptions.Timeout:
            raise Exception(f"Timeout while fetching repository info for {repo_url}")
        except Exception as e:
            raise Exception(f"Failed to fetch repository info: {str(e)}")

    async def get_repo_files(self, repo_url: str, branch: str = "main", 
                           include_patterns: Optional[List[str]] = None,
                           exclude_patterns: Optional[List[str]] = None) -> List[FileInfo]:
        try:
            owner, repo_name = self._extract_repo_info(repo_url)
            
            if exclude_patterns is None:
                exclude_patterns = [
                    "node_modules", ".git", "__pycache__", ".pytest_cache",
                    "venv", "env", ".env", "dist", "build", ".next",
                    ".vscode", ".idea", "coverage", ".nyc_output", "target",
                    "bin", "obj", ".gradle", "vendor"
                ]
            
            files = []
            processed_files = await self._get_tree_recursive(owner, repo_name, branch)
            
            # Limit file processing to prevent timeouts
            max_files = 50  # Process only first 50 files for demo
            processed_files = processed_files[:max_files]
            
            for file_data in processed_files:
                file_path = file_data["path"]
                
                if self._should_include_file(file_path, include_patterns, exclude_patterns):
                    file_extension = os.path.splitext(file_path)[1].lower()
                    language = settings.SUPPORTED_LANGUAGES.get(file_extension, "text")
                    
                    content = None
                    # Only get content for smaller files and common code files
                    if (self._is_text_file(file_extension) and 
                        file_data["size"] < 100000 and  # 100KB limit instead of 1MB
                        language != "text"):  # Skip generic text files
                        content = await self._get_file_content(
                            owner, repo_name, file_data["sha"], file_path
                        )
                    
                    files.append(FileInfo(
                        path=file_path,
                        name=os.path.basename(file_path),
                        size=file_data["size"],
                        language=language,
                        content=content,
                        sha=file_data["sha"]
                    ))
            
            return files
            
        except Exception as e:
            raise Exception(f"Failed to fetch repository files: {str(e)}")

    async def _get_tree_recursive(self, owner: str, repo_name: str, branch: str) -> List[Dict]:
        try:
            url = f"https://api.github.com/repos/{owner}/{repo_name}/git/trees/{branch}?recursive=1"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Filter and limit results
            blob_files = [item for item in data["tree"] if item["type"] == "blob"]
            
            # Sort by size (smaller files first) and limit
            blob_files.sort(key=lambda x: x.get("size", 0))
            return blob_files[:100]  # Limit to 100 files max
            
        except requests.exceptions.Timeout:
            print(f"Timeout getting file tree for {owner}/{repo_name}")
            return []
        except Exception as e:
            print(f"Error getting file tree: {str(e)}")
            return []

    async def _get_file_content(self, owner: str, repo_name: str, sha: str, file_path: str) -> Optional[str]:
        try:
            if self.github:
                repo = self.github.get_repo(f"{owner}/{repo_name}")
                file_content = repo.get_git_blob(sha)
                if file_content.encoding == "base64":
                    content = base64.b64decode(file_content.content).decode('utf-8', errors='ignore')
                    return content
            else:
                url = f"https://api.github.com/repos/{owner}/{repo_name}/git/blobs/{sha}"
                response = self.session.get(url, timeout=15)  # Shorter timeout for individual files
                response.raise_for_status()
                data = response.json()
                
                if data.get("encoding") == "base64":
                    content = base64.b64decode(data["content"]).decode('utf-8', errors='ignore')
                    return content
                    
        except requests.exceptions.Timeout:
            print(f"Timeout getting content for {file_path}, skipping...")
            return None
        except Exception as e:
            print(f"Failed to get content for {file_path}: {str(e)}")
            return None
        
        return None

    def _should_include_file(self, file_path: str, include_patterns: Optional[List[str]], 
                           exclude_patterns: Optional[List[str]]) -> bool:
        # Skip very deep nested files
        if file_path.count('/') > 5:
            return False
            
        # Skip files that are likely to be large or binary
        skip_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.svg', 
                          '.pdf', '.zip', '.tar', '.gz', '.rar', '.7z', '.exe', '.dll',
                          '.so', '.dylib', '.a', '.lib', '.jar', '.war', '.ear'}
        
        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension in skip_extensions:
            return False
            
        if exclude_patterns:
            for pattern in exclude_patterns:
                if pattern in file_path or file_path.startswith(pattern):
                    return False
        
        if include_patterns:
            return any(pattern in file_path for pattern in include_patterns)
        
        return file_extension in settings.SUPPORTED_LANGUAGES

    def _is_text_file(self, file_extension: str) -> bool:
        text_extensions = {
            '.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.cpp', '.c', '.cs',
            '.go', '.rs', '.php', '.rb', '.swift', '.kt', '.scala', '.md',
            '.txt', '.json', '.yaml', '.yml', '.toml', '.xml', '.html',
            '.css', '.scss', '.less', '.sql', '.sh', '.bat', '.ps1',
            '.dockerfile', '.gitignore', '.gitattributes', '.editorconfig'
        }
        return file_extension in text_extensions

    async def get_file_content_by_path(self, repo_url: str, file_path: str, branch: str = "main") -> Optional[str]:
        try:
            owner, repo_name = self._extract_repo_info(repo_url)
            
            if self.github:
                repo = self.github.get_repo(f"{owner}/{repo_name}")
                file_content = repo.get_contents(file_path, ref=branch)
                return file_content.decoded_content.decode('utf-8', errors='ignore')
            else:
                url = f"https://api.github.com/repos/{owner}/{repo_name}/contents/{file_path}?ref={branch}"
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                if data.get("encoding") == "base64":
                    content = base64.b64decode(data["content"]).decode('utf-8', errors='ignore')
                    return content
                    
        except requests.exceptions.Timeout:
            print(f"Timeout getting content for {file_path}")
            return None
        except Exception as e:
            print(f"Failed to get content for {file_path}: {str(e)}")
            return None
        
        return None