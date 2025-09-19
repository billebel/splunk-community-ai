# Quick start script for Catalyst MCP Gateway (Windows)
# Starts the gateway and connects common AI clients

param(
    [string]$ServerName = "splunk-catalyst",
    [switch]$SkipClient
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

Write-ColorOutput "🚀 Starting Catalyst MCP Gateway" $Colors.Blue
Write-ColorOutput "==================================" $Colors.Blue

# Check if MCP server is registered
try {
    $servers = docker mcp server list 2>$null
    if (-not ($servers -match $ServerName)) {
        Write-ColorOutput "❌ MCP server '$ServerName' not found." $Colors.Red
        Write-ColorOutput "Run setup-mcp-gateway.ps1 first!" $Colors.Yellow
        exit 1
    }
}
catch {
    Write-ColorOutput "❌ Failed to check MCP servers: $_" $Colors.Red
    exit 1
}

# Check if server is enabled
try {
    $serverInfo = docker mcp server list | Select-String $ServerName
    if (-not ($serverInfo -match "enabled")) {
        Write-ColorOutput "⚠️  Enabling MCP server..." $Colors.Yellow
        docker mcp server enable $ServerName
    }
}
catch {
    Write-ColorOutput "❌ Failed to enable server: $_" $Colors.Red
    exit 1
}

Write-ColorOutput "✅ MCP server ready" $Colors.Green

# Function to start gateway
function Start-Gateway {
    Write-ColorOutput "🔄 Starting MCP Gateway..." $Colors.Blue

    # Check if gateway is already running
    try {
        docker mcp gateway status | Out-Null
        Write-ColorOutput "⚠️  Gateway already running. Stopping first..." $Colors.Yellow
        docker mcp gateway stop 2>$null
        Start-Sleep -Seconds 2
    }
    catch {
        # Gateway not running, which is fine
    }

    # Start gateway in background
    try {
        $job = Start-Job -ScriptBlock { docker mcp gateway run }

        # Wait for gateway to be ready
        Write-ColorOutput "⏳ Waiting for gateway to be ready..." $Colors.Blue
        for ($i = 1; $i -le 30; $i++) {
            try {
                docker mcp gateway status | Out-Null
                Write-ColorOutput "✅ Gateway is running" $Colors.Green
                return $job
            }
            catch {
                Start-Sleep -Seconds 1
                Write-Host "." -NoNewline
            }
        }

        Write-ColorOutput "❌ Gateway failed to start" $Colors.Red
        Stop-Job $job -Force
        exit 1
    }
    catch {
        Write-ColorOutput "❌ Failed to start gateway: $_" $Colors.Red
        exit 1
    }
}

# Function to connect AI clients
function Connect-Clients {
    if ($SkipClient) {
        Write-ColorOutput "⏭️  Skipping client connection" $Colors.Yellow
        return
    }

    Write-ColorOutput "🔗 Available AI client connections:" $Colors.Blue
    Write-Host "1. Claude (Anthropic)"
    Write-Host "2. VS Code"
    Write-Host "3. Custom client"
    Write-Host "4. Skip client connection"
    Write-Host ""

    $choice = Read-Host "Select client to connect (1-4)"

    switch ($choice) {
        "1" {
            Write-ColorOutput "🔗 Connecting Claude..." $Colors.Blue
            try {
                docker mcp client connect claude
                Write-ColorOutput "✅ Claude connected to MCP Gateway" $Colors.Green
            }
            catch {
                Write-ColorOutput "❌ Failed to connect Claude: $_" $Colors.Red
            }
        }
        "2" {
            Write-ColorOutput "🔗 Connecting VS Code..." $Colors.Blue
            try {
                docker mcp client connect vscode
                Write-ColorOutput "✅ VS Code connected to MCP Gateway" $Colors.Green
            }
            catch {
                Write-ColorOutput "❌ Failed to connect VS Code: $_" $Colors.Red
            }
        }
        "3" {
            Write-ColorOutput "📋 Custom client connection info:" $Colors.Blue
            Write-Host "Gateway URL: http://localhost:8080"
            Write-Host "Server: $ServerName"
            Write-Host "Use this information to configure your MCP client"
        }
        "4" {
            Write-ColorOutput "⏭️  Skipping client connection" $Colors.Yellow
        }
        default {
            Write-ColorOutput "⏭️  Invalid choice, skipping client connection" $Colors.Yellow
        }
    }
}

# Function to show gateway info
function Show-Info {
    Write-Host ""
    Write-ColorOutput "🎉 Catalyst MCP Gateway is running!" $Colors.Green
    Write-ColorOutput "====================================" $Colors.Green
    Write-Host ""

    Write-ColorOutput "Gateway Status:" $Colors.Blue
    try {
        docker mcp gateway status
    }
    catch {
        Write-Host "Status check failed"
    }

    Write-Host ""
    Write-ColorOutput "Available Servers:" $Colors.Blue
    try {
        docker mcp server list
    }
    catch {
        Write-Host "Failed to list servers"
    }

    Write-Host ""
    Write-ColorOutput "Useful Commands:" $Colors.Blue
    Write-ColorOutput "  View server logs:     " $Colors.White -NoNewline
    Write-ColorOutput "docker mcp server logs $ServerName" $Colors.Yellow
    Write-ColorOutput "  Stop gateway:         " $Colors.White -NoNewline
    Write-ColorOutput "docker mcp gateway stop" $Colors.Yellow
    Write-ColorOutput "  Gateway status:       " $Colors.White -NoNewline
    Write-ColorOutput "docker mcp gateway status" $Colors.Yellow
    Write-ColorOutput "  Server management:    " $Colors.White -NoNewline
    Write-ColorOutput "docker mcp server --help" $Colors.Yellow

    Write-Host ""
    Write-ColorOutput "Knowledge Packs Available:" $Colors.Blue
    Write-Host "- splunk_enterprise: Core Splunk Enterprise tools"
    Write-Host "- splunk_cloud: Splunk Cloud Platform tools"
    Write-Host "- splunk_oauth: OAuth authentication flow"
    Write-Host "- splunk_saml: SAML/SSO authentication flow"

    Write-Host ""
    Write-ColorOutput "Development Mode:" $Colors.Blue
    Write-ColorOutput "  For development with hot reload: " $Colors.White -NoNewline
    Write-ColorOutput "docker-compose -f docker-compose.mcp-gateway.yml up" $Colors.Yellow
}

# Main execution
try {
    $gatewayJob = Start-Gateway
    Connect-Clients
    Show-Info

    # Keep script running
    Write-Host ""
    Write-ColorOutput "📋 Press Ctrl+C to stop the gateway" $Colors.Blue
    Write-ColorOutput "📋 Gateway is running in the background..." $Colors.Blue
    Write-ColorOutput "=========================================" $Colors.Blue

    # Cleanup function
    $cleanup = {
        Write-Host ""
        Write-ColorOutput "🛑 Stopping MCP Gateway..." $Colors.Yellow
        try {
            docker mcp gateway stop 2>$null
            Write-ColorOutput "✅ Gateway stopped" $Colors.Green
        }
        catch {
            Write-ColorOutput "⚠️  Gateway may still be running" $Colors.Yellow
        }

        if ($gatewayJob) {
            Stop-Job $gatewayJob -Force 2>$null
            Remove-Job $gatewayJob -Force 2>$null
        }
    }

    # Register cleanup for Ctrl+C
    Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action $cleanup

    # Wait for user to stop
    try {
        do {
            Start-Sleep -Seconds 1
        } while ($gatewayJob.State -eq "Running")
    }
    finally {
        & $cleanup
    }
}
catch {
    Write-ColorOutput "❌ Error during execution: $_" $Colors.Red
    exit 1
}