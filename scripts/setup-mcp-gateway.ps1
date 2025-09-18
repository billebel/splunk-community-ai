# Catalyst MCP Gateway Setup Script for Windows
# Sets up Docker MCP Gateway with Splunk Community AI integration

param(
    [switch]$SkipPrereqs,
    [string]$ServerName = "splunk-catalyst",
    [string]$ImageName = "splunk-community-ai/catalyst-mcp"
)

# Colors for output
$Colors = @{
    Red = [ConsoleColor]::Red
    Green = [ConsoleColor]::Green
    Yellow = [ConsoleColor]::Yellow
    Blue = [ConsoleColor]::Blue
    White = [ConsoleColor]::White
}

function Write-ColorOutput {
    param([string]$Message, [ConsoleColor]$Color = [ConsoleColor]::White)
    Write-Host $Message -ForegroundColor $Color
}

function Test-CommandExists {
    param([string]$Command)
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

Write-ColorOutput "🚀 Setting up Catalyst MCP Gateway for Splunk Community AI" $Colors.Blue
Write-ColorOutput "===========================================================" $Colors.Blue

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

# Check prerequisites
if (-not $SkipPrereqs) {
    Write-ColorOutput "📋 Checking prerequisites..." $Colors.Blue

    if (-not (Test-CommandExists "docker")) {
        Write-ColorOutput "❌ Docker is not installed. Please install Docker Desktop." $Colors.Red
        exit 1
    }

    if (-not (Test-CommandExists "docker-compose")) {
        Write-ColorOutput "❌ Docker Compose is not installed." $Colors.Red
        exit 1
    }

    # Check if Docker MCP plugin is available
    try {
        docker mcp --help | Out-Null
    }
    catch {
        Write-ColorOutput "⚠️  Docker MCP plugin not found." $Colors.Yellow
        Write-ColorOutput "Please follow these steps:" $Colors.Yellow
        Write-ColorOutput "1. Enable Docker Desktop MCP Toolkit feature" $Colors.White
        Write-ColorOutput "2. Download MCP Gateway CLI from GitHub releases" $Colors.White
        Write-ColorOutput "3. Place binary in %USERPROFILE%\.docker\cli-plugins\" $Colors.White
        Write-ColorOutput "" $Colors.White
        Write-ColorOutput "For more info: https://docs.docker.com/ai/mcp-gateway/" $Colors.White
        Read-Host "Press Enter when MCP plugin is installed"
    }

    Write-ColorOutput "✅ Prerequisites check completed" $Colors.Green
}

# Build the MCP server image
Write-ColorOutput "🏗️  Building Catalyst MCP server image..." $Colors.Blue
Set-Location $ProjectRoot

try {
    docker build -f docker/Dockerfile.mcp-gateway -t "${ImageName}:latest" .
    Write-ColorOutput "✅ Docker image built successfully" $Colors.Green
}
catch {
    Write-ColorOutput "❌ Failed to build Docker image: $_" $Colors.Red
    exit 1
}

# Check if server already exists and remove it
try {
    $existingServers = docker mcp server list 2>$null
    if ($existingServers -match $ServerName) {
        Write-ColorOutput "⚠️  Existing MCP server found. Removing..." $Colors.Yellow
        docker mcp server remove $ServerName 2>$null
    }
}
catch {
    # Ignore errors when checking/removing existing servers
}

# Register the MCP server with Docker Gateway
Write-ColorOutput "📝 Registering MCP server with Docker Gateway..." $Colors.Blue

try {
    docker mcp server add $ServerName `
        --image "${ImageName}:latest" `
        --name "Splunk Catalyst MCP Server" `
        --description "Catalyst MCP server for Splunk integration with knowledge packs" `
        --local true

    Write-ColorOutput "✅ MCP server registered successfully" $Colors.Green
}
catch {
    Write-ColorOutput "❌ Failed to register MCP server: $_" $Colors.Red
    exit 1
}

# Set up environment variables
Write-ColorOutput "⚙️  Setting up environment configuration..." $Colors.Blue

$envFile = Join-Path $ProjectRoot ".env"
$envExampleFile = Join-Path $ProjectRoot ".env.example"

if (-not (Test-Path $envFile)) {
    if (Test-Path $envExampleFile) {
        Write-ColorOutput "⚠️  .env file not found. Creating from template..." $Colors.Yellow
        Copy-Item $envExampleFile $envFile
        Write-ColorOutput "📝 Please edit .env file with your Splunk configuration" $Colors.Yellow
    }
    else {
        Write-ColorOutput "❌ .env.example file not found!" $Colors.Red
    }
}

# Enable the server
Write-ColorOutput "🔄 Enabling MCP server..." $Colors.Blue
try {
    docker mcp server enable $ServerName
    Write-ColorOutput "✅ MCP server enabled" $Colors.Green
}
catch {
    Write-ColorOutput "❌ Failed to enable MCP server: $_" $Colors.Red
    exit 1
}

# Setup completion
Write-ColorOutput "" $Colors.White
Write-ColorOutput "🎉 Catalyst MCP Gateway setup completed!" $Colors.Green
Write-ColorOutput "===========================================================" $Colors.Green
Write-ColorOutput "" $Colors.White
Write-ColorOutput "Next steps:" $Colors.Blue
Write-ColorOutput "1. Edit .env file with your Splunk configuration:" $Colors.White
Write-ColorOutput "   - SPLUNK_HOST=your-splunk-host" $Colors.White
Write-ColorOutput "   - SPLUNK_TOKEN=your-splunk-token" $Colors.White
Write-ColorOutput "" $Colors.White
Write-ColorOutput "2. Start the MCP Gateway:" $Colors.White
Write-ColorOutput "   docker mcp gateway run" $Colors.Yellow
Write-ColorOutput "" $Colors.White
Write-ColorOutput "3. Connect your AI client (Claude, VS Code, etc.):" $Colors.White
Write-ColorOutput "   docker mcp client connect claude" $Colors.Yellow
Write-ColorOutput "" $Colors.White
Write-ColorOutput "4. Alternative: Use Docker Compose for development:" $Colors.White
Write-ColorOutput "   docker-compose -f docker-compose.mcp-gateway.yml up" $Colors.Yellow
Write-ColorOutput "" $Colors.White
Write-ColorOutput "Available MCP tools:" $Colors.Blue
Write-ColorOutput "- splunk_search: Execute Splunk searches" $Colors.White
Write-ColorOutput "- splunk_analysis: Analyze Splunk data" $Colors.White
Write-ColorOutput "- knowledge_packs: Dynamic pack loading" $Colors.White
Write-ColorOutput "- oauth_authentication: OAuth/SAML flows" $Colors.White
Write-ColorOutput "" $Colors.White
Write-ColorOutput "For troubleshooting:" $Colors.Blue
Write-ColorOutput "   docker mcp server logs $ServerName" $Colors.Yellow
Write-ColorOutput "   docker mcp gateway status" $Colors.Yellow