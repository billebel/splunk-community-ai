# Pack Setup Guide

We're still figuring out the best ways to set this up, but here's what we've learned so far.

## Prerequisites

You'll need:
- Docker and Docker Compose
- An AI API key (Claude works well, others should too)
- Either your own Splunk or willingness to try our Docker setup

## Setup Options

### Option 1: Use Your Existing Splunk

If you have Splunk already:

1. **Get your connection details**
   ```bash
   SPLUNK_URL=https://your-splunk.company.com:8089
   SPLUNK_USER=your-username
   SPLUNK_PASSWORD=your-password
   ```

2. **Make sure the user has these permissions**
   - Search capabilities (obviously)
   - Access to REST API endpoints
   - We're still learning what minimum permissions work best

3. **Test the connection**
   ```bash
   curl -k -u username:password "https://your-splunk:8089/services/server/info?output_mode=json"
   ```

### Option 2: Try Our Docker Splunk

If you want to just try it out:

1. **Start a test Splunk instance**
   ```bash
   docker-compose -f docker-compose.splunk.yml up -d
   ```

2. **Wait for it to start up** (takes a few minutes)
   - Check: http://localhost:8000 
   - Login: admin/changeme

3. **Use the defaults in .env**
   ```bash
   SPLUNK_URL=http://localhost:8089
   SPLUNK_USER=admin
   SPLUNK_PASSWORD=changeme
   ```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and fill in what you have:

```bash
# Required - At least one AI provider
ANTHROPIC_API_KEY=your-claude-key
# OPENAI_API_KEY=your-openai-key
# GOOGLE_API_KEY=your-gemini-key

# Splunk connection
SPLUNK_URL=your-splunk-url
SPLUNK_USER=your-username
SPLUNK_PASSWORD=your-password
SPLUNK_HEC_TOKEN=optional-for-logging

# Chat interface (can leave defaults)
JWT_SECRET=change-this-for-production
JWT_REFRESH_SECRET=change-this-too
```

### Testing Your Setup

1. **Start everything**
   ```bash
   docker-compose up -d
   ```

2. **Check the logs**
   ```bash
   docker-compose logs -f
   ```
   Look for connection errors or startup issues

3. **Try the chat interface**
   - Go to http://localhost:3080
   - Create an account (or login if you've set up auth)
   - Ask: "What data is available in our Splunk environment?"

## Common Issues We've Encountered

### "Can't connect to Splunk"
- Check your URL (http vs https, port number)
- Verify credentials work with curl first
- Some corporate networks block external connections

### "Tools not working"
- The pack expects certain Splunk REST endpoints
- Some older Splunk versions might not have everything
- We're still testing compatibility

### "Chat interface won't load"
- Check if port 3080 is available
- Look at docker-compose logs for errors
- Sometimes it takes a minute to fully start

### "AI responses are weird"
- Different AI models behave differently
- Claude seems to work best so far
- We're still learning the optimal prompting

## What We're Still Working On

- Better error messages when things go wrong
- Automatic detection of Splunk capabilities
- Easier first-time setup process
- More flexible authentication options

Found something else that doesn't work? Please [let us know](https://github.com/your-org/splunk-community-mcp/issues) - we want to make this easier for everyone.