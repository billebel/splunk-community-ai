# Social Media Automation Setup

This guide explains how to set up the automated social media cross-posting for your fork of the Splunk Community AI project.

## Overview

The blog automation system can automatically post significant development updates to:
- **Twitter/X** - Technical updates with hashtags
- **Reddit** - Detailed posts in relevant subreddits (r/splunk, r/devops, etc.)
- **LinkedIn** - Professional updates for cybersecurity community

## Required GitHub Secrets

To enable social media posting, add these secrets to your GitHub repository:

### Twitter/X API Setup

1. Apply for Twitter Developer access at [developer.twitter.com](https://developer.twitter.com)
2. Create a new app and generate API keys
3. Add these GitHub secrets:

```
TWITTER_API_KEY=your_api_key_here
TWITTER_API_SECRET=your_api_secret_here  
TWITTER_ACCESS_TOKEN=your_access_token_here
TWITTER_ACCESS_SECRET=your_access_secret_here
```

### Reddit API Setup

1. Create a Reddit app at [reddit.com/prefs/apps](https://reddit.com/prefs/apps)
2. Choose "script" type application
3. Add these GitHub secrets:

```
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USER_AGENT=YourBotName/1.0 by YourUsername
```

### LinkedIn API Setup (Optional)

1. Create a LinkedIn app at [developer.linkedin.com](https://developer.linkedin.com)
2. Generate access tokens
3. Add this GitHub secret:

```
LINKEDIN_ACCESS_TOKEN=your_access_token_here
```

## Configuration

### What Gets Posted Automatically

The system automatically posts when commits match these patterns:
- `feat:` - New features 
- `security:` - Security improvements
- `BREAKING CHANGE` - Major changes
- `release:` - Version releases

### What Doesn't Get Posted

- Minor fixes and typos
- Documentation updates
- Automated commits
- Posts marked with `social_media: false`

### Customizing Social Media Content

You can customize the social media posting behavior by editing:
- `.github/scripts/social-media-post.py` - Main posting logic
- `.github/scripts/analyze-commits.py` - What triggers posts

### Manual Control

To manually trigger a blog post and social sharing:
1. Add `[blog]` or `blog: Custom Title` to your commit message
2. Use the "Auto-Generate Blog Posts" workflow dispatch in GitHub Actions

## Platform-Specific Posting

### Twitter/X Posts Format
```
🚀 New Feature: Enhanced CI/CD Pipeline

✅ Multi-Python version testing
✅ Dependency caching  
✅ Coverage reporting

👀 Details: https://your-blog-url

#DevOps #Automation #Splunk
```

### Reddit Posts Format
```
Title: [Open Source] Enhanced CI/CD Pipeline

Just pushed some major improvements to our Splunk Community AI platform:

**What we built:** Multi-Python version testing and dependency caching

**Key improvements:**
• Enhanced CI/CD pipeline with better testing
• Performance optimizations

**Technical details:** https://your-blog-url

This is part of our open-source reference model for secure AI integration 
with Splunk Enterprise. Feedback and contributions welcome!
```

### LinkedIn Posts Format
```
🎯 Development Update: Enhanced CI/CD Pipeline

We've made significant improvements to our open-source Splunk Community AI platform:

⚡ Improved development workflows and automation
📈 Better performance and reliability

This represents our continued commitment to transparent, community-driven 
development in the cybersecurity and AI space.

Technical details: https://your-blog-url

#OpenSource #Splunk #AI #Cybersecurity #DevOps
```

## Testing

To test your social media integration:

1. Make a commit with `feat:` prefix
2. Check the GitHub Actions logs for the "Auto-Generate Blog Posts" workflow
3. Verify the blog post was created in `blog/_posts/`
4. Check that social media posts were generated (look at the workflow logs)

## Troubleshooting

### Common Issues

**"No blog post found"**
- Check that your commit matched the blog-worthy patterns
- Verify the blog post was created in `blog/_posts/`

**"Social media credentials not available"**
- Ensure all required secrets are set in GitHub repository settings
- Check that secret names match exactly (case-sensitive)

**"Blog post not marked for social media sharing"**
- The commit didn't match significant update patterns
- Try adding `blog:` to your commit message to force posting

### Debugging

Enable debug logging by adding this to your workflow:
```yaml
env:
  DEBUG: true
```

## Security Notes

- API credentials are stored as GitHub Secrets (encrypted)
- The posting scripts are publicly visible but don't contain credentials
- Social media posting can be disabled by removing the secrets
- All posts include links back to your repository for transparency

## Customization Examples

### Adding New Platforms

To add Discord, Slack, or other platforms:
1. Add new posting method to `social-media-post.py`
2. Add required secrets to GitHub
3. Update the posting workflow

### Custom Hashtags

Edit the `tag_map` in `social-media-post.py`:
```python
tag_map = {
    'your-tag': '#YourHashtag',
    'security': '#InfoSec',  # Custom security hashtag
}
```

### Different Subreddits

Modify the subreddit selection logic:
```python
if 'your-topic' in tags:
    subreddits.append('r/YourSubreddit')
```