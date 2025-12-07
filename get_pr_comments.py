#!/usr/bin/env python3
"""
Script to retrieve all comments from Azure DevOps Pull Requests for a given user
and save them to a JSON file.

This script:
1. Runs get_user_prs.py to get all PRs for a user
2. Retrieves comments for each PR
3. Appends all comments to pr_comments.json
4. Deletes the temporary user_prs.json file
"""

import json
import subprocess
import sys
import argparse
import os

# Hard-coded organization and project
ORGANIZATION = "ORG"
PROJECT = "PRJ"

def get_repository_id(repository_name):
    """
    Get the repository ID from the repository name.
    
    Args:
        repository_name: Name of the repository
        
    Returns:
        Repository ID (GUID)
    """
    try:
        cmd = [
            "az", "repos", "show",
            "--repository", repository_name,
            "--project", PROJECT,
            "--org", f"https://dev.azure.com/{ORGANIZATION}",
            "--output", "json"
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        repo_data = json.loads(result.stdout)
        return repo_data["id"]
        
    except subprocess.CalledProcessError as e:
        print(f"Error getting repository ID: {e}", file=sys.stderr)
        print(f"stderr: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error parsing repository data: {e}", file=sys.stderr)
        sys.exit(1)


def get_pr_comments(repository_name, pr_number):
    """
    Retrieve all comments from a Pull Request using Azure CLI.
    
    Args:
        repository_name: Name of the repository
        pr_number: Pull request number
        
    Returns:
        List of dictionaries with reviewer_name and comment
    """
    try:
        # Get repository ID first
        repo_id = get_repository_id(repository_name)
        
        # Construct the REST API URL for PR threads
        # API: https://docs.microsoft.com/en-us/rest/api/azure/devops/git/pull-request-threads/list
        api_url = f"https://dev.azure.com/{ORGANIZATION}/{PROJECT}/_apis/git/repositories/{repo_id}/pullRequests/{pr_number}/threads?api-version=7.0"
        
        # Use az rest command with Azure DevOps resource ID
        # 499b84ac-1321-427f-aa17-267ca6975798 is the Azure DevOps resource ID
        threads_cmd = [
            "az", "rest",
            "--resource", "499b84ac-1321-427f-aa17-267ca6975798",
            "--uri", api_url,
            "--method", "GET"
        ]
        
        result = subprocess.run(
            threads_cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        response_data = json.loads(result.stdout)
        threads_data = response_data.get("value", [])
        
        # Extract comments from threads
        comments = []
        for thread in threads_data:
            if "comments" in thread:
                for comment in thread["comments"]:
                    # Extract author name, comment text, and date
                    author = comment.get("author", {}).get("displayName", "Unknown")
                    content = comment.get("content", "")
                    published_date = comment.get("publishedDate", "")
                    
                    # Filter out system comments and only include user comments
                    comment_type = comment.get("commentType", "")
                    if content and comment_type != "system":  # Only include non-empty user comments
                        comments.append({
                            "reviewer_name": author,
                            "comment": content,
                            "date": published_date
                        })
        
        return comments
        
    except subprocess.CalledProcessError as e:
        print(f"Error executing Azure CLI command: {e}", file=sys.stderr)
        print(f"stderr: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main function to parse arguments and retrieve PR comments for a user."""
    parser = argparse.ArgumentParser(
        description="Retrieve all comments from Azure DevOps Pull Requests for a given user"
    )
    parser.add_argument(
        "--repository",
        required=True,
        help="Repository name"
    )
    parser.add_argument(
        "--user",
        required=True,
        help="User display name (e.g., 'Deniz KALKAN')"
    )
    parser.add_argument(
        "--output",
        default="pr_comments.json",
        help="Output JSON file path (default: pr_comments.json)"
    )
    
    args = parser.parse_args()
    
    user_prs_file = "user_prs.json"
    
    # Step 1: Run get_user_prs.py to get all PRs for the user
    print(f"Fetching PRs for user: {args.user}...", file=sys.stderr)
    try:
        subprocess.run(
            [
                "python3", "get_user_prs.py",
                "--repository", args.repository,
                "--user", args.user,
                "--output", user_prs_file
            ],
            check=True,
            capture_output=True,
            text=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Error running get_user_prs.py: {e}", file=sys.stderr)
        print(f"stderr: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    
    # Step 2: Read the PR IDs from user_prs.json
    try:
        with open(user_prs_file, "r", encoding="utf-8") as f:
            pr_ids_text = f.read()
            # Parse PR IDs (format: "ID,\n")
            pr_ids = [line.strip().rstrip(',') for line in pr_ids_text.strip().split('\n') if line.strip()]
    except FileNotFoundError:
        print(f"Error: {user_prs_file} not found", file=sys.stderr)
        sys.exit(1)
    
    print(f"Found {len(pr_ids)} PRs to process...", file=sys.stderr)
    
    # Step 3: Load existing comments if file exists
    existing_comments = []
    try:
        with open(args.output, "r", encoding="utf-8") as f:
            existing_comments = json.load(f)
    except FileNotFoundError:
        pass  # File doesn't exist yet, start with empty list
    except json.JSONDecodeError:
        pass  # File exists but is invalid JSON, start fresh
    
    # Step 4: Get comments for each PR
    all_new_comments = []
    for i, pr_id in enumerate(pr_ids, 1):
        print(f"Processing PR {pr_id} ({i}/{len(pr_ids)})...", file=sys.stderr)
        try:
            comments = get_pr_comments(args.repository, int(pr_id))
            all_new_comments.extend(comments)
        except Exception as e:
            print(f"Warning: Failed to get comments for PR {pr_id}: {e}", file=sys.stderr)
            continue
    
    # Step 5: Append new comments to existing ones
    all_comments = existing_comments + all_new_comments
    
    # Step 6: Write combined comments to JSON file
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(all_comments, f, indent=2, ensure_ascii=False)
    
    print(f"Successfully saved {len(all_new_comments)} new comments to {args.output}", file=sys.stderr)
    print(f"Total comments in file: {len(all_comments)}", file=sys.stderr)
    
    # Step 7: Delete the temporary user_prs.json file
    try:
        os.remove(user_prs_file)
        print(f"Deleted temporary file: {user_prs_file}", file=sys.stderr)
    except OSError as e:
        print(f"Warning: Could not delete {user_prs_file}: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
