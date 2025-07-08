# BlueStar

**AI-Powered Developer Blog Generation Agent**

BlueStar is an AI agent designed to automatically generate and publish developer blog posts by analyzing user-selected Git commits. The agent uses LangGraph for orchestration, Self-RAG for content refinement, and MCP for tool integration.

## Overview

BlueStar analyzes Git commits to understand development progress and context, then generates developer blog posts ("coding diaries") based on this analysis, guided by predefined instructions and optional user input.

**Core Workflow**: `Manual Trigger → Fetch Commits → Analyze → Generate Outline → [Optional: Human Input] → Generate Post → Publish`

## Features

- 🔍 **Git Integration**: Analyzes commit messages and diffs
- 🤖 **AI-Powered Analysis**: Uses LLM to extract meaningful context
- 📝 **Blog Generation**: Creates structured, narrative blog posts
- 🔄 **Self-RAG**: Self-reflection and refinement for quality improvement
- 🛠️ **MCP Integration**: Model Context Protocol for tool orchestration
- 👤 **Human-in-the-Loop**: Optional interactive context gathering

## Development Status

🚧 **Currently in development** - Following phased development approach:

- **Phase 0**: Foundation Setup *(Current)*
- **Phase 1**: Core MVP (single commit → basic blog post)
- **Phase 2**: Analysis Enhancement & Multi-commit support
- **Phase 3**: Publishing Integration & Human-in-the-Loop
- **Phase 4**: Advanced Features & MCP Packaging

## Technology Stack

- **Core**: Python 3.13+, LangGraph, LangChain
- **AI**: OpenAI/Anthropic APIs, Self-RAG patterns
- **Integration**: MCP protocol, GitHub API (primary), Git CLI (fallback)
- **Testing**: pytest
- **Package Management**: uv

## Getting Started

### Prerequisites

- Python 3.13+
- GitHub API access (primary) or local Git repository access (fallback)
- LLM API access (OpenAI, Anthropic, etc.)
- Blog platform API credentials (optional for later phases)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd bluestar

# Install dependencies
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Configuration

Set the following environment variables in your `.env` file:

```env
BLUESTAR_LLM_PROVIDER=openai
BLUESTAR_LLM_MODEL=gpt-4o-mini  
BLUESTAR_LLM_API_KEY=your_api_key_here
GITHUB_TOKEN=your_github_token_here
BLUESTAR_LOG_LEVEL=INFO
```

### Usage

```bash
# Run the main application
python -m src.bluestar.main

# Run tests
pytest tests/
```

## Development

See `BlueStar_Development_Process.md` for detailed development guidelines and phase-by-phase implementation plan.

## License

This project is currently in development. License to be determined.

---

*BlueStar - Turning code commits into compelling developer stories.*
