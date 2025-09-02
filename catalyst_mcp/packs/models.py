"""Data models for universal knowledge packs."""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union
from enum import Enum
import yaml


class PackValidationError(Exception):
    """Raised when a pack fails validation."""
    pass


class ToolType(Enum):
    """Tool operation types."""
    LIST = "list"
    DETAILS = "details"
    SEARCH = "search"
    EXECUTE = "execute"
    QUERY = "query"        # Database queries
    COMMAND = "command"    # Shell/SSH commands
    STREAM = "stream"      # Real-time data streams
    BATCH = "batch"        # Batch operations
    TRANSACTION = "transaction"  # Multi-step transactions


class AuthMethod(Enum):
    """Supported authentication methods."""
    BASIC = "basic"
    BEARER = "bearer"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    AWS_IAM = "aws_iam"
    SSH_KEY = "ssh_key"      # SSH key authentication
    CERT = "certificate"     # Certificate-based auth
    KERBEROS = "kerberos"    # Kerberos authentication
    CUSTOM = "custom"


class TransformEngine(Enum):
    """Supported response transformation engines."""
    JQ = "jq"
    JAVASCRIPT = "javascript"
    PYTHON = "python"
    TEMPLATE = "template"


@dataclass
class PackMetadata:
    """Knowledge pack metadata."""
    name: str
    version: str
    description: str
    vendor: str
    license: str
    compatibility: str
    domain: str
    tags: List[str] = field(default_factory=list)
    pricing_tier: str = "free"
    required_capabilities: List[str] = field(default_factory=list)


@dataclass
class AuthConfig:
    """Authentication configuration."""
    method: AuthMethod
    config: Dict[str, str] = field(default_factory=dict)


@dataclass
class RetryPolicy:
    """API retry configuration."""
    max_retries: int = 3
    backoff: str = "exponential"
    backoff_factor: float = 1.0


@dataclass
class ConnectionConfig:
    """Universal connection configuration for all integration types."""
    type: str  # "rest", "database", "message_queue", "filesystem", "ssh", "grpc", "websocket"
    
    # Common fields
    timeout: int = 30
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    auth: AuthConfig = None
    
    # REST API specific
    base_url: Optional[str] = None
    verify_ssl: Union[bool, str] = True
    
    # Database specific  
    engine: Optional[str] = None  # postgresql, mysql, mongodb, redis, etc.
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    schema: Optional[str] = None
    pool_size: int = 5
    
    # Message Queue specific
    exchange: Optional[str] = None
    routing_key: Optional[str] = None
    queue_name: Optional[str] = None
    
    # File System specific
    root_path: Optional[str] = None
    bucket: Optional[str] = None  # For S3-like systems
    
    # SSH specific
    hostname: Optional[str] = None
    username: Optional[str] = None
    key_file: Optional[str] = None
    
    # Additional connection parameters
    extra_config: Dict[str, Any] = field(default_factory=dict)


@dataclass  
class ParameterDefinition:
    """Tool parameter definition."""
    name: str
    type: str
    required: bool = False
    default: Any = None
    description: str = ""
    enum: List[str] = field(default_factory=list)
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None


@dataclass
class TransformConfig:
    """Enhanced response transformation configuration."""
    type: TransformEngine
    
    # Inline transform content
    expression: Optional[str] = None
    code: Optional[str] = None
    template: Optional[str] = None
    
    # External file references
    file: Optional[str] = None
    function: Optional[str] = None
    
    # Execution options
    timeout: int = 30
    sandbox: bool = True
    
    
@dataclass
class ExecutionStep:
    """Multi-step execution configuration."""
    name: str
    method: str
    endpoint: str
    query_params: Dict[str, str] = field(default_factory=dict)
    form_data: Dict[str, str] = field(default_factory=dict)
    response_key: Optional[str] = None


@dataclass
class ToolDefinition:
    """Universal tool definition from YAML."""
    name: str
    type: ToolType
    description: str
    parameters: List[ParameterDefinition] = field(default_factory=list)
    transform: Optional[TransformConfig] = None
    execution_steps: List[ExecutionStep] = field(default_factory=list)
    
    # REST API specific
    endpoint: Optional[str] = None
    method: str = "GET"
    query_params: Dict[str, str] = field(default_factory=dict)
    form_data: Dict[str, str] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    
    # Database specific
    sql: Optional[str] = None
    table: Optional[str] = None
    collection: Optional[str] = None  # For NoSQL
    
    # Message Queue specific
    queue: Optional[str] = None
    exchange_name: Optional[str] = None
    message_type: Optional[str] = None
    
    # File System specific
    path: Optional[str] = None
    operation: Optional[str] = None  # read, write, list, delete, etc.
    
    # SSH/Shell specific
    command: Optional[str] = None
    shell: Optional[str] = None
    working_directory: Optional[str] = None
    
    # Additional tool-specific configuration
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PromptDefinition:
    """Prompt template definition."""
    name: str
    description: str
    template: str
    suggested_tools: List[str] = field(default_factory=list)
    arguments: List[ParameterDefinition] = field(default_factory=list)


