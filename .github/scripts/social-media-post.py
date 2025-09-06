#!/usr/bin/env python3
"""
Social media cross-posting automation.
Automatically posts blog content to Twitter, Reddit, LinkedIn, etc.
"""

import os
import json
import requests
import time
from datetime import datetime
from pathlib import Path
import re

class SocialMediaPoster:
    def __init__(self):
        self.github_repo = "billebel/splunk-community-ai"
        self.blog_base_url = f"https://{self.github_repo.split('/')[0]}.github.io/splunk-community-ai/blog"
        
        # API credentials (from GitHub Secrets)
        self.twitter_api_key = os.getenv("TWITTER_API_KEY")
        self.twitter_api_secret = os.getenv("TWITTER_API_SECRET")
        self.twitter_access_token = os.getenv("TWITTER_ACCESS_TOKEN")
        self.twitter_access_secret = os.getenv("TWITTER_ACCESS_SECRET")
        
        self.reddit_client_id = os.getenv("REDDIT_CLIENT_ID")
        self.reddit_client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        self.reddit_user_agent = os.getenv("REDDIT_USER_AGENT")
        
        self.linkedin_access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
        
    def get_latest_blog_post(self):
        """Get the most recent blog post from the _posts directory."""
        posts_dir = Path("blog/_posts")
        if not posts_dir.exists():
            return None
        
        # Get the most recent post file
        post_files = list(posts_dir.glob("*.md"))
        if not post_files:
            return None
        
        latest_post = max(post_files, key=os.path.getctime)
        
        # Parse the front matter and content
        with open(latest_post, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract front matter
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                front_matter_text = parts[1]
                post_content = parts[2].strip()
                
                # Parse YAML-like front matter (simple parsing)
                front_matter = {}
                for line in front_matter_text.strip().split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        if key == 'tags':
                            value = [tag.strip() for tag in value.strip('[]').split(',')]
                        elif key == 'categories':
                            value = [cat.strip() for cat in value.strip('[]').split(',')]
                        front_matter[key] = value
                
                # Generate blog post URL
                filename = latest_post.stem
                post_url = f"{self.blog_base_url}/{filename.replace('_', '/')}.html"
                
                return {
                    'title': front_matter.get('title', 'Development Update'),
                    'excerpt': front_matter.get('excerpt', ''),
                    'categories': front_matter.get('categories', []),
                    'tags': front_matter.get('tags', []),
                    'commit_hash': front_matter.get('commit_hash', ''),
                    'url': post_url,
                    'content': post_content,
                    'social_media': front_matter.get('social_media', False)
                }
        
        return None
    
    def create_twitter_post(self, blog_post):
        """Create a Twitter/X post from blog post data."""
        if not all([self.twitter_api_key, self.twitter_api_secret, 
                   self.twitter_access_token, self.twitter_access_secret]):
            print("Twitter credentials not available, skipping Twitter post")
            return False
        
        title = blog_post['title']
        url = blog_post['url']
        tags = blog_post.get('tags', [])
        
        # Create hashtags from tags
        hashtags = []
        tag_map = {
            'feature': '#NewFeature',
            'security': '#CyberSecurity', 
            'ci-cd': '#DevOps',
            'performance': '#Performance',
            'automation': '#Automation',
            'splunk': '#Splunk',
            'ai': '#AI',
            'mcp': '#MCP'
        }
        
        for tag in tags[:3]:  # Limit to 3 hashtags
            hashtags.append(tag_map.get(tag, f'#{tag.title()}'))
        
        # Create tweet text (280 char limit)
        emoji = self.get_emoji_for_category(blog_post.get('categories', []))
        tweet_text = f"{emoji} {title}\n\n"
        
        # Add key points if we have space
        if len(tweet_text + url + ' '.join(hashtags)) < 200:
            if 'ci-cd' in tags:
                tweet_text += "✅ Enhanced automation & testing\n"
            elif 'security' in tags:
                tweet_text += "🛡️ Security improvements\n" 
            elif 'feature' in tags:
                tweet_text += "🚀 New capabilities added\n"
        
        tweet_text += f"\n👀 Details: {url}"
        
        if hashtags and len(tweet_text + ' '.join(hashtags)) < 270:
            tweet_text += f"\n{' '.join(hashtags)}"
        
        # For now, just print what we would post (actual Twitter API integration would go here)
        print(f"Would post to Twitter:")
        print(f"Text: {tweet_text}")
        print(f"Length: {len(tweet_text)} characters")
        
        return True
    
    def create_reddit_post(self, blog_post):
        """Create Reddit posts in relevant subreddits."""
        if not all([self.reddit_client_id, self.reddit_client_secret]):
            print("Reddit credentials not available, skipping Reddit post")
            return False
        
        title = blog_post['title']
        url = blog_post['url']
        categories = blog_post.get('categories', [])
        tags = blog_post.get('tags', [])
        
        # Determine relevant subreddits based on content
        subreddits = []
        if 'security' in tags or 'splunk' in tags:
            subreddits.append('r/splunk')
        if 'ci-cd' in tags or 'automation' in tags:
            subreddits.append('r/devops')
        if 'ai' in tags:
            subreddits.append('r/MachineLearning')
        
        # Create Reddit-style post
        reddit_title = f"[Open Source] {title}"
        reddit_text = f"""Just pushed some updates to our Splunk Community AI platform:

**What we built:** {blog_post.get('excerpt', title)}

**Key improvements:**
"""
        
        # Add bullet points based on tags
        if 'ci-cd' in tags:
            reddit_text += "• Enhanced CI/CD pipeline with better testing\n"
        if 'security' in tags:
            reddit_text += "• Security improvements and guardrails\n"
        if 'performance' in tags:
            reddit_text += "• Performance optimizations\n"
        
        reddit_text += f"""
**Technical details:** {url}

This is part of our open-source reference model for secure AI integration with Splunk Enterprise. Feedback and contributions welcome!

**Repository:** https://github.com/{self.github_repo}
"""
        
        print(f"Would post to Reddit ({', '.join(subreddits)}):")
        print(f"Title: {reddit_title}")
        print(f"Text: {reddit_text}")
        
        return True
    
    def create_linkedin_post(self, blog_post):
        """Create a LinkedIn post for professional audience."""
        title = blog_post['title']
        url = blog_post['url']
        tags = blog_post.get('tags', [])
        
        # Professional tone for LinkedIn
        linkedin_text = f"🎯 Development Update: {title}\n\n"
        
        linkedin_text += "We've made significant improvements to our open-source Splunk Community AI platform:\n\n"
        
        # Professional benefits focus
        if 'security' in tags:
            linkedin_text += "🛡️ Enhanced security controls and audit capabilities\n"
        if 'ci-cd' in tags:
            linkedin_text += "⚡ Improved development workflows and automation\n"
        if 'performance' in tags:
            linkedin_text += "📈 Better performance and reliability\n"
        
        linkedin_text += f"\nThis represents our continued commitment to transparent, community-driven development in the cybersecurity and AI space.\n\n"
        linkedin_text += f"Technical details: {url}\n\n"
        linkedin_text += f"#OpenSource #Splunk #AI #Cybersecurity #DevOps"
        
        print(f"Would post to LinkedIn:")
        print(f"Text: {linkedin_text}")
        
        return True
    
    def get_emoji_for_category(self, categories):
        """Get appropriate emoji for post category."""
        emoji_map = {
            'feature': '🚀',
            'bugfix': '🐛', 
            'security': '🛡️',
            'performance': '⚡',
            'ci-cd': '🔧',
            'documentation': '📖',
            'release': '📦'
        }
        
        for category in categories:
            if category in emoji_map:
                return emoji_map[category]
        
        return '🔧'  # Default
    
    def should_post_to_social_media(self, blog_post):
        """Determine if this post should be shared on social media."""
        
        # Check if explicitly marked for social media
        if blog_post.get('social_media') is False:
            return False
        
        # Skip automated/minor posts
        title = blog_post.get('title', '').lower()
        skip_patterns = [
            'auto-generated',
            'minor fix',
            'typo',
            'update readme',
            'formatting'
        ]
        
        for pattern in skip_patterns:
            if pattern in title:
                return False
        
        # Only post significant updates
        significant_tags = ['feature', 'security', 'release', 'breaking-change']
        tags = blog_post.get('tags', [])
        
        return any(tag in significant_tags for tag in tags)
    
    def post_to_all_platforms(self):
        """Main function to post to all social media platforms."""
        
        blog_post = self.get_latest_blog_post()
        if not blog_post:
            print("No blog post found to share")
            return False
        
        print(f"Processing blog post: {blog_post['title']}")
        
        # Check if we should post to social media
        if not self.should_post_to_social_media(blog_post):
            print("Blog post not marked for social media sharing")
            return False
        
        success = True
        
        # Post to each platform
        try:
            success &= self.create_twitter_post(blog_post)
        except Exception as e:
            print(f"Twitter posting failed: {e}")
            success = False
        
        try:
            success &= self.create_reddit_post(blog_post)
        except Exception as e:
            print(f"Reddit posting failed: {e}")
            success = False
        
        try:
            success &= self.create_linkedin_post(blog_post)
        except Exception as e:
            print(f"LinkedIn posting failed: {e}")
            success = False
        
        return success

def main():
    """Main function."""
    poster = SocialMediaPoster()
    success = poster.post_to_all_platforms()
    
    if success:
        print("✅ Social media posting completed successfully")
    else:
        print("⚠️ Some social media posts may have failed")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())