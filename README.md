# BlueStar

**AI-Powered Developer Blog Generation Agent**

BlueStar is an AI agent designed to automatically generate and publish developer blog posts by analyzing user-selected Git commits. The agent uses LangGraph for orchestration, Self-RAG for content refinement, and MCP for tool integration.

## Overview

BlueStar analyzes Git commits to understand development progress and context, then generates developer blog posts ("coding diaries") based on this analysis, guided by predefined instructions and optional user input.

**Core Workflow**: `Input Collection → Commit Fetching → Analysis → Content Generation → Human Review Loop → Publishing Decision → Optional Blog Publishing`

## Features

- 🔍 **Git Integration**: Analyzes commit messages and diffs
- 🤖 **AI-Powered Analysis**: Uses LLM to extract meaningful context
- 📝 **Blog Generation**: Creates structured, narrative blog posts
- 🔄 **Self-RAG**: Self-reflection and refinement for quality improvement
- 🛠️ **MCP Integration**: Model Context Protocol for tool orchestration
- 👤 **Human-in-the-Loop**: Optional interactive context gathering

## Development Status

🚧 **Currently in development** - Following phased development approach:

- **Phase 0**: Foundation Setup ✅ *(Completed)*
  - Project structure, dependencies, configuration management
  - Data models (CommitData, CommitAnalysis, GhostBlogPost)
  - Custom exception handling and testing infrastructure
- **Phase 1**: Core MVP (single commit → basic blog post) 🔄 *(In Progress)*
  - ✅ GitHub API client with authentication and rate limiting
  - ✅ Commit data parsing and structured models
  - ✅ Real GitHub API integration tested successfully
  - ✅ LangGraph architecture designed with comprehensive workflow
  - ✅ AgentState structure finalized with human-in-the-loop integration
  - ✅ Error handling strategy leveraging existing exception hierarchy
  - ✅ Workflow control decisions (progress tracking, metrics separation)
  - ✅ Performance metrics strategy defined (separate implementation)
  - 🔄 Node implementations - *Next*
  - 🆕 CommitFetcher tool (LangGraph integration)
  - 🆕 CommitAnalyzer node (LLM-powered analysis)
  - 🆕 ContentSynthesizer node with human-in-the-loop
  - 🆕 Complete workflow orchestration
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
# Interactive CLI mode (development)
python -m src.bluestar.main

# CLI with command line arguments
python -m src.bluestar.main --repo microsoft/vscode --commit abc123def456

# CLI with additional instructions
python -m src.bluestar.main --repo https://github.com/microsoft/vscode --commit abc123def456 --instructions "Focus on performance improvements"

# Check configuration
python -m src.bluestar.main --config-check

# Run tests
pytest tests/
```

## Development

See `BlueStar_Development_Process.md` for detailed development guidelines and phase-by-phase implementation plan.

## License

This project is currently in development. License to be determined.

---

*BlueStar - Turning code commits into compelling developer stories.*
