# SupportOps AI Copilot

SupportOps AI Copilot is a portfolio project demonstrating a Retrieval-Augmented Generation (RAG) application for IT support and operations runbooks.

The application retrieves relevant internal documentation, generates an answer using a local LLM, and returns source references through a FastAPI endpoint.

> **Project status:** Local portfolio MVP. The application has working API endpoints and retrieval evaluation, but answer quality is not yet consistently reliable. Do not use it for real operational decisions.

## Features

- Markdown and TXT knowledge ingestion.
- Recursive text chunking with source metadata and chunk identifiers.
- Multilingual E5 embeddings using `passage:` and `query:` prefixes.
- Persistent local Chroma vector store with cosine distance.
- Ollama-based answer generation using `qwen3:4b-instruct`.
- FastAPI endpoints with API-key validation.
- Request IDs and latency telemetry.
- User feedback storage in SQLite.
- Retrieval evaluation against a small labeled dataset.
- Heuristic answer evaluation and automated API tests.

## Architecture

```text
Markdown / TXT runbooks
        |
        v
Document ingestion
        |
        v
Chunking and metadata
        |
        v
Multilingual E5 embeddings
        |
        v
Persistent Chroma vector store

Client
  |
  v
FastAPI /ask
  |
  v
Semantic retrieval (Top-K)
  |
  v
Focus on the source of the top-ranked result
  |
  v
Ollama chat model
  |
  v
Answer + source references

Additional components:
- SQLite feedback storage
- Request IDs and latency logs
- Offline retrieval and answer evaluation
```

The current retrieval policy focuses on chunks from the source returned at the highest rank. This reduces mixing unrelated procedures but can exclude relevant information stored in other documents.

## Requirements

- Python 3.11 recommended.
- Git.
- Ollama installed and running.
- The Ollama model `qwen3:4b-instruct`.
- Internet access for initial Python package and embedding-model downloads.

## Run locally on Windows

Run these commands from the repository root.

### 1. Create a virtual environment

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

If PowerShell blocks activation, run this in the current terminal session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### 2. Configure environment variables

Create a local `.env` file:

```powershell
Copy-Item .env.example .env
```

The example uses a development-only API key:

`change-me-local-only`

Replace this value before any deployment. Never commit `.env` or expose API credentials in a public repository.

### 3. Install the Ollama model

Check the locally available models:

```powershell
ollama list
```

If needed, download the configured model:

```powershell
ollama pull qwen3:4b-instruct
```

Make sure Ollama is running before sending requests to the API.

### 4. Build the knowledge index

```powershell
python -m supportops.ingest
```

This reads supported files in `data/knowledge/`, splits them into chunks, creates embeddings, and rebuilds the local Chroma index.

The first run downloads the embedding model. The index is stored under `storage/chroma/`.

### 5. Start the API

```powershell
uvicorn supportops.api:app --reload --app-dir src
```

Open these URLs in a browser:

- API documentation: http://127.0.0.1:8000/docs
- Health endpoint: http://127.0.0.1:8000/health

The health endpoint checks whether the API process is alive. It does not verify that the LLM or vector store is ready.

### 6. Try the question-answer endpoint

Open a second PowerShell terminal, activate the virtual environment, and run:

```powershell
$headers = @{
    "X-API-Key" = "change-me-local-only"
}

$body = @{
    query = "Apa yang harus dilakukan ketika layanan kritis tidak tersedia untuk banyak pelanggan?"
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri "http://127.0.0.1:8000/ask" `
    -Method Post `
    -Headers $headers `
    -ContentType "application/json" `
    -Body $body |
    ConvertTo-Json -Depth 5
```

The response contains:

- `request_id`
- `answer`
- `sources`
- `latency_ms`

The API returns source references to help users inspect the documents used by the retrieval pipeline.

## API endpoints

| Method | Endpoint    | Purpose                                       | Authentication |
| ------ | ----------- | --------------------------------------------- | -------------- |
| GET    | `/health`   | Liveness check                                | No             |
| POST   | `/ask`      | Retrieve documentation and generate an answer | `X-API-Key`    |
| POST   | `/feedback` | Store a rating and optional comment           | `X-API-Key`    |

## Evaluation

### Unit tests

```powershell
pytest -q
```

The API tests use a fake RAG service and do not need to run the LLM. They validate API behavior, not the correctness of generated answers.

### Retrieval evaluation

```powershell
python -m supportops.evaluate_retrieval
```

The evaluation uses 10 questions and measures whether the expected source appears among the retrieved results.

The latest observed local run achieved:

**Source Hit@4: 10/10 (100%)**

This is a result on a small diagnostic dataset, not proof of production retrieval quality.

### Answer evaluation

```powershell
python -m supportops.evaluate_answers
```

This checks three sample questions using keyword-based completeness rules and forbidden phrases.

The latest observed local run passed 2 of 3 cases. These checks are heuristic: they can miss valid paraphrases and cannot prove factual correctness or faithfulness.

Results can change after modifying the prompt, model, retrieval logic, or evaluation criteria.

## Security and limitations

- The default API key is intended only for local development.
- The application should not be exposed publicly with the example API key.
- API-key authentication is a simple demonstration, not a complete production identity or authorization system.
- Retrieved documents are supplied as evidence, but prompt instructions alone are not a complete defense against prompt injection.
- The LLM can omit important steps or generate unsupported claims.
- The current answer evaluation dataset is small and does not establish production reliability.
- Chroma and SQLite are local stores; they are not managed cloud services.
- The application does not provide a graphical chatbot frontend.
- Request latency depends on the machine, model, and amount of retrieved context.

Use synthetic or non-sensitive documentation for demonstrations. Do not submit confidential company runbooks, customer information, credentials, or production secrets.

## Suggested demonstration

1. Start the API and open `/docs`.
2. Submit a question about an incident-response procedure.
3. Inspect the generated answer and returned source references.
4. Submit valid feedback and confirm that the API saves it.
5. Run the retrieval evaluation and explain what Source Hit@4 measures.
6. Run the answer evaluation and discuss the remaining quality limitations.
7. Run `pytest -q` and explain what the tests cover.

## Future improvements

- Expand the labeled evaluation dataset.
- Improve answer-level evaluation beyond keyword matching.
- Reduce unsupported claims and omissions in generated answers.
- Add stronger retrieval evaluation before introducing reranking.
- Add production-grade authentication, rate limits, and monitoring before any public deployment.
- Consider a separate frontend if an interactive chatbot experience is needed.
