#!/usr/bin/env python3
"""
Analyze commits to determine if they warrant a blog post.
This script examines commit messages, file changes, and patterns to decide
if a commit represents significant development worth sharing.
"""

import os
import subprocess
import re
import json
import sys
from datetime import datetime

def run_git_command(cmd):
    """Execute git command and return output."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip(), result.returncode
    except Exception as e:
        print(f"Error running git command: {e}")
        return "", 1

def analyze_commit(commit_hash="HEAD"):
    """Analyze a commit to determine if it's blog-worthy."""
    
    # Get commit info
    commit_msg, _ = run_git_command(f"git log -1 --pretty=format:'%s' {commit_hash}")
    commit_body, _ = run_git_command(f"git log -1 --pretty=format:'%b' {commit_hash}")
    files_changed, _ = run_git_command(f"git diff-tree --no-commit-id --name-only -r {commit_hash}")
    
    analysis = {
        "commit_hash": commit_hash[:8],
        "message": commit_msg,
        "body": commit_body,
        "files_changed": files_changed.split('\n') if files_changed else [],
        "should_create_post": False,
        "social_worthy": False,
        "post_category": "development",
        "post_tags": [],
        "post_title": "",
        "reasoning": []
    }
    
    # Patterns that indicate blog-worthy commits
    blog_worthy_patterns = [
        (r"^feat(\(.+\))?: ", "feature", ["feature", "enhancement"]),
        (r"^fix(\(.+\))?: ", "bugfix", ["bugfix", "improvement"]),
        (r"^perf(\(.+\))?: ", "performance", ["performance", "optimization"]),
        (r"^security(\(.+\))?: ", "security", ["security", "safety"]),
        (r"^BREAKING CHANGE", "breaking", ["breaking-change", "major"]),
        (r"^release:", "release", ["release", "version"]),
        (r"^ci(\(.+\))?: ", "ci-cd", ["ci-cd", "automation"]),
        (r"^docs(\(.+\))?: ", "documentation", ["documentation", "guides"]),
    ]
    
    # Social media worthy patterns (subset of blog-worthy)
    social_patterns = [
        r"^feat.*: .*(?:new|add|implement).*",
        r"^release:",
        r"^BREAKING CHANGE",
        r"^security.*:",
        r".*(?:launch|release|milestone).*"
    ]
    
    # File change patterns that indicate significance
    significant_files = [
        (r"\.github/workflows/.*\.yml$", "ci-cd updates"),
        (r"docker-compose.*\.yml$", "deployment changes"),
        (r"README\.md$", "documentation updates"),
        (r"requirements.*\.txt$", "dependency updates"),
        (r".*\.py$", "code changes"),
        (r".*guardrails.*", "security updates"),
        (r".*test.*\.py$", "test improvements"),
    ]
    
    # Check commit message patterns
    for pattern, category, tags in blog_worthy_patterns:
        if re.search(pattern, commit_msg, re.IGNORECASE):
            analysis["should_create_post"] = True
            analysis["post_category"] = category
            analysis["post_tags"] = tags
            analysis["reasoning"].append(f"Matches {category} pattern: {pattern}")
            
            # Generate title from commit message
            title = re.sub(r"^[a-z]+(\(.+\))?: ", "", commit_msg, flags=re.IGNORECASE)
            analysis["post_title"] = title.capitalize()
            break
    
    # Check for social media worthiness
    for pattern in social_patterns:
        if re.search(pattern, commit_msg, re.IGNORECASE):
            analysis["social_worthy"] = True
            analysis["reasoning"].append(f"Social worthy: matches {pattern}")
            break
    
    # Check file significance
    significant_changes = 0
    for file_path in analysis["files_changed"]:
        for pattern, description in significant_files:
            if re.search(pattern, file_path):
                significant_changes += 1
                analysis["reasoning"].append(f"Significant file: {file_path} ({description})")
                break
    
    # If many significant files changed, it's probably blog-worthy
    if significant_changes >= 3 and not analysis["should_create_post"]:
        analysis["should_create_post"] = True
        analysis["post_category"] = "improvement"
        analysis["post_tags"] = ["improvement", "maintenance"]
        analysis["post_title"] = f"Multiple improvements and updates"
        analysis["reasoning"].append(f"Multiple significant files changed ({significant_changes})")
    
    # Special handling for merge commits
    if "Merge pull request" in commit_msg:
        # Extract PR number
        pr_match = re.search(r"#(\d+)", commit_msg)
        if pr_match:
            analysis["pr_number"] = pr_match.group(1)
            # Don't auto-post for merge commits, let PR analysis handle it
            analysis["should_create_post"] = False
            analysis["reasoning"].append("Merge commit - handled by PR analysis")
    
    # Check for manual blog indicators in commit body
    if "blog:" in commit_body.lower() or "[blog]" in commit_body.lower():
        analysis["should_create_post"] = True
        analysis["reasoning"].append("Manual blog indicator found in commit body")
        
        # Look for custom title
        title_match = re.search(r"blog:\s*(.+?)(?:\n|$)", commit_body, re.IGNORECASE)
        if title_match:
            analysis["post_title"] = title_match.group(1).strip()
    
    # Skip if this looks like an automated commit
    automated_patterns = [
        r"^Auto-generated",
        r"^Automated",
        r"^📝 Auto-generated blog post",
        r"^\[bot\]",
        r"^Update.*\.md$",
    ]
    
    for pattern in automated_patterns:
        if re.search(pattern, commit_msg):
            analysis["should_create_post"] = False
            analysis["reasoning"].append(f"Skipped: automated commit pattern {pattern}")
            break
    
    return analysis

def main():
    """Main function to analyze commits and set GitHub Actions outputs."""
    
    commit_hash = os.getenv("GITHUB_SHA", "HEAD")
    
    print(f"Analyzing commit: {commit_hash}")
    
    analysis = analyze_commit(commit_hash)
    
    print("Analysis results:")
    print(json.dumps(analysis, indent=2))
    
    # Set GitHub Actions outputs
    github_output = os.getenv("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"should_create_post={str(analysis['should_create_post']).lower()}\n")
            f.write(f"social_worthy={str(analysis['social_worthy']).lower()}\n")
            f.write(f"post_title={analysis['post_title']}\n")
            f.write(f"post_category={analysis['post_category']}\n")
            f.write(f"post_tags={','.join(analysis['post_tags'])}\n")
    
    # Exit with appropriate code
    sys.exit(0 if analysis["should_create_post"] else 1)

if __name__ == "__main__":
    main()