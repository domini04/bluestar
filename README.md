# BlueStar

**AI-Powered Developer Blog Generation Agent**

BlueStar is an AI agent designed to automatically generate and publish developer blog posts by analyzing user-selected Git commits. The agent uses LangGraph for workflow orchestration and is designed to run locally as a powerful command-line tool.

## Overview

BlueStar analyzes Git commits to understand development progress and context, then generates developer blog posts ("coding diaries") based on this analysis, guided by predefined instructions and optional user input.

**Core Workflow**: `Input Collection → Commit Fetching → Analysis → Content Generation → Human Review Loop → Publishing Decision → Optional Blog Publishing`

## Features

- 🔍 **Git Integration**: Analyzes commit messages and diffs with multi-file processing
- 🤖 **AI-Powered Analysis**: LLM-powered commit analysis with context assessment
- 📊 **Enhanced Context**: Automatic repository metadata, README, and config integration  
- 🔬 **Quality Assurance**: Systematic evaluation framework with LangSmith tracing
- 📝 **Blog Generation**: Creates structured, narrative blog posts
- 🚀 **Publishing**: Publish to Ghost or Notion (database or page URL)
- 🔄 **Self-RAG**: Self-reflection and refinement for quality improvement *(Planned)*
- 👤 **Human-in-the-Loop**: Interactive content refinement and publishing decisions

## Architecture

BlueStar is built on a modular, stateful workflow orchestrated by **LangGraph**. The architecture is designed for clarity, maintainability, and robustness, with a clear separation between workflow orchestration, state management, and individual node operations.

For a detailed explanation of the components, data flow, and design principles, please see the [**LangGraph Architecture Document**](LangGraph_Architecture.md).

## Development Status

✅ **Core CLI Functionality Complete**

The core feature set of BlueStar is complete and available for use via the command-line interface (CLI). This includes fetching single commits, AI-powered analysis, content generation, a human-in-the-loop refinement process, and publishing to supported platforms.

Future development will focus on the following priorities:
1.  **GUI Implementation**: Creating a graphical user interface for a more interactive user experience.
2.  **Enhanced Context Gathering**: Improving the agent's ability to understand project context for more insightful blog posts. This includes multi-commit analysis.

For a detailed breakdown of past, current, and future development phases, please see the [**BlueStar Development Process document**](BlueStar_Development_Process.md).

## Technology Stack

- **Core**: Python 3.13+, LangGraph, LangChain
- **AI**: OpenAI/Anthropic APIs, Self-RAG patterns
- **Integration**: GitHub API (primary), Git CLI (fallback)
- **Testing**: pytest with comprehensive unit + integration tests, LangSmith tracing
- **Quality**: Evaluation framework for LLM output assessment
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
cp .env.copy .env
# Edit .env with your API keys
```

### Configuration

Set the following environment variables in your `.env` file:

```env
# LLM selection (provider required, model optional)
BLUESTAR_LLM_PROVIDER=openai           # allowed: openai, claude, gemini, grok
BLUESTAR_LLM_MODEL=gpt-5               # optional; defaults per provider (e.g., openai→gpt-5, gemini→gemini-2.5-pro)

# Provider-specific API key (set the one matching your provider)
OPENAI_API_KEY=your_openai_key         # or
ANTHROPIC_API_KEY=your_claude_key      # or
GOOGLE_API_KEY=your_gemini_key         # or
GROK_API_KEY=your_grok_key

# GitHub
GITHUB_TOKEN=your_github_token_here

BLUESTAR_LOG_LEVEL=INFO

# Notion (optional)
NOTION_API_KEY=your_notion_integration_secret
# Accepts either a database URL or a page URL. If a page URL is provided,
# BlueStar will create the blog post as a child page under it.
NOTION_URL=https://www.notion.so/your-workspace/Your-Database-or-Page-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Optional: preselect publishing target (ghost|notion|local|discard)
BLUESTAR_PUBLISH=notion
```

### Usage

```bash
# Interactive CLI mode (development)
uv run python -m src.bluestar.main

# CLI with command line arguments
uv run python -m src.bluestar.main --repo microsoft/vscode --commit abc123def456

# Override LLM selection from CLI (provider allowlist + free-form model)
uv run python -m src.bluestar.main \
  --repo microsoft/vscode --commit abc123def456 \
  --llm-provider openai --llm-model gpt-5

# CLI with additional instructions
uv run python -m src.bluestar.main --repo https://github.com/microsoft/vscode --commit abc123def456 --instructions "Focus on performance improvements"

# Check configuration
uv run python -m src.bluestar.main --config-check

# Run tests
uv run pytest tests/
```

### Notion notes

- "Publish" to Notion means creating a page under the provided Notion URL:
  - If `NOTION_URL` is a database URL → the page is created in that database with structured properties.
  - If `NOTION_URL` is a page URL → the page is created as a child of that page (metadata is embedded in content).
- Ensure your Notion integration has access to the target URL (share the database/page with the integration).

## Development

See `BlueStar_Development_Process.md` for detailed development guidelines and phase-by-phase implementation plan.

## License

This project is currently in development. License to be determined.

---

*BlueStar - Turning code commits into compelling developer stories.*
