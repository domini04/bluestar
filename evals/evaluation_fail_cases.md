# Evaluation Failure Cases

This document logs specific failure cases identified during automated evaluation (LLM-as-a-Judge) to track regression and guide prompt tuning.

---

## 1. Hallucinated Code Implementation (Faithfulness)

**Date**: 2025-12-08
**Repo/Commit**: `domini04/AI-Imposter` (Commit SHA: `2f3cbdc...`)
**Failure Type**: **Faithfulness (Hallucination)**
**Evaluator Score**: 0/1
**Status**: **RESOLVED (Dec 11, 2025)** via Prompt Tuning ("Strict Reporter" Mode).

### Issue Description
The `ContentSynthesizer` correctly identified the technical topics but generated **generic tutorial code** instead of using the actual implementation provided in the commit diff.

### Detailed Analysis

#### Case A: Dockerfile Mismatch (CRITICAL 🔴)
*   **Reality (Commit Diff)**: Single-stage build, installs `uv`, copies `pyproject.toml`.
    ```dockerfile
    # backend/Dockerfile
    FROM python:3.11-slim
    COPY pyproject.toml ./
    RUN pip install --no-cache-dir uv
    RUN uv pip install --system --no-cache .
    ```
*   **Hallucination (Blog Post)**: Multi-stage build (`AS builder`), copies `requirements.txt`, creates venv.
    ```dockerfile
    FROM python:3.11-slim as builder
    COPY requirements.txt .
    RUN uv venv /opt/venv
    ```
*   **Impact**: **Critical**. Users copying this code would fail to build because `requirements.txt` does not exist in the repo (it uses `pyproject.toml`). This breaks the tutorial utility of the blog.

#### Case B: Middleware Implementation Mismatch (Minor 🟡)
*   **Reality (Commit Diff)**: Uses `starlette.datastructures.Headers` to safely parse headers.
    ```python
    # backend/app/main.py
    if scope["type"] in ("http", "websocket"):
        headers = Headers(scope=scope)
        forwarded_proto = headers.get("x-forwarded-proto")
        if forwarded_proto:
            scope["scheme"] = forwarded_proto
    ```
*   **Hallucination (Blog Post)**: Uses manual dictionary conversion and byte-string keys (`b"x-forwarded-proto"`), which is brittle and stylistically different.
    ```python
    if scope["type"] == "http":
        headers = dict(scope["headers"])
        if b"x-forwarded-proto" in headers:
            scope["scheme"] = headers[b"x-forwarded-proto"].decode("ascii")
    ```
*   **Impact**: Minor. The hallucinated code is less robust but technically valid Python. It simplifies the explanation but misrepresents the specific library choices.

#### Case C: Hardcoded Credentials vs Env Vars (Minor 🟡)
*   **Reality (Commit Diff)**: Robustly checks `os.getenv("GOOGLE_APPLICATION_CREDENTIALS")`.
    ```python
    # backend/app/services/firebase_service.py
    else:
        cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not cred_path:
            raise ValueError(...)
        cred = credentials.Certificate(cred_path)
    ```
*   **Hallucination (Blog Post)**: Hardcodes a file path `"path/to/serviceAccountKey.json"`.
    ```python
    else:
        # Running locally, use the service account file
        cred = credentials.Certificate("path/to/serviceAccountKey.json")
    ```
*   **Impact**: Minor/Medium. It simplifies the example for a reader, but promotes a security bad practice compared to the actual secure implementation.

---

## 2. Async/Sync & Logic Hallucination (Faithfulness)

**Date**: 2025-12-08
**Repo/Commit**: `domini04/AI-Imposter` (Commit SHA: `32d3db0...`)
**Failure Type**: **Faithfulness (Hallucination)**
**Evaluator Score**: 0/1
**Status**: **RESOLVED (Dec 11, 2025)** via Prompt Tuning ("Strict Reporter" Mode).

### Issue Description
The blog post presented synchronous code as asynchronous (`async/await`) and hallucinated collection names.

### Detailed Analysis

