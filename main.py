#!/usr/bin/env python3
from langchain_mcp_m2m import MCPClientCredentials
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from langchain_anthropic import ChatAnthropic
import sys
import json
import os
import shutil
import argparse
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

def extract_bundled_files():
    """Extract bundled data.json to exe directory if needed."""
    if not getattr(sys, 'frozen', False):
        return  # Not running as exe, skip extraction
    
    exe_dir = Path(sys.executable).parent
    
    # Extract data.json if bundled (but not .env - it stays in the bundle)
    if hasattr(sys, '_MEIPASS'):  # PyInstaller temporary directory
        bundle_dir = Path(sys._MEIPASS)
        
        # Extract data.json
        bundled_data_json = bundle_dir / 'data.json'
        target_data_json = exe_dir / 'data.json'
        if bundled_data_json.exists() and not target_data_json.exists():
            shutil.copy2(bundled_data_json, target_data_json)


def get_data_path() -> str:
    """Get the path to data.json file."""
    # Extract bundled files first if running as exe
    extract_bundled_files()
    
    # Check if running as compiled executable (PyInstaller, etc.)
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        exe_dir = Path(sys.executable).parent
        return str(exe_dir / 'data.json')
    else:
        # Running as script
        script_dir = Path(__file__).parent
        return str(script_dir / 'data.json')


# Load .env file - from bundle when frozen, otherwise current directory
extract_bundled_files()  # Extract data.json first
if getattr(sys, 'frozen', False):
    # Running as compiled executable - load .env from bundle
    if hasattr(sys, '_MEIPASS'):
        bundle_dir = Path(sys._MEIPASS)
        env_path = bundle_dir / '.env'
        if env_path.exists():
            load_dotenv(env_path)
        else:
            # Fallback to exe directory
            exe_dir = Path(sys.executable).parent
            env_path = exe_dir / '.env'
            if env_path.exists():
                load_dotenv(env_path)
else:
    # Running as script
    load_dotenv()


def load_credentials() -> Dict[str, str]:
    """Load credentials from data.json file."""
    data_path = get_data_path()

    if not os.path.exists(data_path):
        raise FileNotFoundError(
            f"data.json not found at {data_path}. Please create it with your credentials.")

    with open(data_path, 'r', encoding='utf-8') as f:
        data: Dict[str, Any] = json.load(f)

    client_id = data.get('editable', {}).get(
        'locus_client_id', {}).get('value', '')
    client_secret = data.get('editable', {}).get(
        'locus_client_secret', {}).get('value', '')

    if not client_id or not client_secret:
        raise ValueError(
            'LOCUS_CLIENT_ID and LOCUS_CLIENT_SECRET must be set in data.json')

    return {
        'client_id': client_id,
        'client_secret': client_secret
    }


async def process_query(query: str, client_id: str, client_secret: str) -> str:
    """Process a query using the Locus MCP agent."""
    # Create MCP client with Client Credentials
    client = MCPClientCredentials(
        {
            'locus': {
                'url': 'https://mcp.paywithlocus.com/mcp',
                'transport': 'streamable_http',
                'auth': {
                    'client_id': client_id,
                    'client_secret': client_secret
                }
            }
        }
    )

    # Connect and load tools
    await client.initialize()
    tools = await client.get_tools()

    # Create LLM and agent
    llm = ChatAnthropic(
        model='claude-sonnet-4-20250514',
        anthropic_api_key=os.getenv('ANTHROPIC_API_KEY')
    )

    agent = create_react_agent(llm, tools)

    # Run the query
    result = await agent.ainvoke({
        'messages': [HumanMessage(content=query)]
    })

    # Get the last message content
    last_message = result['messages'][-1]
    if hasattr(last_message, 'content'):
        return last_message.content
    else:
        return str(last_message)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Locus MCP Agent')
    parser.add_argument('command', choices=['run'], help='Command to execute')
    parser.add_argument('query', nargs='+', help='Query to process')

    args = parser.parse_args()

    if args.command != 'run':
        print('❌ Error: Invalid command')
        print('Usage: python index.py run "<your query>"')
        sys.exit(1)

    query = ' '.join(args.query)
    if not query:
        print('❌ Error: Query parameter is required')
        print('Usage: python index.py run "<your query>"')
        sys.exit(1)

    try:
        # Load credentials from data.json
        credentials = load_credentials()

        # Process the query
        import asyncio
        response = asyncio.run(process_query(
            query,
            credentials['client_id'],
            credentials['client_secret']
        ))

        print(response)
    except Exception as error:
        import traceback
        print(f'❌ Error: {error}')
        print('\nFull traceback:')
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