@dataclass
class ResourceDefinition:
    """Resource definition for documentation/help."""
    name: str
    type: str
    url: str
    description: str


@dataclass
class Pack:
    """Complete knowledge pack definition."""
    metadata: PackMetadata
    connection: ConnectionConfig
    tools: Dict[str, ToolDefinition] = field(default_factory=dict)
    prompts: Dict[str, PromptDefinition] = field(default_factory=dict)
    resources: Dict[str, ResourceDefinition] = field(default_factory=dict)
    error_mapping: Dict[str, str] = field(default_factory=dict)
    
    @classmethod
    def from_yaml_file(cls, yaml_path: str) -> 'Pack':
        """Load pack from YAML file."""
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Pack':
        """Create pack from dictionary data."""
        # Parse metadata
        metadata_dict = data.get('metadata', {})
        metadata = PackMetadata(
            name=metadata_dict['name'],
            version=metadata_dict['version'],
            description=metadata_dict['description'],
            vendor=metadata_dict['vendor'],
            license=metadata_dict['license'],
            compatibility=metadata_dict['compatibility'],
            domain=metadata_dict['domain'],
            tags=metadata_dict.get('tags', []),
            pricing_tier=metadata_dict.get('pricing_tier', 'free'),
            required_capabilities=metadata_dict.get('required_capabilities', [])
        )
        
        # Parse connection config
        conn_dict = data.get('connection', {})
        retry_dict = conn_dict.get('retry_policy', {})
        retry_policy = RetryPolicy(
            max_retries=retry_dict.get('max_retries', 3),
            backoff=retry_dict.get('backoff', 'exponential'),
            backoff_factor=retry_dict.get('backoff_factor', 1.0)
        )
        
        auth_dict = conn_dict.get('auth', {})
        auth_config = AuthConfig(
            method=AuthMethod(auth_dict['method']),
            config=auth_dict.get('config', {})
        ) if auth_dict else None
        
        connection = ConnectionConfig(
            type=conn_dict['type'],
            base_url=conn_dict['base_url'],
            timeout=conn_dict.get('timeout', 30),
            verify_ssl=conn_dict.get('verify_ssl', True),
            retry_policy=retry_policy,
            auth=auth_config
        )
        
        # Parse tools
        tools = {}
        for tool_name, tool_dict in data.get('tools', {}).items():
            # Parse parameters
            parameters = []
            for param_dict in tool_dict.get('parameters', []):
                param = ParameterDefinition(
                    name=param_dict['name'],
                    type=param_dict['type'],
                    required=param_dict.get('required', False),
                    default=param_dict.get('default'),
                    description=param_dict.get('description', ''),
                    enum=param_dict.get('enum', []),
                    min_value=param_dict.get('min_value'),
                    max_value=param_dict.get('max_value')
                )
                parameters.append(param)
            
            # Parse transform config
            transform = None
            if 'transform' in tool_dict:
                transform_dict = tool_dict['transform']
                transform = TransformConfig(
                    type=TransformEngine(transform_dict['type']),
                    expression=transform_dict.get('expression'),
                    code=transform_dict.get('code'),
                    template=transform_dict.get('template'),
                    file=transform_dict.get('file'),
                    function=transform_dict.get('function'),
                    timeout=transform_dict.get('timeout', 30),
                    sandbox=transform_dict.get('sandbox', True)
                )
            
            # Parse execution steps
            execution_steps = []
            for step_dict in tool_dict.get('execution_steps', []):
                step = ExecutionStep(
                    name=step_dict['name'],
                    method=step_dict['method'],
                    endpoint=step_dict['endpoint'],
                    query_params=step_dict.get('query_params', {}),
                    form_data=step_dict.get('form_data', {}),
                    response_key=step_dict.get('response_key')
                )
                execution_steps.append(step)
            
            tool = ToolDefinition(
                name=tool_name,
                type=ToolType(tool_dict['type']),
                description=tool_dict['description'],
                endpoint=tool_dict['endpoint'],
                method=tool_dict.get('method', 'GET'),
                parameters=parameters,
                query_params=tool_dict.get('query_params', {}),
                form_data=tool_dict.get('form_data', {}),
                headers=tool_dict.get('headers', {}),
                transform=transform,
                execution_steps=execution_steps
            )
            tools[tool_name] = tool
        
        # Parse prompts (simplified for now)
        prompts = {}
        for prompt_name, prompt_dict in data.get('prompts', {}).items():
            prompt = PromptDefinition(
                name=prompt_name,
                description=prompt_dict['description'],
                template=prompt_dict['template'],
                suggested_tools=prompt_dict.get('suggested_tools', [])
            )
            prompts[prompt_name] = prompt
        
        # Parse resources (simplified for now) 
        resources = {}
        for resource_name, resource_dict in data.get('resources', {}).items():
            resource = ResourceDefinition(
                name=resource_name,
                type=resource_dict['type'],
                url=resource_dict['url'],
                description=resource_dict['description']
            )
            resources[resource_name] = resource
        
        return cls(
            metadata=metadata,
            connection=connection,
            tools=tools,
            prompts=prompts,
            resources=resources,
            error_mapping=data.get('error_mapping', {})
        )