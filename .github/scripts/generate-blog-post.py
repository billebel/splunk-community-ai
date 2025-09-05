#!/usr/bin/env python3
"""
Generate blog posts from commit analysis.
This script creates markdown blog posts based on commit changes and metadata.
"""

import os
import subprocess
import re
import json
from datetime import datetime, timezone
from pathlib import Path

def run_git_command(cmd):
    """Execute git command and return output."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip(), result.returncode
    except Exception as e:
        print(f"Error running git command: {e}")
        return "", 1

def get_commit_details(commit_hash):
    """Get detailed commit information."""
    commit_msg, _ = run_git_command(f"git log -1 --pretty=format:'%s' {commit_hash}")
    commit_body, _ = run_git_command(f"git log -1 --pretty=format:'%b' {commit_hash}")
    author_name, _ = run_git_command(f"git log -1 --pretty=format:'%an' {commit_hash}")
    author_email, _ = run_git_command(f"git log -1 --pretty=format:'%ae' {commit_hash}")
    commit_date, _ = run_git_command(f"git log -1 --pretty=format:'%ci' {commit_hash}")
    files_changed, _ = run_git_command(f"git diff-tree --no-commit-id --name-only -r {commit_hash}")
    diff_stat, _ = run_git_command(f"git diff-tree --stat --no-commit-id -r {commit_hash}")
    
    return {
        "hash": commit_hash,
        "short_hash": commit_hash[:8],
        "message": commit_msg,
        "body": commit_body,
        "author_name": author_name,
        "author_email": author_email,
        "date": commit_date,
        "files_changed": files_changed.split('\n') if files_changed else [],
        "diff_stat": diff_stat
    }

def analyze_changes(files_changed):
    """Analyze the types of changes made."""
    categories = {
        "features": [],
        "bug_fixes": [],
        "documentation": [],
        "tests": [],
        "ci_cd": [],
        "security": [],
        "performance": [],
        "dependencies": []
    }
    
    patterns = {
        "features": [r".*(?:feature|feat|new).*\.py$", r".*tools/.*\.yaml$"],
        "bug_fixes": [r".*(?:fix|bug).*\.py$"],
        "documentation": [r".*\.md$", r".*docs/.*", r".*README.*"],
        "tests": [r".*test.*\.py$", r".*tests/.*"],
        "ci_cd": [r"\.github/workflows/.*", r"docker-compose.*\.yml$", r"Dockerfile"],
        "security": [r".*guardrails.*", r".*security.*"],
        "performance": [r".*perf.*", r".*optimization.*"],
        "dependencies": [r"requirements.*\.txt$", r"Gemfile", r"package\.json"]
    }
    
    for file_path in files_changed:
        for category, category_patterns in patterns.items():
            for pattern in category_patterns:
                if re.search(pattern, file_path, re.IGNORECASE):
                    categories[category].append(file_path)
                    break
    
    return categories

def generate_blog_post_content(commit_details, categories, pr_number=None):
    """Generate the actual blog post content."""
    
    commit_msg = commit_details["message"]
    commit_body = commit_details["body"]
    
    # Determine post type and category from commit message
    post_type = "development"
    tags = ["development"]
    
    if re.search(r"^feat", commit_msg, re.IGNORECASE):
        post_type = "feature"
        tags = ["feature", "enhancement"]
    elif re.search(r"^fix", commit_msg, re.IGNORECASE):
        post_type = "bugfix"
        tags = ["bugfix", "improvement"]
    elif re.search(r"^perf", commit_msg, re.IGNORECASE):
        post_type = "performance"
        tags = ["performance", "optimization"]
    elif re.search(r"^security", commit_msg, re.IGNORECASE):
        post_type = "security"
        tags = ["security", "safety"]
    elif re.search(r"^ci", commit_msg, re.IGNORECASE):
        post_type = "ci-cd"
        tags = ["ci-cd", "automation"]
    elif re.search(r"^docs", commit_msg, re.IGNORECASE):
        post_type = "documentation"
        tags = ["documentation", "guides"]
    
    # Generate title
    title = re.sub(r"^[a-z]+(\(.+\))?: ", "", commit_msg, flags=re.IGNORECASE)
    title = title.capitalize()
    
    # Create filename-friendly version
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    filename_title = re.sub(r"[^a-z0-9]+", "-", title.lower())
    filename_title = re.sub(r"-+", "-", filename_title).strip("-")
    filename = f"{date_str}-{filename_title}.md"
    
    # Build the blog post content
    content = f"""---
