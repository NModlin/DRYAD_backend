#!/usr/bin/env python3
"""
DRYAD.AI Developer CLI Tool

Advanced command-line interface for DRYAD.AI development, testing, and debugging.
Provides utilities for developers working with the DRYAD.AI platform.
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
import subprocess
import tempfile

try:
    import click
    import httpx
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich.prompt import Prompt, Confirm
    from rich.syntax import Syntax
    from rich.markdown import Markdown
    from rich.tree import Tree
    from rich.live import Live
    from rich.layout import Layout
    import yaml
except ImportError:
    print("❌ Required dependencies not installed. Install with:")
    print("pip install click httpx rich pyyaml")
    sys.exit(1)

console = Console()

@click.group()
@click.option('--base-url', default='http://localhost:8000', help='DRYAD.AI API base URL')
@click.option('--api-key', default=None, help='API key for authentication')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def cli(ctx, base_url: str, api_key: Optional[str], verbose: bool):
    """🤖 DRYAD.AI Developer CLI - Advanced tools for DRYAD.AI development"""
    ctx.ensure_object(dict)
    ctx.obj['base_url'] = base_url
    ctx.obj['api_key'] = api_key or os.getenv('GREMLINS_AI_API_KEY')
    ctx.obj['verbose'] = verbose
    
    if verbose:
        console.print(Panel(
            f"[bold blue]DRYAD.AI Developer CLI[/bold blue]\n"
            f"Base URL: {base_url}\n"
            f"API Key: {'***' if ctx.obj['api_key'] else 'None'}\n"
            f"Verbose: {verbose}",
            title="🔧 Configuration",
            border_style="blue"
        ))

@cli.command()
@click.pass_context
def health(ctx):
    """🏥 Check system health and component status"""
    async def _health_check():
        try:
            async with httpx.AsyncClient() as client:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console
                ) as progress:
                    task = progress.add_task("🔍 Checking system health...", total=None)
                    
                    response = await client.get(f"{ctx.obj['base_url']}/api/v1/health")
                    progress.remove_task(task)
                    
                    if response.status_code == 200:
                        health_data = response.json()
                        
                        # Create health status table
                        table = Table(title="🏥 System Health Status")
                        table.add_column("Component", style="cyan", no_wrap=True)
                        table.add_column("Status", style="bold")
                        table.add_column("Details", style="yellow")
                        
                        # Overall status
                        status = health_data.get('status', 'unknown')
                        status_emoji = "✅" if status == "healthy" else "❌" if status == "unhealthy" else "⚠️"
                        table.add_row("Overall", f"{status_emoji} {status.title()}", "")
                        
                        # Component statuses
                        components = health_data.get('components', {})
                        for component, comp_status in components.items():
                            comp_emoji = "✅" if comp_status == "healthy" else "❌" if comp_status == "unhealthy" else "⚠️"
                            table.add_row(component.title(), f"{comp_emoji} {comp_status.title()}", "")
                        
                        console.print(table)
                        
                        # Additional info
                        if ctx.obj['verbose']:
                            console.print("\n[bold]Additional Information:[/bold]")
                            console.print(f"Version: {health_data.get('version', 'Unknown')}")
                            console.print(f"Timestamp: {health_data.get('timestamp', 'Unknown')}")
                            
                    else:
                        console.print(f"❌ Health check failed: HTTP {response.status_code}", style="bold red")
                        
        except Exception as e:
            console.print(f"❌ Health check failed: {e}", style="bold red")
    
    asyncio.run(_health_check())

@cli.command()
@click.option('--endpoint', default='/api/v1/agent/invoke', help='API endpoint to test')
@click.option('--method', default='POST', help='HTTP method')
@click.option('--data', help='JSON data to send')
@click.option('--file', 'data_file', help='File containing JSON data')
@click.pass_context
def api_test(ctx, endpoint: str, method: str, data: Optional[str], data_file: Optional[str]):
    """🧪 Test API endpoints with custom data"""
    async def _api_test():
        try:
            # Prepare request data
            request_data = None
            if data:
                request_data = json.loads(data)
            elif data_file:
                with open(data_file, 'r') as f:
                    request_data = json.load(f)
            
            # Default test data for agent invoke
            if endpoint == '/api/v1/agent/invoke' and not request_data:
                request_data = {
                    "input": "Hello, this is a test message from the developer CLI!",
                    "save_conversation": False
                }
            
            headers = {'Content-Type': 'application/json'}
            if ctx.obj['api_key']:
                headers['Authorization'] = f"Bearer {ctx.obj['api_key']}"
            
            async with httpx.AsyncClient() as client:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console
                ) as progress:
                    task = progress.add_task(f"🧪 Testing {method} {endpoint}...", total=None)
                    
                    start_time = time.time()
                    response = await client.request(
                        method,
                        f"{ctx.obj['base_url']}{endpoint}",
                        json=request_data,
                        headers=headers
                    )
                    end_time = time.time()
                    
                    progress.remove_task(task)
                
                # Display results
                status_color = "green" if 200 <= response.status_code < 300 else "red"
                console.print(Panel(
                    f"[bold]Status:[/bold] [{status_color}]{response.status_code}[/{status_color}]\n"
                    f"[bold]Response Time:[/bold] {(end_time - start_time) * 1000:.2f}ms\n"
                    f"[bold]Content Type:[/bold] {response.headers.get('content-type', 'Unknown')}",
                    title=f"🧪 API Test Results - {method} {endpoint}",
                    border_style=status_color
                ))
                
                # Display response
                try:
                    response_json = response.json()
                    console.print("\n[bold]Response Body:[/bold]")
                    console.print_json(json.dumps(response_json, indent=2))
                except:
                    console.print("\n[bold]Response Body:[/bold]")
                    console.print(response.text)
                
        except Exception as e:
            console.print(f"❌ API test failed: {e}", style="bold red")
    
    asyncio.run(_api_test())

@cli.command()
@click.option('--count', default=10, help='Number of requests to send')
@click.option('--concurrent', default=1, help='Number of concurrent requests')
@click.option('--endpoint', default='/api/v1/agent/invoke', help='Endpoint to benchmark')
@click.pass_context
def benchmark(ctx, count: int, concurrent: int, endpoint: str):
    """⚡ Benchmark API performance"""
    async def _benchmark():
        console.print(Panel(
            f"[bold]Endpoint:[/bold] {endpoint}\n"
            f"[bold]Total Requests:[/bold] {count}\n"
            f"[bold]Concurrent:[/bold] {concurrent}",
            title="⚡ Benchmark Configuration",
            border_style="yellow"
        ))
        
        results = []
        
        async def make_request(session: httpx.AsyncClient, request_id: int):
            try:
                start_time = time.time()
                response = await session.post(
                    f"{ctx.obj['base_url']}{endpoint}",
                    json={"input": f"Benchmark request #{request_id}", "save_conversation": False},
                    headers={'Content-Type': 'application/json'}
                )
                end_time = time.time()
                
                return {
                    'id': request_id,
                    'status_code': response.status_code,
                    'response_time': (end_time - start_time) * 1000,
                    'success': 200 <= response.status_code < 300
                }
            except Exception as e:
                return {
                    'id': request_id,
                    'status_code': 0,
                    'response_time': 0,
                    'success': False,
                    'error': str(e)
                }
        
        async with httpx.AsyncClient() as session:
            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=console
            ) as progress:
                task = progress.add_task("🚀 Running benchmark...", total=count)
                
                # Run requests in batches
                for i in range(0, count, concurrent):
                    batch_size = min(concurrent, count - i)
                    batch_tasks = [
                        make_request(session, i + j + 1) 
                        for j in range(batch_size)
                    ]
                    
                    batch_results = await asyncio.gather(*batch_tasks)
                    results.extend(batch_results)
                    progress.update(task, advance=batch_size)
        
        # Analyze results
        successful_requests = [r for r in results if r['success']]
        failed_requests = [r for r in results if not r['success']]
        
        if successful_requests:
            response_times = [r['response_time'] for r in successful_requests]
            avg_time = sum(response_times) / len(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            
            # Calculate percentiles
            sorted_times = sorted(response_times)
            p50 = sorted_times[len(sorted_times) // 2]
            p95 = sorted_times[int(len(sorted_times) * 0.95)]
            p99 = sorted_times[int(len(sorted_times) * 0.99)]
        else:
            avg_time = min_time = max_time = p50 = p95 = p99 = 0
        
        # Display results
        table = Table(title="📊 Benchmark Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total Requests", str(count))
        table.add_row("Successful", str(len(successful_requests)))
        table.add_row("Failed", str(len(failed_requests)))
        table.add_row("Success Rate", f"{len(successful_requests)/count*100:.1f}%")
        table.add_row("Average Response Time", f"{avg_time:.2f}ms")
        table.add_row("Min Response Time", f"{min_time:.2f}ms")
        table.add_row("Max Response Time", f"{max_time:.2f}ms")
        table.add_row("50th Percentile", f"{p50:.2f}ms")
        table.add_row("95th Percentile", f"{p95:.2f}ms")
        table.add_row("99th Percentile", f"{p99:.2f}ms")
        
        console.print(table)
        
        if failed_requests and ctx.obj['verbose']:
            console.print("\n[bold red]Failed Requests:[/bold red]")
            for req in failed_requests[:5]:  # Show first 5 failures
                console.print(f"Request #{req['id']}: {req.get('error', 'Unknown error')}")
    
    asyncio.run(_benchmark())

@cli.command()
@click.option('--output', default='gremlins-ai-config.yaml', help='Output configuration file')
@click.pass_context
def init_config(ctx, output: str):
    """📝 Initialize a configuration file for development"""
    config = {
        'gremlins_ai': {
            'base_url': ctx.obj['base_url'],
            'api_key': '${GREMLINS_AI_API_KEY}',
            'timeout': 30,
            'max_retries': 3
        },
        'development': {
            'debug': True,
            'log_level': 'INFO',
            'auto_reload': True
        },
        'testing': {
            'test_data_dir': './test_data',
            'mock_responses': False,
            'coverage_threshold': 80
        },
        'deployment': {
            'environment': 'development',
            'docker': {
                'image': 'DRYAD.AI-backend:latest',
                'ports': ['8000:8000'],
                'volumes': ['./data:/app/data']
            }
        }
    }
    
    with open(output, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, indent=2)
    
    console.print(Panel(
        f"[bold green]✅ Configuration file created:[/bold green] {output}\n\n"
        f"[bold]Next steps:[/bold]\n"
        f"1. Edit the configuration file to match your setup\n"
        f"2. Set environment variables (GREMLINS_AI_API_KEY)\n"
        f"3. Use the config with: --config {output}",
        title="📝 Configuration Initialized",
        border_style="green"
    ))

@cli.command()
@click.argument('template', type=click.Choice(['python-basic', 'python-async', 'javascript-basic', 'react-app', 'nextjs-app']))
@click.option('--output-dir', default='.', help='Output directory for the template')
@click.option('--name', help='Project name')
@click.pass_context
def create_template(ctx, template: str, output_dir: str, name: Optional[str]):
    """🏗️ Create a new project from template"""
    if not name:
        name = Prompt.ask("Enter project name")
    
    project_dir = Path(output_dir) / name
    
    if project_dir.exists():
        if not Confirm.ask(f"Directory {project_dir} already exists. Continue?"):
            return
    
    project_dir.mkdir(parents=True, exist_ok=True)
    
    templates = {
        'python-basic': create_python_basic_template,
        'python-async': create_python_async_template,
        'javascript-basic': create_javascript_basic_template,
        'react-app': create_react_app_template,
        'nextjs-app': create_nextjs_app_template,
    }
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task(f"🏗️ Creating {template} template...", total=None)
        
        templates[template](project_dir, name, ctx.obj)
        
        progress.remove_task(task)
    
    console.print(Panel(
        f"[bold green]✅ Template created successfully![/bold green]\n\n"
        f"[bold]Project:[/bold] {name}\n"
        f"[bold]Location:[/bold] {project_dir}\n"
        f"[bold]Template:[/bold] {template}\n\n"
        f"[bold]Next steps:[/bold]\n"
        f"1. cd {project_dir}\n"
        f"2. Follow the README.md instructions\n"
        f"3. Start building with DRYAD.AI!",
        title="🏗️ Template Created",
        border_style="green"
    ))

def create_python_basic_template(project_dir: Path, name: str, config: Dict[str, Any]):
    """Create a basic Python template"""
    # Create main.py
    main_py = f'''#!/usr/bin/env python3
"""
{name} - DRYAD.AI Python Application

