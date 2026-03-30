#!/usr/bin/env python3
"""
Minimalist Coding Agent - Entry Point

A simple, readable agent that exposes the agent loop for teaching purposes.
Run with: python main.py "your task here"

Example:
    python main.py "Create a file called hello.py that prints Hello World"
"""

import argparse
import os
import sys

from agent import Agent
from tdd_agent import TDD_Agent
from tdd_multiagent import TDD_MultiAgent
from providers import ClaudeProvider, GroqProvider
from tools import ReadFileTool, WriteFileTool, ShellTool


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="A minimalist coding agent for teaching",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python main.py "Create a hello.py file that prints Hello World"
    python main.py "Read the contents of main.py"
    python main.py "List all Python files in the current directory"
        """,
    )
    parser.add_argument("task", help="The task for the agent to perform")
    parser.add_argument(
        "--provider",
        choices=["claude", "groq"],
        default="groq",
        help="LLM provider to use (default: groq)",
    )
    parser.add_argument(
        "--model", 
        default="openai/gpt-oss-120b",
        help="Groq model to use (default: openai/gpt-oss-120b)",
    )
    parser.add_argument(
        "--output", "-o",
        help="Save transcript to file (.md for Markdown, .txt for plain text)",
    )
    args = parser.parse_args()

    # Get API key from environment
    if args.provider == "claude":
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            print("Error: ANTHROPIC_API_KEY environment variable not set")
            print("Get your API key from https://console.anthropic.com/")
            sys.exit(1)
    elif args.provider == "groq":
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            print("Error: GROQ_API_KEY environment variable not set")
            print("Get your API key from https://console.groq.com/")
            sys.exit(1)

    # Create the provider 
    if args.provider == "claude":
        provider = ClaudeProvider(api_key=api_key, model=args.model)
    elif args.provider == "groq":
        provider = GroqProvider(api_key=api_key, model=args.model)

    # Create the tools
    tools = [
        ReadFileTool(),
        WriteFileTool(),
        ShellTool(),
    ]

    # Create and run the agent
    # agent = Agent(provider=provider, tools=tools, transcript_path=args.output)
    # agent = TDD_Agent(provider=provider, tools=tools, transcript_path=args.output)
    agent = TDD_MultiAgent(test_provider=provider, code_provider=provider, tools=tools, transcript_path=args.output)
    agent.run(args.task)


if __name__ == "__main__":
    main()
