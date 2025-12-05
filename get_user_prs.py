#!/usr/bin/env python3
"""
Script to retrieve all completed PRs for a given user in Azure DevOps
and save them to a JSON file.
"""

import json
import subprocess
import sys
import argparse

# Hard-coded organization and project
ORGANIZATION = "LHG-DES"
PROJECT = "lhg"


def get_user_completed_prs(repository_name, creator_name):
    """
    Retrieve all active and completed PRs for a specific user using Azure CLI.
    
    Args:
        repository_name: Name of the repository
        creator_name: Display name of the PR creator
        
    Returns:
        List of PR IDs
    """
    try:
        # Get all PRs (active and completed) for the repository filtered by creator
        cmd = [
            "az", "repos", "pr", "list",
            "--repository", repository_name,
            "--project", PROJECT,
            "--org", f"https://dev.azure.com/{ORGANIZATION}",
            "--creator", creator_name,
            "--status", "all",
            "--top", "10000",  # Set high limit to get all PRs from 2022-2025
            "--output", "json"
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        prs_data = json.loads(result.stdout)
        
        # Filter PRs by status (active or completed), then extract PR IDs
        pr_ids = []
        for pr in prs_data:
            status = pr.get("status", "")
            
            # Include only active or completed PRs
            if status in ["active", "completed"]:
                pr_id = pr.get("pullRequestId")
                if pr_id:
                    pr_ids.append(str(pr_id))
        
        return pr_ids
        
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
    """Main function to parse arguments and retrieve user's completed PRs."""
    parser = argparse.ArgumentParser(
        description="Retrieve all active and completed PRs for a given user in Azure DevOps"
    )
    parser.add_argument(
        "--repository",
        required=True,
        help="Repository name"
    )
    parser.add_argument(
        "--user",
        required=True,
        help="User display name (e.g., 'Ahmet Atar')"
    )
    parser.add_argument(
        "--output",
        default="user_prs.json",
        help="Output file path (default: user_prs.json)"
    )
    
    args = parser.parse_args()
    
    # Get user's completed PRs
    pr_ids = get_user_completed_prs(args.repository, args.user)
    
    # Write to file in the specified format (PR IDs separated by lines)
    with open(args.output, "w", encoding="utf-8") as f:
        for pr_id in pr_ids:
            f.write(f"{pr_id},\n")


if __name__ == "__main__":
    main()
