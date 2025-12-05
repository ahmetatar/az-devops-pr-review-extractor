# Azure DevOps PR Review Extractor

Python scripts to retrieve and analyze Pull Request comments from Azure DevOps using the Azure CLI.

## Prerequisites

- Python 3.6 or higher
- Azure CLI with DevOps extension installed
- Authenticated Azure CLI session

### Install Azure CLI DevOps Extension

```bash
az extension add --name azure-devops
```

### Authentication

Ensure you're logged in to Azure DevOps:

```bash
az login
az devops configure --defaults organization=https://dev.azure.com/LHG-DES project=lhg
```

## Scripts

### 1. `get_pr_comments.py`

Main script that retrieves all PR comments for a specific user.

**Features:**
- Automatically fetches all active and completed PRs for a user
- Retrieves comments from each PR
- Appends comments to existing file (non-destructive)
- Includes reviewer name, comment text, and timestamp
- Filters out system-generated comments

**Usage:**

```bash
python3 get_pr_comments.py --repository <repo_name> --user "<User Display Name>"
```

**Example:**

```bash
python3 get_pr_comments.py --repository lhg --user "Deniz KALKAN"
```

**Options:**
- `--repository`: Repository name (required)
- `--user`: User display name as shown in Azure DevOps (required)
- `--output`: Output file path (default: `pr_comments.json`)

**Output Format:**

```json
[
  {
    "reviewer_name": "John Doe",
    "comment": "This looks good, but consider...",
    "date": "2025-11-24T16:02:47.68Z"
  }
]
```

### 2. `get_user_prs.py`

Utility script that retrieves all PR IDs for a specific user.

**Usage:**

```bash
python3 get_user_prs.py --repository <repo_name> --user "<User Display Name>"
```

**Example:**

```bash
python3 get_user_prs.py --repository lhg --user "USER_NAME"
```

**Options:**
- `--repository`: Repository name (required)
- `--user`: User display name (required)
- `--output`: Output file path (default: `user_prs.json`)

**Output Format:**

```
12891,
12078,
11195,
```

## Configuration

Both scripts use hard-coded organization and project values:

```python
ORGANIZATION = "LHG-DES"
PROJECT = "lhg"
```

To use with a different organization or project, modify these values in the script files.

## Workflow

The `get_pr_comments.py` script follows this workflow:

1. Calls `get_user_prs.py` to retrieve all PRs for the specified user
2. Reads the generated `user_prs.json` file
3. Iterates through each PR and fetches all comments
4. Appends new comments to `pr_comments.json`
5. Deletes the temporary `user_prs.json` file

## Notes

- Comments are appended to the output file, allowing incremental collection
- System-generated comments (policy updates, etc.) are automatically filtered out
- The script retrieves PRs from 2022-2025 by setting `--top 10000`
- Only PRs with "active" or "completed" status are processed
- Progress is displayed to stderr during execution

## Example Output

```
Fetching PRs for user: USER NAME...
Found 25 PRs to process...
Processing PR 12891 (1/25)...
Processing PR 12078 (2/25)...
...
Successfully saved 122 new comments to pr_comments.json
Total comments in file: 122
Deleted temporary file: user_prs.json
```

## Troubleshooting

### Authentication Issues

If you encounter authentication errors:

```bash
az logout
az login
az devops configure --defaults organization=https://dev.azure.com/LHG-DES project=lhg
```

### No PRs Found

- Verify the user display name matches exactly as shown in Azure DevOps
- Check that the repository name is correct
- Ensure you have access to the repository and project

### Rate Limiting

If processing many PRs, the script may take several minutes to complete. Each PR requires a separate API call to retrieve comments.

## License

Internal use only.
