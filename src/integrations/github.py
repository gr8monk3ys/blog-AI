"""
GitHub integration functionality.
"""
import os
import base64
from typing import Dict, Any, List, Optional

import requests

from ..types.integrations import (
    GitHubCredentials,
    GitHubRepository,
    GitHubFileOptions,
    IntegrationResult
)


class GitHubIntegrationError(Exception):
    """Exception raised for errors in the GitHub integration process."""
    pass


def upload_file(
    credentials: GitHubCredentials,
    repository: GitHubRepository,
    options: GitHubFileOptions
) -> IntegrationResult:
    """
    Upload a file to GitHub.
    
    Args:
        credentials: The GitHub credentials.
        repository: The GitHub repository.
        options: The file options.
        
    Returns:
        The integration result.
        
    Raises:
        GitHubIntegrationError: If an error occurs during upload.
    """
    try:
        # Create authentication header
        headers = {
            "Authorization": f"token {credentials.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Check if file exists
        file_exists = False
        file_sha = None
        
        try:
            response = requests.get(
                f"https://api.github.com/repos/{repository.owner}/{repository.name}/contents/{options.path}",
                headers=headers,
                params={"ref": options.branch}
            )
            
            if response.status_code == 200:
                file_exists = True
                file_sha = response.json()["sha"]
        except Exception:
            pass
        
        # Create file data
        file_data = {
            "message": options.message,
            "content": base64.b64encode(options.content.encode()).decode(),
            "branch": options.branch
        }
        
        if file_exists:
            file_data["sha"] = file_sha
        
        # Upload file
        response = requests.put(
            f"https://api.github.com/repos/{repository.owner}/{repository.name}/contents/{options.path}",
            headers=headers,
            json=file_data
        )
        
        # Check response
        if response.status_code in (200, 201):
            file_data = response.json()
            return IntegrationResult(
                success=True,
                message=f"File uploaded successfully",
                data={"file_url": file_data["content"]["html_url"]}
            )
        else:
            return IntegrationResult(
                success=False,
                message=f"Failed to upload file: {response.text}",
                data=None
            )
    except Exception as e:
        raise GitHubIntegrationError(f"Error uploading file: {str(e)}")


def create_repository(
    credentials: GitHubCredentials,
    name: str,
    description: Optional[str] = None,
    private: bool = False
) -> GitHubRepository:
    """
    Create a repository in GitHub.
    
    Args:
        credentials: The GitHub credentials.
        name: The name of the repository.
        description: The description of the repository.
        private: Whether the repository is private.
        
    Returns:
        The created GitHub repository.
        
    Raises:
        GitHubIntegrationError: If an error occurs during creation.
    """
    try:
        # Create authentication header
        headers = {
            "Authorization": f"token {credentials.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Create repository data
        repo_data = {
            "name": name,
            "private": private
        }
        
        if description:
            repo_data["description"] = description
        
        # Create repository
        response = requests.post(
            "https://api.github.com/user/repos",
            headers=headers,
            json=repo_data
        )
        
        # Check response
        if response.status_code in (200, 201):
            repo_data = response.json()
            return GitHubRepository(
                owner=repo_data["owner"]["login"],
                name=repo_data["name"]
            )
        else:
            raise GitHubIntegrationError(f"Failed to create repository: {response.text}")
    except Exception as e:
        raise GitHubIntegrationError(f"Error creating repository: {str(e)}")


def get_repositories(
    credentials: GitHubCredentials
) -> List[GitHubRepository]:
    """
    Get repositories from GitHub.
    
    Args:
        credentials: The GitHub credentials.
        
    Returns:
        A list of GitHub repositories.
        
    Raises:
        GitHubIntegrationError: If an error occurs during retrieval.
    """
    try:
        # Create authentication header
        headers = {
            "Authorization": f"token {credentials.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Get repositories
        response = requests.get(
            "https://api.github.com/user/repos",
            headers=headers
        )
        
        # Check response
        if response.status_code == 200:
            repos_data = response.json()
            repos = []
            
            for repo_data in repos_data:
                repos.append(
                    GitHubRepository(
                        owner=repo_data["owner"]["login"],
                        name=repo_data["name"]
                    )
                )
            
            return repos
        else:
            raise GitHubIntegrationError(f"Failed to get repositories: {response.text}")
    except Exception as e:
        raise GitHubIntegrationError(f"Error getting repositories: {str(e)}")


def get_repository(
    credentials: GitHubCredentials,
    owner: str,
    name: str
) -> GitHubRepository:
    """
    Get a repository from GitHub.
    
    Args:
        credentials: The GitHub credentials.
        owner: The owner of the repository.
        name: The name of the repository.
        
    Returns:
        The GitHub repository.
        
    Raises:
        GitHubIntegrationError: If an error occurs during retrieval.
    """
    try:
        # Create authentication header
        headers = {
            "Authorization": f"token {credentials.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Get repository
        response = requests.get(
            f"https://api.github.com/repos/{owner}/{name}",
            headers=headers
        )
        
        # Check response
        if response.status_code == 200:
            repo_data = response.json()
            return GitHubRepository(
                owner=repo_data["owner"]["login"],
                name=repo_data["name"]
            )
        else:
            raise GitHubIntegrationError(f"Failed to get repository: {response.text}")
    except Exception as e:
        raise GitHubIntegrationError(f"Error getting repository: {str(e)}")


def create_branch(
    credentials: GitHubCredentials,
    repository: GitHubRepository,
    branch_name: str,
    base_branch: str = "main"
) -> IntegrationResult:
    """
    Create a branch in GitHub.
    
    Args:
        credentials: The GitHub credentials.
        repository: The GitHub repository.
        branch_name: The name of the branch.
        base_branch: The base branch.
        
    Returns:
        The integration result.
        
    Raises:
        GitHubIntegrationError: If an error occurs during creation.
    """
    try:
        # Create authentication header
        headers = {
            "Authorization": f"token {credentials.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Get base branch reference
        response = requests.get(
            f"https://api.github.com/repos/{repository.owner}/{repository.name}/git/refs/heads/{base_branch}",
            headers=headers
        )
        
        # Check response
        if response.status_code != 200:
            return IntegrationResult(
                success=False,
                message=f"Failed to get base branch reference: {response.text}",
                data=None
            )
        
        base_sha = response.json()["object"]["sha"]
        
        # Create branch
        branch_data = {
            "ref": f"refs/heads/{branch_name}",
            "sha": base_sha
        }
        
        response = requests.post(
            f"https://api.github.com/repos/{repository.owner}/{repository.name}/git/refs",
            headers=headers,
            json=branch_data
        )
        
        # Check response
        if response.status_code in (200, 201):
            return IntegrationResult(
                success=True,
                message=f"Branch created successfully",
                data={"branch_name": branch_name}
            )
        else:
            return IntegrationResult(
                success=False,
                message=f"Failed to create branch: {response.text}",
                data=None
            )
    except Exception as e:
        raise GitHubIntegrationError(f"Error creating branch: {str(e)}")


def create_pull_request(
    credentials: GitHubCredentials,
    repository: GitHubRepository,
    title: str,
    head: str,
    base: str = "main",
    body: Optional[str] = None
) -> IntegrationResult:
    """
    Create a pull request in GitHub.
    
    Args:
        credentials: The GitHub credentials.
        repository: The GitHub repository.
        title: The title of the pull request.
        head: The head branch.
        base: The base branch.
        body: The body of the pull request.
        
    Returns:
        The integration result.
        
    Raises:
        GitHubIntegrationError: If an error occurs during creation.
    """
    try:
        # Create authentication header
        headers = {
            "Authorization": f"token {credentials.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Create pull request data
        pr_data = {
            "title": title,
            "head": head,
            "base": base
        }
        
        if body:
            pr_data["body"] = body
        
        # Create pull request
        response = requests.post(
            f"https://api.github.com/repos/{repository.owner}/{repository.name}/pulls",
            headers=headers,
            json=pr_data
        )
        
        # Check response
        if response.status_code in (200, 201):
            pr_data = response.json()
            return IntegrationResult(
                success=True,
                message=f"Pull request created successfully",
                data={"pr_url": pr_data["html_url"]}
            )
        else:
            return IntegrationResult(
                success=False,
                message=f"Failed to create pull request: {response.text}",
                data=None
            )
    except Exception as e:
        raise GitHubIntegrationError(f"Error creating pull request: {str(e)}")


def upload_blog_post(
    credentials: GitHubCredentials,
    repository: GitHubRepository,
    title: str,
    content: str,
    path: Optional[str] = None,
    branch: str = "main",
    commit_message: Optional[str] = None
) -> IntegrationResult:
    """
    Upload a blog post to GitHub.
    
    Args:
        credentials: The GitHub credentials.
        repository: The GitHub repository.
        title: The title of the blog post.
        content: The content of the blog post.
        path: The path to save the blog post.
        branch: The branch to upload to.
        commit_message: The commit message.
        
    Returns:
        The integration result.
        
    Raises:
        GitHubIntegrationError: If an error occurs during upload.
    """
    try:
        # Create safe filename from title
        safe_title = title.lower().replace(" ", "-").replace(":", "").replace("'", "").replace('"', "")
        
        # Create path if not provided
        if not path:
            path = f"content/blog/{safe_title}.md"
        
        # Create commit message if not provided
        if not commit_message:
            commit_message = f"Add blog post: {title}"
        
        # Create file options
        options = GitHubFileOptions(
            path=path,
            content=content,
            message=commit_message,
            branch=branch
        )
        
        # Upload file
        return upload_file(credentials, repository, options)
    except Exception as e:
        raise GitHubIntegrationError(f"Error uploading blog post: {str(e)}")
