#!/usr/bin/env python3
"""
Generate LibreChat Configuration from Simplified Chat Config

This script transforms the domain-specific chat.yml configuration into
LibreChat's complex librechat.yaml format and docker-compose.chat.yml.

Usage:
    python scripts/generate-librechat-config.py
"""

import yaml
import os
import sys
from pathlib import Path

def load_chat_config():
    """Load the simplified chat.yml configuration."""
    chat_config_path = Path("chat.yml")
    if not chat_config_path.exists():
        print("Error: chat.yml not found in current directory")
        sys.exit(1)
    
    with open(chat_config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def generate_librechat_yaml(config):
    """Generate librechat.yaml from chat config."""
    
    # Build endpoints configuration
    endpoints = {}
    
    # Add Google endpoint if configured
    if 'google' in config['models'].get('providers', []):
        endpoints['google'] = {
            'models': {
                'default': config['models']['google']['available'],
                'fetch': False
            }
        }
    
    # Add Anthropic endpoint if configured
    if 'anthropic' in config['models'].get('providers', []):
        endpoints['anthropic'] = {
            'titleConvo': True,
            'titleModel': config['models']['anthropic']['title_model']
        }
    
    # Build MCP servers configuration
    mcp_servers = {}
    if config['mcp']['enabled']:
        for server_key, server_config in config['mcp']['servers'].items():
            mcp_servers[server_key] = {
                'type': server_config['type'],
                'url': server_config['url'],
                'headers': {
                    'X-User-ID': '{{LIBRECHAT_USER_ID}}',
                    'X-User-Email': '{{LIBRECHAT_USER_EMAIL}}'
                }
            }
    
    # Build file configuration
    file_config = {
        'enabled': True,
        'endpoints': {
            'google': {
                'fileLimit': 5,
                'fileSizeLimit': 10,
                'totalSizeLimit': 50,
                'supportedMimeTypes': [
                    'image/*',
                    'application/pdf', 
                    'text/*'
                ]
            },
            'default': {
                'totalSizeLimit': 20
            }
        },
        'serverFileSizeLimit': 100,
        'avatarSizeLimit': 2
    }
    
    # Build interface configuration
    interface = {
        'endpointsMenu': False,
        'privacyPolicy': {
            'externalUrl': '',
            'openNewTab': True
        }
    }
    
    # Build complete LibreChat configuration
    librechat_config = {
        'version': '1.2.8',
        'cache': True,
        'endpoints': endpoints,
        'mcpServers': mcp_servers,
        'fileConfig': file_config,
        'interface': interface
    }
    
    return librechat_config

def generate_docker_compose_chat(config):
    """Generate docker-compose.chat.yml from chat config."""
    
    # Build environment variables for LibreChat
    environment = [
        'HOST=0.0.0.0',
        'NODE_ENV=production',
        'MONGO_URI=mongodb://mongodb:27017/LibreChat'
    ]
    
    # Add API keys for each provider
    if 'google' in config['models'].get('providers', []):
        environment.extend([
            # GOOGLE_KEY will be read from .env file via env_file directive
            f'GOOGLE_MODELS={",".join(config["models"]["google"]["available"])}'
        ])
    
    if 'anthropic' in config['models'].get('providers', []):
        environment.extend([
            # ANTHROPIC_API_KEY will be read from .env file via env_file directive
            f'ANTHROPIC_MODELS={",".join(config["models"]["anthropic"]["available"])}'
        ])
    
    # Add RAG configuration
    if config['rag']['enabled']:
        environment.extend([
            'RAG_API_URL=http://rag-api:8001',
            f'EMBEDDINGS_PROVIDER={config["rag"]["embeddings"]["provider"]}',
            f'EMBEDDINGS_MODEL={config["rag"]["embeddings"]["model"]}',
            'RAG_USE_FULL_CONTEXT=false',
            f'CHUNK_SIZE={config["rag"]["settings"]["chunk_size"]}',
            f'CHUNK_OVERLAP={config["rag"]["settings"]["chunk_overlap"]}'
        ])
    
    # Build endpoints list dynamically
    endpoints_list = config['models'].get('providers', []).copy()
    endpoints_list.extend(['agents', 'assistants'])
    
    # Add other required environment variables
    environment.extend([
        # OPENAI_API_KEY will be read from .env file via env_file directive
        f'ENDPOINTS={",".join(endpoints_list)}',
        'JWT_SECRET=${JWT_SECRET:-your-secret-key-change-in-production}',
        'JWT_REFRESH_SECRET=${JWT_REFRESH_SECRET:-your-refresh-secret-change-in-production}',
        f'ALLOW_REGISTRATION={str(config["security"]["allow_registration"]).lower()}'
    ])
    
    # Build volumes
    volumes = [
        './librechat.yaml:/app/librechat.yaml:ro',
        'librechat-uploads:/app/client/public/images'
    ]
    
    # Build depends_on - remove MCP dependency for standalone chat
    depends_on = ['mongodb', 'rag-api'] if config['rag']['enabled'] else ['mongodb']
    
    # Build complete docker-compose configuration
    docker_config = {
        'version': '3.8',
        'services': {
            'librechat': {
                'image': 'ghcr.io/danny-avila/librechat:latest',
                'container_name': 'librechat-splunk',
                'restart': 'unless-stopped',
                'ports': ['3080:3080'],
                'environment': environment,
                'env_file': ['.env'],  # Explicitly use .env file
                'volumes': volumes,
                'networks': [config['docker']['network']],
                'depends_on': depends_on
            }
        }
    }
    
    # Add RAG API service if enabled
    if config['rag']['enabled']:
        docker_config['services']['rag-api'] = {
            'image': 'ghcr.io/danny-avila/librechat-rag-api-dev-lite:latest',
            'container_name': 'librechat-rag',
            'restart': 'unless-stopped',
            'ports': [f'{config["docker"]["rag_port"]}:8001'],
            'environment': [
                # OPENAI_API_KEY will be read from .env file via env_file directive
            ],
            'env_file': ['.env'],  # Explicitly use .env file
            'volumes': ['rag_data:/app/data'],
            'networks': [config['docker']['network']]
        }
    
    # Add MongoDB service
    docker_config['services']['mongodb'] = {
        'image': 'mongo:latest',
        'container_name': 'librechat-mongodb',
        'restart': 'unless-stopped',
        'volumes': ['mongodb_data:/data/db'],
        'networks': [config['docker']['network']]
    }
    
    # Add volumes section
    docker_config['volumes'] = {
        'librechat-uploads': None,
        'mongodb_data': None,
        'rag_data': None
    }
    
    # Add networks section
    docker_config['networks'] = {
        config['docker']['network']: {
            'driver': 'bridge',
            'name': config['docker']['network']
        }
    }
    
    return docker_config

def write_config_file(filename, config, description):
    """Write configuration to file with error handling."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2, sort_keys=False)
        print(f"Generated {filename} - {description}")
    except Exception as e:
        print(f"Error writing {filename}: {e}")
        return False
    return True

def main():
    """Main script execution."""
    print("Generating LibreChat configuration from chat.yml...")
    
    # Load chat configuration
    try:
        chat_config = load_chat_config()
        print(f"Loaded chat configuration: {chat_config['app']['name']}")
    except Exception as e:
        print(f"Error loading chat.yml: {e}")
        sys.exit(1)
    
    # Generate LibreChat configuration
    try:
        librechat_config = generate_librechat_yaml(chat_config)
        success = write_config_file(
            'librechat.yaml', 
            librechat_config, 
            f"LibreChat configuration with {len(librechat_config.get('mcpServers', {}))} MCP servers"
        )
        if not success:
            sys.exit(1)
    except Exception as e:
        print(f"Error generating librechat.yaml: {e}")
        sys.exit(1)
    
    # Generate Docker Compose configuration
    try:
        docker_config = generate_docker_compose_chat(chat_config)
        success = write_config_file(
            'docker-compose.chat.yml', 
            docker_config,
            f"Docker Compose with {len(docker_config['services'])} services"
        )
        if not success:
            sys.exit(1)
    except Exception as e:
        print(f"Error generating docker-compose.chat.yml: {e}")
        sys.exit(1)
    
    print("\nConfiguration generation complete!")
    print("\nNext steps:")
    print("1. Review generated files: librechat.yaml, docker-compose.chat.yml")
    print("2. Set required API keys in .env file")
    print("3. Start chat interface: docker-compose -f docker-compose.chat.yml up -d")
    print("4. Access at: http://localhost:3080")

if __name__ == "__main__":
    main()