Basic example of using the DRYAD.AI Python SDK.
"""

import asyncio
from dryad_ai import DRYAD.AIClient

async def main():
    """Main application function"""
    async with DRYAD.AIClient(
        base_url="{config['base_url']}",
        api_key="{config.get('api_key', 'your-api-key-here')}"
    ) as client:
        
        # Test connection
        health = await client.get_system_health()
        print(f"🏥 System status: {{health.status}}")
        
        # Simple chat
        response = await client.invoke_agent("Hello, DRYAD.AI!")
        print(f"🤖 AI Response: {{response['output']}}")
        
        # Create conversation
        conversation = await client.create_conversation(title="{name} Chat")
        print(f"💬 Created conversation: {{conversation.id}}")
        
        # Chat with context
        response = await client.invoke_agent(
            "What can you help me with?",
            conversation_id=conversation.id,
            save_conversation=True
        )
        print(f"🤖 AI Response: {{response['output']}}")

if __name__ == "__main__":
    asyncio.run(main())
'''
    
    # Create requirements.txt
    requirements = '''gremlins-ai>=1.0.0-beta.1
python-dotenv>=1.0.0
'''
    
    # Create README.md
    readme = f'''# {name}

A DRYAD.AI Python application.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export GREMLINS_AI_API_KEY=your-api-key-here
export GREMLINS_AI_BASE_URL=http://localhost:8000
```

3. Run the application:
```bash
python main.py
```

## Features

- Basic DRYAD.AI integration
- Health checking
- Simple chat functionality
- Conversation management

## Next Steps

- Add error handling
- Implement more complex workflows
- Add logging and monitoring
- Create tests
'''
    
    # Write files
    (project_dir / 'main.py').write_text(main_py)
    (project_dir / 'requirements.txt').write_text(requirements)
    (project_dir / 'README.md').write_text(readme)
    (project_dir / '.env.example').write_text('GREMLINS_AI_API_KEY=your-api-key-here\nGREMLINS_AI_BASE_URL=http://localhost:8000\n')

def create_python_async_template(project_dir: Path, name: str, config: Dict[str, Any]):
    """Create an advanced async Python template"""
    # Implementation would go here
    create_python_basic_template(project_dir, name, config)  # Fallback for now

def create_javascript_basic_template(project_dir: Path, name: str, config: Dict[str, Any]):
    """Create a basic JavaScript template"""
    # Implementation would go here
    pass

def create_react_app_template(project_dir: Path, name: str, config: Dict[str, Any]):
    """Create a React app template"""
    # Implementation would go here
    pass

def create_nextjs_app_template(project_dir: Path, name: str, config: Dict[str, Any]):
    """Create a Next.js app template"""
    # Implementation would go here
    pass

@cli.command()
@click.pass_context
def doctor(ctx):
    """🩺 Diagnose common development issues"""
    console.print(Panel(
        "[bold blue]🩺 DRYAD.AI Development Doctor[/bold blue]\n"
        "Checking for common development issues...",
        border_style="blue"
    ))
    
    issues = []
    
    # Check Python version
    python_version = sys.version_info
    if python_version < (3, 8):
        issues.append("❌ Python version too old. Requires Python 3.8+")
    else:
        console.print("✅ Python version OK")
    
    # Check if DRYAD.AI server is running
    try:
        import httpx
        response = httpx.get(f"{ctx.obj['base_url']}/api/v1/health", timeout=5)
        if response.status_code == 200:
            console.print("✅ DRYAD.AI server is running")
        else:
            issues.append(f"❌ DRYAD.AI server returned status {response.status_code}")
    except Exception as e:
        issues.append(f"❌ Cannot connect to DRYAD.AI server: {e}")
    
    # Check SDK installation
    try:
        import dryad_ai
        console.print("✅ DRYAD.AI SDK is installed")
    except ImportError:
        issues.append("❌ DRYAD.AI SDK not installed. Run: pip install gremlins-ai")
    
    # Check environment variables
    if not ctx.obj['api_key']:
        issues.append("⚠️ GREMLINS_AI_API_KEY not set (optional for development)")
    else:
        console.print("✅ API key configured")
    
    # Summary
    if issues:
        console.print("\n[bold red]Issues Found:[/bold red]")
        for issue in issues:
            console.print(f"  {issue}")
    else:
        console.print("\n[bold green]🎉 No issues found! Your development environment looks good.[/bold green]")

def main():
    """Main entry point"""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        console.print(f"❌ Unexpected error: {e}", style="bold red")
        sys.exit(1)

if __name__ == "__main__":
    main()
