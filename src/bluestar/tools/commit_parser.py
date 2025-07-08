"""
Commit Data Parser for BlueStar

Converts GitHub API responses into structured CommitData models.
"""

import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from ..formats.commit_data import CommitData, DiffData
from ..core.exceptions import InvalidCommitError


class CommitDataParser:
    """
    Parses GitHub API commit responses into structured CommitData objects.
    
    Handles commit metadata, file changes, and diff content parsing.
    """
    
    @staticmethod
    def parse_commit_data(
        commit_response: Dict[str, Any], 
        diff_content: str,
        repo_identifier: str
    ) -> CommitData:
        """
        Parse GitHub API commit response into CommitData model.
        
        Args:
            commit_response: GitHub API commit response
            diff_content: Raw diff content from GitHub API
            repo_identifier: Repository identifier (owner/repo)
            
        Returns:
            Structured CommitData object
            
        Raises:
            InvalidCommitError: If commit data is invalid or incomplete
        """
        try:
            # Parse basic commit info
            sha = commit_response["sha"]
            message = commit_response["commit"]["message"]
            
            # Parse author info
            author_info = commit_response["commit"]["author"]
            author = author_info["name"]
            author_email = author_info["email"]
            
            # Parse date
            date_str = author_info["date"]
            date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            
            # Parse file changes
            files_data = commit_response.get("files", [])
            files_changed = [file_data["filename"] for file_data in files_data]
            
            # Calculate totals
            total_additions = sum(file_data.get("additions", 0) for file_data in files_data)
            total_deletions = sum(file_data.get("deletions", 0) for file_data in files_data)
            
            # Parse detailed diffs
            diffs = CommitDataParser._parse_diffs(files_data, diff_content)
            
            # Extract other metadata
            tags = CommitDataParser._extract_tags(commit_response)
            
            return CommitData(
                sha=sha,
                message=message,
                author=author,
                author_email=author_email,
                date=date,
                branch=None,  # GitHub API doesn't always provide branch info in commit response
                files_changed=files_changed,
                total_additions=total_additions,
                total_deletions=total_deletions,
                diffs=diffs,
                repository_path=repo_identifier,
                tags=tags,
                project_structure=None  # Optional, can be enhanced later
            )
            
        except KeyError as e:
            raise InvalidCommitError(
                sha=commit_response.get("sha", "unknown"),
                repo_path=repo_identifier
            ) from e
        except Exception as e:
            raise InvalidCommitError(
                sha=commit_response.get("sha", "unknown"), 
                repo_path=repo_identifier
            ) from e
    
    @staticmethod
    def _parse_diffs(files_data: List[Dict[str, Any]], diff_content: str) -> List[DiffData]:
        """
        Parse file changes and diff content into DiffData objects.
        
        Args:
            files_data: File change data from GitHub API
            diff_content: Raw diff content
            
        Returns:
            List of DiffData objects
        """
        diffs = []
        
        # Split diff content by files
        diff_sections = CommitDataParser._split_diff_by_files(diff_content)
        
        for file_data in files_data:
            filename = file_data["filename"]
            
            # Determine change type
            change_type = CommitDataParser._determine_change_type(file_data)
            
            # Get diff content for this file
            file_diff = diff_sections.get(filename, "")
            
            # Create DiffData object
            diff_data = DiffData(
                file_path=filename,
                change_type=change_type,
                additions=file_data.get("additions", 0),
                deletions=file_data.get("deletions", 0),
                diff_content=file_diff
            )
            
            diffs.append(diff_data)
        
        return diffs
    
    @staticmethod
    def _split_diff_by_files(diff_content: str) -> Dict[str, str]:
        """
        Split unified diff content by individual files.
        
        Args:
            diff_content: Raw unified diff content
            
        Returns:
            Dictionary mapping filename to its diff content
        """
        if not diff_content:
            return {}
        
        file_diffs = {}
        current_file = None
        current_diff = []
        
        lines = diff_content.split('\n')
        
        for line in lines:
            # Check for new file header
            if line.startswith('diff --git'):
                # Save previous file diff
                if current_file and current_diff:
                    file_diffs[current_file] = '\n'.join(current_diff)
                
                # Extract filename from diff header
                # Format: diff --git a/filename b/filename
                match = re.search(r'diff --git a/(.*?) b/(.*?)$', line)
                if match:
                    current_file = match.group(2)  # Use the 'b' version (after change)
                    current_diff = [line]
                else:
                    current_file = None
                    current_diff = []
            elif current_file:
                current_diff.append(line)
        
        # Save last file diff
        if current_file and current_diff:
            file_diffs[current_file] = '\n'.join(current_diff)
        
        return file_diffs
    
    @staticmethod
    def _determine_change_type(file_data: Dict[str, Any]) -> str:
        """
        Determine the type of change for a file.
        
        Args:
            file_data: File data from GitHub API
            
        Returns:
            Change type: "added", "modified", "deleted", or "renamed"
        """
        status = file_data.get("status", "modified")
        
        # GitHub API status values map directly to our types
        status_mapping = {
            "added": "added",
            "removed": "deleted", 
            "modified": "modified",
            "renamed": "renamed"
        }
        
        return status_mapping.get(status, "modified")
    
    @staticmethod
    def _extract_tags(commit_response: Dict[str, Any]) -> List[str]:
        """
        Extract git tags from commit response.
        
        Note: GitHub API commit response doesn't include tag info by default.
        This could be enhanced with additional API calls if needed.
        
        Args:
            commit_response: GitHub API commit response
            
        Returns:
            List of tag names (empty for now)
        """
        # GitHub API doesn't include tag info in basic commit response
        # This would require additional API calls to /repos/{owner}/{repo}/tags
        # For Phase 1, returning empty list
        return []
    
    @staticmethod
    def validate_commit_response(commit_response: Dict[str, Any]) -> bool:
        """
        Validate that commit response has required fields.
        
        Args:
            commit_response: GitHub API commit response
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = [
            "sha",
            "commit.message", 
            "commit.author.name",
            "commit.author.email",
            "commit.author.date"
        ]
        
        for field in required_fields:
            try:
                obj = commit_response
                for key in field.split('.'):
                    obj = obj[key]
            except (KeyError, TypeError):
                return False
        
        return True 