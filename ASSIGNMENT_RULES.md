\# Assessment Rules



These rules are mandatory. Read this file fully before writing or changing any code.



\## Scope lock

\- This repository contains exactly one project: PROJECT\_DESCRIPTION

\- Build only what this project requires. No extra features, no authentication, no database servers, no paid services, no unrequested frameworks.

\- Do not use LangChain or LlamaIndex. Use plain Python and official SDKs only.

\- Allowed stack: Python 3.10+, Streamlit, Groq SDK for the LLM, fastembed for embeddings, faiss-cpu for vectors, pypdf for PDFs, requests for HTTP, pytest for tests.

\- If something is ambiguous, ask one short question before coding. Do not guess.

\- If unsure about an API, read its official documentation. Never invent parameters, endpoints, or function names.



\## Code style

\- Clean, readable, production-style Python with type hints on every function.

\- No comments, except where logic is genuinely non-obvious. No docstring essays, no section banners, no decorative text, no emojis.

\- Small single-purpose functions. Maximum about 40 lines per function.

\- Descriptive names. No abbreviations that are not universal.

\- No dead code, no commented-out code, no placeholder TODOs, no unused imports.



\## Architecture for easy debugging

\- One module per responsibility: config, logging setup, exceptions, clients, core logic, UI. The UI file contains no business logic.

\- All settings in one config module, read from environment variables, with st.secrets as a fallback for deployment. No hard-coded keys, URLs, or model names outside config.

\- Custom exception classes in one exceptions module. Each external call is wrapped and raises a specific exception with a clear message.

\- Use the standard logging module. Every module gets its own named logger. Log the operation, key inputs (never secrets), and failures with the full traceback.

\- The UI shows short friendly error messages. The full technical detail goes to the logs.

\- Pure logic functions must be testable without network access.



\## Quality bar

\- Handle empty input, invalid input, network failure, timeouts, and rate limits explicitly.

\- Every HTTP call has a timeout.

\- Pin all dependency versions in requirements.txt.

\- Add a .env.example listing every required variable with no real values.

\- Add a small pytest suite covering the pure logic.



\## Secrets and git

\- Never commit keys or tokens. .env is git-ignored.

\- Commit messages follow the form: type(scope): short description.



\## Workflow

1\. State the plan as a list of files with one line of purpose each. Wait for approval before writing code.

2\. Write code only for the approved plan.

3\. At the end, output the exact commands to install, run, and test locally, as a numbered list.

4\. Stop.



\## README rules

\- Cover: overview, architecture, setup and run steps, design decisions with reasons, known limitations, example usage.

\- Plain, factual writing. No em-dashes, no emojis, no marketing language.

