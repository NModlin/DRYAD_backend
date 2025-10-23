#!/usr/bin/env python3
"""
DRYAD.AI CLI Tool

Command-line interface for interacting with the DRYAD.AI platform.
Provides easy access to all major features including chat, document processing,
multi-agent workflows, and system management.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

try:
    import click
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.prompt import Prompt, Confirm
    from rich.syntax import Syntax
    from rich.markdown import Markdown
except ImportError:
    print("❌ CLI dependencies not installed. Install with: pip install gremlins-ai[cli]")
    sys.exit(1)

from .client import DRYAD.AIClient
from .exceptions import DRYAD.AIError

console = Console()

# Global client instance
client: Optional[DRYAD.AIClient] = None

@click.group()
@click.option('--base-url', default=None, help='DRYAD.AI API base URL')
@click.option('--api-key', default=None, help='API key for authentication')
@click.option('--timeout', default=30, help='Request timeout in seconds')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def cli(ctx, base_url: Optional[str], api_key: Optional[str], timeout: int, verbose: bool):
    """DRYAD.AI CLI - Interact with the DRYAD.AI platform from the command line."""
    ctx.ensure_object(dict)
    ctx.obj['base_url'] = base_url or os.getenv('GREMLINS_AI_BASE_URL', 'http://localhost:8000')
    ctx.obj['api_key'] = api_key or os.getenv('GREMLINS_AI_API_KEY')
    ctx.obj['timeout'] = timeout
    ctx.obj['verbose'] = verbose
    
    if verbose:
        console.print(f"🔧 Configuration:", style="bold blue")
        console.print(f"   Base URL: {ctx.obj['base_url']}")
        console.print(f"   API Key: {'***' if ctx.obj['api_key'] else 'None'}")
        console.print(f"   Timeout: {timeout}s")

@cli.command()
@click.argument('message')
@click.option('--conversation-id', help='Conversation ID for context')
@click.option('--save', is_flag=True, help='Save conversation')
@click.option('--format', 'output_format', type=click.Choice(['text', 'json', 'markdown']), default='text')
@click.pass_context
def chat(ctx, message: str, conversation_id: Optional[str], save: bool, output_format: str):
    """Send a message to the AI agent."""
    async def _chat():
        try:
            async with DRYAD.AIClient(
                base_url=ctx.obj['base_url'],
                api_key=ctx.obj['api_key'],
                timeout=ctx.obj['timeout']
            ) as client:
                
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console
                ) as progress:
                    task = progress.add_task("🤔 Thinking...", total=None)
                    
                    response = await client.invoke_agent(
                        message,
                        conversation_id=conversation_id,
                        save_conversation=save
                    )
                    
                    progress.remove_task(task)
                
                if output_format == 'json':
                    console.print_json(json.dumps(response, indent=2))
                elif output_format == 'markdown':
                    console.print(Markdown(response['output']))
                else:
                    console.print(Panel(
                        response['output'],
                        title="🤖 AI Response",
                        border_style="green"
                    ))
                    
                    if ctx.obj['verbose']:
                        console.print(f"\n⏱️  Execution time: {response.get('execution_time', 0):.2f}s")
                        if conversation_id:
                            console.print(f"💬 Conversation ID: {conversation_id}")
                
        except DRYAD.AIError as e:
            console.print(f"❌ Error: {e}", style="bold red")
            sys.exit(1)
    
    asyncio.run(_chat())

@cli.command()
@click.option('--limit', default=10, help='Number of conversations to list')
@click.option('--format', 'output_format', type=click.Choice(['table', 'json']), default='table')
@click.pass_context
def conversations(ctx, limit: int, output_format: str):
    """List recent conversations."""
    async def _list_conversations():
        try:
            async with DRYAD.AIClient(
                base_url=ctx.obj['base_url'],
                api_key=ctx.obj['api_key'],
                timeout=ctx.obj['timeout']
            ) as client:
                
                conversations = await client.list_conversations(limit=limit)
                
                if output_format == 'json':
                    console.print_json(json.dumps([conv.dict() for conv in conversations], indent=2))
                else:
                    table = Table(title="Recent Conversations")
                    table.add_column("ID", style="cyan", no_wrap=True)
                    table.add_column("Title", style="green")
                    table.add_column("Messages", justify="right", style="blue")
                    table.add_column("Created", style="yellow")
                    
                    for conv in conversations:
                        table.add_row(
                            conv.id[:8] + "...",
                            conv.title or "Untitled",
                            str(len(conv.messages)) if hasattr(conv, 'messages') else "N/A",
                            conv.created_at.strftime("%Y-%m-%d %H:%M") if conv.created_at else "N/A"
                        )
                    
                    console.print(table)
                
        except DRYAD.AIError as e:
            console.print(f"❌ Error: {e}", style="bold red")
            sys.exit(1)
    
    asyncio.run(_list_conversations())

@cli.command()
@click.argument('conversation_id')
@click.option('--format', 'output_format', type=click.Choice(['text', 'json', 'markdown']), default='text')
@click.pass_context
def show_conversation(ctx, conversation_id: str, output_format: str):
    """Show details of a specific conversation."""
    async def _show_conversation():
        try:
            async with DRYAD.AIClient(
                base_url=ctx.obj['base_url'],
                api_key=ctx.obj['api_key'],
                timeout=ctx.obj['timeout']
            ) as client:
                
                conversation = await client.get_conversation(conversation_id)
                
                if output_format == 'json':
                    console.print_json(json.dumps(conversation.dict(), indent=2))
                else:
                    console.print(Panel(
                        f"**Title:** {conversation.title or 'Untitled'}\n"
                        f"**ID:** {conversation.id}\n"
                        f"**Messages:** {len(conversation.messages)}\n"
                        f"**Created:** {conversation.created_at}",
                        title="💬 Conversation Details",
                        border_style="blue"
                    ))
                    
                    for i, msg in enumerate(conversation.messages, 1):
                        style = "green" if msg.role == "assistant" else "blue"
                        console.print(Panel(
                            msg.content,
                            title=f"Message {i} - {msg.role.title()}",
                            border_style=style
                        ))
                
        except DRYAD.AIError as e:
            console.print(f"❌ Error: {e}", style="bold red")
            sys.exit(1)
    
    asyncio.run(_show_conversation())

@cli.command()
@click.option('--format', 'output_format', type=click.Choice(['table', 'json']), default='table')
@click.pass_context
def status(ctx, output_format: str):
    """Check system status and health."""
    async def _status():
        try:
            async with DRYAD.AIClient(
                base_url=ctx.obj['base_url'],
                api_key=ctx.obj['api_key'],
                timeout=ctx.obj['timeout']
            ) as client:
                
                health = await client.get_system_health()
                
                if output_format == 'json':
                    console.print_json(json.dumps(health.dict(), indent=2))
                else:
                    # Create status table
                    table = Table(title="System Status")
                    table.add_column("Component", style="cyan")
                    table.add_column("Status", style="green")
                    table.add_column("Details", style="yellow")
                    
                    # Add rows based on health data
                    status_emoji = "✅" if health.status == "healthy" else "❌"
                    table.add_row("Overall", f"{status_emoji} {health.status.title()}", "")
                    
                    if hasattr(health, 'components'):
                        for component, status in health.components.items():
                            emoji = "✅" if status == "healthy" else "❌"
                            table.add_row(component.title(), f"{emoji} {status.title()}", "")
                    
                    console.print(table)
                
        except DRYAD.AIError as e:
            console.print(f"❌ Error: {e}", style="bold red")
            sys.exit(1)
    
    asyncio.run(_status())

@cli.command()
@click.pass_context
def interactive(ctx):
    """Start an interactive chat session."""
    async def _interactive():
        console.print(Panel(
            "🤖 DRYAD.AI Interactive Chat\n\n"
            "Commands:\n"
            "  /quit, /exit - Exit the session\n"
            "  /new - Start a new conversation\n"
            "  /help - Show this help",
            title="Welcome to DRYAD.AI",
            border_style="green"
        ))
        
        conversation_id: Optional[str] = None
        
        try:
            async with DRYAD.AIClient(
                base_url=ctx.obj['base_url'],
                api_key=ctx.obj['api_key'],
                timeout=ctx.obj['timeout']
            ) as client:
                
                while True:
                    try:
                        user_input = Prompt.ask("\n[bold blue]You[/bold blue]").strip()
                        
                        if user_input.lower() in ['/quit', '/exit']:
                            console.print("👋 Goodbye!")
                            break
                        elif user_input.lower() == '/new':
                            conversation_id = None
                            console.print("🆕 Started new conversation")
                            continue
                        elif user_input.lower() == '/help':
                            console.print(Panel(
                                "Commands:\n"
                                "  /quit, /exit - Exit the session\n"
                                "  /new - Start a new conversation\n"
                                "  /help - Show this help",
                                title="Help",
                                border_style="blue"
                            ))
                            continue
                        elif not user_input:
                            continue
                        
                        # Create conversation if needed
                        if not conversation_id:
                            conversation = await client.create_conversation(title="Interactive Chat")
                            conversation_id = conversation.id
                        
                        # Send message
                        with Progress(
                            SpinnerColumn(),
                            TextColumn("[progress.description]{task.description}"),
                            console=console
                        ) as progress:
                            task = progress.add_task("🤔 Thinking...", total=None)
                            
                            response = await client.invoke_agent(
                                user_input,
                                conversation_id=conversation_id,
                                save_conversation=True
                            )
                            
                            progress.remove_task(task)
                        
                        console.print(Panel(
                            response['output'],
                            title="🤖 AI",
                            border_style="green"
                        ))
                        
                    except KeyboardInterrupt:
                        console.print("\n👋 Goodbye!")
                        break
                    except DRYAD.AIError as e:
                        console.print(f"❌ Error: {e}", style="bold red")
                    except Exception as e:
                        console.print(f"❌ Unexpected error: {e}", style="bold red")
                        
        except Exception as e:
            console.print(f"❌ Failed to start interactive session: {e}", style="bold red")
            sys.exit(1)
    
    asyncio.run(_interactive())

def main():
    """Main entry point for the CLI."""
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