layout: post
title: "{title}"
date: {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S +0000")}
categories: [{post_type}, development]
tags: {tags}
author: "Development Team"
commit_hash: "{commit_details['short_hash']}"
"""
    
    if pr_number:
        content += f"pull_request: {pr_number}\n"
    
    content += f"""social_media: true
excerpt: "Latest development update: {commit_msg}"
---

## What We Did

{commit_msg}

"""
    
    if commit_body and commit_body.strip():
        content += f"{commit_body}\n\n"
    
    # Add technical details based on file changes
    if any(categories.values()):
        content += "## Changes Made\n\n"
        
        if categories["features"]:
            content += "### ✨ New Features\n"
            for file in categories["features"]:
                content += f"- Updated `{file}`\n"
            content += "\n"
        
        if categories["bug_fixes"]:
            content += "### 🐛 Bug Fixes\n"
            for file in categories["bug_fixes"]:
                content += f"- Fixed issues in `{file}`\n"
            content += "\n"
        
        if categories["ci_cd"]:
            content += "### 🔧 CI/CD Improvements\n"
            for file in categories["ci_cd"]:
                content += f"- Enhanced `{file}`\n"
            content += "\n"
        
        if categories["security"]:
            content += "### 🛡️ Security Enhancements\n"
            for file in categories["security"]:
                content += f"- Improved security in `{file}`\n"
            content += "\n"
        
        if categories["documentation"]:
            content += "### 📖 Documentation Updates\n"
            for file in categories["documentation"]:
                content += f"- Updated `{file}`\n"
            content += "\n"
        
        if categories["tests"]:
            content += "### 🧪 Testing Improvements\n"
            for file in categories["tests"]:
                content += f"- Enhanced `{file}`\n"
            content += "\n"
    
    # Add file change statistics
    if commit_details["diff_stat"]:
        content += "## Technical Details\n\n"
        content += "```\n"
        content += commit_details["diff_stat"]
        content += "\n```\n\n"
    
    # Add links and footer
    content += "---\n\n"
    content += "**Technical Details:**\n"
    content += f"- **Commit**: [`{commit_details['short_hash']}`](https://github.com/billebel/splunk-community-ai/commit/{commit_details['hash']})\n"
    
    if pr_number:
        content += f"- **Pull Request**: [#{pr_number}](https://github.com/billebel/splunk-community-ai/pull/{pr_number})\n"
    
    if commit_details["files_changed"]:
        content += f"- **Files Changed**: {len(commit_details['files_changed'])} files\n"
    
    content += "\n*This post was automatically generated from development activity.*"
    
    return content, filename

def main():
    """Main function to generate blog posts."""
    
    commit_hash = os.getenv("COMMIT_HASH", os.getenv("GITHUB_SHA", "HEAD"))
    pr_number = os.getenv("PR_NUMBER")
    
    print(f"Generating blog post for commit: {commit_hash}")
    
    # Get commit details
    commit_details = get_commit_details(commit_hash)
    print(f"Commit message: {commit_details['message']}")
    
    # Analyze changes
    categories = analyze_changes(commit_details["files_changed"])
    print(f"Change categories: {categories}")
    
    # Generate blog post content
    content, filename = generate_blog_post_content(commit_details, categories, pr_number)
    
    # Write the blog post file
    blog_dir = Path("blog/_posts")
    blog_dir.mkdir(parents=True, exist_ok=True)
    
    blog_file = blog_dir / filename
    with open(blog_file, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"Generated blog post: {blog_file}")
    print("Content preview:")
    print("=" * 50)
    print(content[:500] + "..." if len(content) > 500 else content)
    print("=" * 50)

if __name__ == "__main__":
    main()