#### Case A: Async vs Sync Hallucination (Critical 🔴)
*   **Reality (Commit Diff)**: Standard synchronous Python methods (`def`, `add()`, `stream()`).
    ```python
    # NO async def here
    def _archive_game_result(game_ref, game_data: dict, winner: str):
        # ...
        db = get_firestore_client()
        messages_docs = list(messages_ref.stream())  <-- SYNCHRONOUS stream()
        db.collection("game_results").add(game_result_dict) <-- SYNCHRONOUS add()
    ```
*   **Hallucination (Blog Post)**: Rewrote everything as `async def`, `await db.collection...`.
    ```python
    # Hallucinated ASYNC definition
    async def _archive_game_result(db: AsyncClient, game_id: str):
        game_data = (await game_doc_ref.get()).to_dict()  <-- HALLUCINATED await
        messages_snapshot = await game_doc_ref.collection("messages").get() <-- HALLUCINATED await
        await db.collection("game_results").document(game_id).set(archive_data)
    ```
*   **Impact**: **Critical**. This is a fundamental misrepresentation of the codebase's architecture. A reader might assume the project uses an async driver (like `asyncio-google-cloud-firestore`), which is a major architectural decision not present in the code. It misleads the reader about the tech stack.

#### Case B: Collection Name Errors (Minor 🟡)
*   **Reality**: `game_rooms` collection.
*   **Hallucination**: `games` collection.
    ```python
    game_doc_ref = db.collection("games").document(game_id)  <-- WRONG COLLECTION NAME
    ```
*   **Impact**: Minor. It's a simplification that breaks copy-paste ability but conveys the semantic meaning clearly.

#### Case C: Function Signature Mismatch (Minor 🟡)
*   **Reality**: `_archive_game_result(game_ref, game_data, winner)`
*   **Hallucination**: `_archive_game_result(db, game_id)`
*   **Impact**: Minor. The hallucinated signature is cleaner for a blog post, though factually incorrect.

---

## 3. Enum & Frontend Logic Hallucination (Faithfulness)

**Date**: 2025-12-08
**Repo/Commit**: `domini04/AI-Imposter` (Commit SHA: `[PENDING]`)
**Failure Type**: **Faithfulness (Hallucination)**
**Evaluator Score**: 0/1
**Status**: **IMPROVED (Dec 11, 2025)**. Major hallucinations gone. Minor inference of Enum values remains but is stylistically correct (snake_case).

### Issue Description
The blog post hallucinated specific Enum values and frontend function names, inventing a "cleaner" implementation rather than reporting the actual one.

### Detailed Analysis

#### Case A: Invented Enum Values (Minor 🟡)
*   **Reality (Commit Diff)**:
    ```python
    # backend/app/models/game.py
    endCondition: Literal["all_impostors_eliminated", "max_rounds_reached"]
    ```
*   **Hallucination (Blog Post)**:
    ```python
    endCondition: Literal["AI_ELIMINATED", "HUMANS_ELIMINATED", "TIME_UP_AI_WINS"]
    ```
*   **Impact**: **Minor**. While the values are technically incorrect, they convey the correct *semantic meaning* of the refactor (moving to enums). Since the blog post is for reading/engagement rather than a reproducible technical manual, exact string matches are less critical than the conceptual accuracy.

#### Case B: Invented Frontend Implementation (Minor 🟡)
*   **Reality (Commit Diff)**:
    ```javascript
    // frontend/src/utils/gameMessages.js
    export function getEndReasonMessage(endCondition) { ... }
    ```
*   **Hallucination (Blog Post)**:
    ```javascript
    // Invented function name and Arrow function style
    export const getEndGameMessage = (endCondition) => { ... }
    ```
*   **Impact**: Minor. While syntactically valid JavaScript, it misnames the core utility function introduced in the commit.

### Root Cause Analysis (Common)
The `ContentSynthesizer` defaults to its training data (generic "Best Practice" tutorials) rather than the specific provided context. It prioritizes "Making a good looking post" over "Reporting the actual changes".

### Action Plan
- [x] Tune `ContentSynthesizer` system prompt to strictly forbid inventing code (Critical fix).
- [x] Add instruction: "Respect the synchronous/asynchronous nature of the code."
- [x] Add instruction: "Use variable/collection names from the diff, do not invent simpler ones."
