"""
Multi-language transform engine for knowledge packs.
Supports JavaScript, Python, jq, and template transforms.
"""

import os
import re
import json
import logging
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class TransformType(Enum):
    """Supported transform engine types."""
    JAVASCRIPT = "javascript"
    PYTHON = "python"
    JQ = "jq"
    TEMPLATE = "template"


@dataclass
class TransformConfig:
    """Enhanced transform configuration supporting multiple engines."""
    type: TransformType
    
    # Inline transform content
    code: Optional[str] = None
    expression: Optional[str] = None
    template: Optional[str] = None
    
    # External file references
    file: Optional[str] = None
    function: Optional[str] = None
    
    # Execution options
    timeout: int = 30
    sandbox: bool = True


class TransformEngine:
    """Multi-language transform engine."""
    
    def __init__(self, pack_root_path: str):
        """Initialize transform engine for a specific pack.
        
        Args:
            pack_root_path: Root directory of the knowledge pack
        """
        self.pack_root = Path(pack_root_path)
        self.transforms_dir = self.pack_root / "transforms"
        
        # Check available engines
        self._javascript_available = self._check_nodejs_available()
        self._jq_available = self._check_jq_available()
        
        logger.info(f"Transform engine initialized for {pack_root_path}")
        logger.info(f"Available engines: Python=True, JavaScript={self._javascript_available}, jq={self._jq_available}")
    
    def transform(self, data: Dict[str, Any], config: TransformConfig, variables: Dict[str, Any] = None) -> Any:
        """Execute transform using the specified engine.
        
        Args:
            data: Raw data to transform
            config: Transform configuration
            variables: Variables from tool execution context
            
        Returns:
            Transformed data
        """
        variables = variables or {}
        
        try:
            # Handle both enum and string values
            transform_type = config.type
            if hasattr(transform_type, 'value'):
                transform_type = transform_type.value
            
            if transform_type == "python":
                return self._transform_python(data, config, variables)
            elif transform_type == "javascript":
                return self._transform_javascript(data, config, variables)
            elif transform_type == "jq":
                return self._transform_jq(data, config, variables)
            elif transform_type == "template":
                return self._transform_template(data, config, variables)
            else:
                logger.error(f"Unsupported transform type: {config.type}")
                return data
                
        except Exception as e:
            logger.error(f"Transform failed ({config.type.value}): {e}")
            return {
                "error": f"Transform failed: {str(e)}",
                "original_data": data
            }
    
    def _transform_python(self, data: Dict[str, Any], config: TransformConfig, variables: Dict[str, Any]) -> Any:
        """Execute Python transform."""
        if config.file:
            return self._execute_python_file(data, config, variables)
        elif config.code:
            return self._execute_python_inline(data, config, variables)
        else:
            logger.error("Python transform requires either 'file' or 'code'")
            return data
    
    def _execute_python_file(self, data: Dict[str, Any], config: TransformConfig, variables: Dict[str, Any]) -> Any:
        """Execute Python transform from external file."""
        transform_file = self.transforms_dir / config.file
        
        if not transform_file.exists():
            logger.error(f"Transform file not found: {transform_file}")
            return data
        
        try:
            # Import the transform module dynamically
            import importlib.util
            spec = importlib.util.spec_from_file_location("transform_module", transform_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Get the specified function
            if config.function and hasattr(module, config.function):
                transform_func = getattr(module, config.function)
                return transform_func(data, variables)
            else:
                # Look for default function names
                for default_name in ['transform', 'main', 'process']:
                    if hasattr(module, default_name):
                        transform_func = getattr(module, default_name)
                        return transform_func(data, variables)
                
                logger.error(f"No suitable transform function found in {transform_file}")
                return data
                
        except Exception as e:
            logger.error(f"Python transform execution failed: {e}")
            return data
    
    def _execute_python_inline(self, data: Dict[str, Any], config: TransformConfig, variables: Dict[str, Any]) -> Any:
        """Execute inline Python transform code."""
        try:
            # Create a safe execution environment
            exec_globals = {
                '__builtins__': {
                    'len': len, 'str': str, 'int': int, 'float': float, 'bool': bool,
                    'list': list, 'dict': dict, 'tuple': tuple, 'set': set,
                    'min': min, 'max': max, 'sum': sum, 'sorted': sorted,
                    'enumerate': enumerate, 'zip': zip, 'map': map, 'filter': filter,
                    'json': json, 're': re
                },
                'data': data,
                'variables': variables,
                'result': None
            }
            
            # Execute the code
            exec(config.code, exec_globals)
            
            # Look for result or call transform function
            if 'result' in exec_globals and exec_globals['result'] is not None:
                return exec_globals['result']
            elif 'transform' in exec_globals:
                return exec_globals['transform'](data, variables)
            else:
                logger.warning("Python inline transform produced no result")
                return data
                
        except Exception as e:
            logger.error(f"Python inline transform failed: {e}")
            return data
    
    def _transform_javascript(self, data: Dict[str, Any], config: TransformConfig, variables: Dict[str, Any]) -> Any:
        """Execute JavaScript transform."""
        if not self._javascript_available:
            logger.error("JavaScript transforms require Node.js - falling back to original data")
            return data
        
        try:
            if config.file:
                return self._execute_javascript_file(data, config, variables)
            elif config.code:
                return self._execute_javascript_inline(data, config, variables)
            else:
                logger.error("JavaScript transform requires either 'file' or 'code'")
                return data
                
        except Exception as e:
            logger.error(f"JavaScript transform failed: {e}")
            return data
    
    def _execute_javascript_file(self, data: Dict[str, Any], config: TransformConfig, variables: Dict[str, Any]) -> Any:
        """Execute JavaScript transform from external file."""
        transform_file = self.transforms_dir / config.file
        
        if not transform_file.exists():
            logger.error(f"JavaScript transform file not found: {transform_file}")
            return data
        
        # Create a wrapper script that loads the transform and executes it
        # Fix Windows path handling for Node.js
        transform_path = str(transform_file.absolute()).replace('\\', '\\\\')
        
        wrapper_script = f"""
        const fs = require('fs');
        const path = require('path');
        
        // Load the transform module
        const transformModule = require('{transform_path}');
        
        // Parse input data
        const inputData = JSON.parse(process.argv[2]);
        const variables = JSON.parse(process.argv[3]);
        
        // Execute transform
        let result;
        if (transformModule.{config.function or 'transform'}) {{
            result = transformModule.{config.function or 'transform'}(inputData.data, inputData.variables);
        }} else if (typeof transformModule === 'function') {{
            result = transformModule(inputData.data, inputData.variables);
        }} else {{
            throw new Error('No suitable transform function found');
        }}
        
        // Output result
        console.log(JSON.stringify(result));
        """
        
        return self._execute_nodejs_script(wrapper_script, data, variables, config.timeout)
    
    def _execute_javascript_inline(self, data: Dict[str, Any], config: TransformConfig, variables: Dict[str, Any]) -> Any:
        """Execute inline JavaScript transform code."""
        wrapper_script = f"""
        // Parse input data
        const inputData = JSON.parse(process.argv[2]);
        const data = inputData.data;
        const variables = inputData.variables;
        
        // Execute inline transform
        const transformFunction = function(data, variables) {{
            {config.code}
        }};
        
        const result = transformFunction(data, variables);
        
        // Output result
        console.log(JSON.stringify(result));
        """
        
        return self._execute_nodejs_script(wrapper_script, data, variables, config.timeout)
    
    def _execute_nodejs_script(self, script: str, data: Dict[str, Any], variables: Dict[str, Any], timeout: int) -> Any:
        """Execute a Node.js script with data."""
        try:
            # Create temporary script file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(script)
                script_path = f.name
            
            # Prepare input data
            input_data = json.dumps({"data": data, "variables": variables})
            
            # Execute script
            result = subprocess.run(
                ['node', script_path, input_data],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            # Clean up temporary file
            os.unlink(script_path)
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                logger.error(f"JavaScript execution failed: {result.stderr}")
                return data
                
        except subprocess.TimeoutExpired:
            logger.error(f"JavaScript transform timed out after {timeout} seconds")
            return data
        except Exception as e:
            logger.error(f"JavaScript transform execution error: {e}")
            return data
    
    def _transform_jq(self, data: Dict[str, Any], config: TransformConfig, variables: Dict[str, Any]) -> Any:
        """Execute jq transform."""
        try:
            import jq
        except ImportError:
            logger.error("jq transforms require the 'jq' Python library")
            return data
        
        try:
            if config.file:
                return self._execute_jq_file(data, config, variables)
            elif config.expression:
                return self._execute_jq_inline(data, config, variables)
            else:
                logger.error("jq transform requires either 'file' or 'expression'")
                return data
                
        except Exception as e:
            logger.error(f"jq transform failed: {e}")
            return data
    
    def _execute_jq_file(self, data: Dict[str, Any], config: TransformConfig, variables: Dict[str, Any]) -> Any:
        """Execute jq transform from external file."""
        import jq
        
        transform_file = self.transforms_dir / config.file
        
        if not transform_file.exists():
            logger.error(f"jq transform file not found: {transform_file}")
            return data
        
        # Read jq expression from file
        with open(transform_file, 'r') as f:
            expression = f.read().strip()
        
        # Execute jq transform
        compiled = jq.compile(expression)
        result = compiled.input(data).all()
        
        # Return single result if only one item
        if isinstance(result, list) and len(result) == 1:
            return result[0]
        
        return result
    
    def _execute_jq_inline(self, data: Dict[str, Any], config: TransformConfig, variables: Dict[str, Any]) -> Any:
        """Execute inline jq expression."""
        import jq
        
        # Substitute variables in jq expression
        expression = self._substitute_variables(config.expression, variables)
        
        # Execute jq transform
        compiled = jq.compile(expression)
        result = compiled.input(data).all()
        
        # Return single result if only one item
        if isinstance(result, list) and len(result) == 1:
            return result[0]
        
        return result
    
    def _transform_template(self, data: Dict[str, Any], config: TransformConfig, variables: Dict[str, Any]) -> str:
        """Execute template transform."""
        try:
            from jinja2 import Template
            
            template_content = config.template or config.code
            if config.file:
                template_file = self.transforms_dir / config.file
                if template_file.exists():
                    with open(template_file, 'r') as f:
                        template_content = f.read()
                else:
                    logger.error(f"Template file not found: {template_file}")
                    return str(data)
            
            if not template_content:
                logger.error("Template transform requires 'template', 'code', or 'file'")
                return str(data)
            
            # Combine data and variables for template context
            context = {**data, **variables}
            
            template = Template(template_content)
            return template.render(**context)
            
        except Exception as e:
            logger.error(f"Template transform failed: {e}")
            return str(data)
    
    def _substitute_variables(self, template: str, variables: Dict[str, Any]) -> str:
        """Substitute variables in template string."""
        if not template:
            return template
            
        for key, value in variables.items():
            pattern = f"{{{key}}}"
            template = template.replace(pattern, str(value) if value is not None else "")
        
        return template
    
    def _check_nodejs_available(self) -> bool:
        """Check if Node.js is available."""
        try:
            result = subprocess.run(['node', '--version'], capture_output=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def _check_jq_available(self) -> bool:
        """Check if jq library is available."""
        try:
            import jq
            return True
        except ImportError:
            return False
    
    def get_engine_status(self) -> Dict[str, bool]:
        """Get status of available transform engines."""
        return {
            "python": True,  # Always available
            "javascript": self._javascript_available,
            "jq": self._jq_available,
            "template": True  # Jinja2 should be available
        }