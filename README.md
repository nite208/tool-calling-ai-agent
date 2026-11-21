# Tool-Calling AI Agent

A Streamlit chat application that runs an agentic loop over the Groq API with
native tool calling. The agent answers general questions directly and delegates
arithmetic, weather lookups, and Wikipedia summaries to dedicated tools.

---

## Architecture

```
app.py                  Streamlit UI: renders chat, owns session state
src/
  config.py             All settings read from environment variables
  logging_setup.py      Configures the standard logging module once
  exceptions.py         Custom exception hierarchy
  llm_client.py         Thin wrapper around the Groq SDK
  agent.py              Agentic loop: sends messages, executes tools, loops
  tools/
    __init__.py         Re-exports registry helpers
    registry.py         TOOL_REGISTRY dict and execute_tool dispatcher
    calculator.py       AST-based arithmetic evaluator
    weather.py          Open-Meteo geocoding and forecast
    wikipedia.py        Wikipedia REST API summary
tests/
  test_calculator.py    Pure-logic tests for the calculator
  test_registry.py      Schema and dispatcher tests for the registry
```

### Agentic loop

1. Build a messages list: system prompt + full conversation history.
2. Call `chat_completion` with the messages and all tool schemas.
3. If the model returns `tool_calls`, execute each one with `execute_tool` and
   append the results as `role: tool` messages.
4. Repeat from step 2 until the model returns a plain text response or the step
   cap (`MAX_AGENT_STEPS`) is reached.

The loop supports parallel tool calls in a single turn and sequential chains
across turns.

---

## Tools

### calculator

Evaluates arithmetic expressions using Python's `ast` module. No `eval` or
`exec` is used. Only numeric literals and the operators `+`, `-`, `*`, `/`,
`//`, `%`, `**` are allowed.

**Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `expression` | string | yes | Arithmetic expression, e.g. `(3 + 5) * 2` |

### get_weather

Resolves a city name with the Open-Meteo Geocoding API, then fetches current
conditions from the Open-Meteo Forecast API. No API key required.

**Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `city` | string | yes | City name, e.g. `London` or `New York` |

**Returns:** condition, temperature, apparent temperature, humidity, wind
speed and direction, precipitation.

### wikipedia_search

Fetches a page summary from the Wikipedia REST API
(`/api/rest_v1/page/summary/{title}`).

**Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `topic` | string | yes | Article title or topic, e.g. `Python programming language` |

---

## Example prompts

**Direct answers (no tools)**

- `Hello, who are you?`
- `What is the capital of France?`
- `Explain the difference between TCP and UDP.`

**Calculator**

- `What is 123 * 456?`
- `Calculate (2 ** 10) - 1`
- `Divide 355 by 113`

**Weather**

- `What is the weather in Tokyo?`
- `Current conditions in Buenos Aires?`

**Wikipedia**

- `Tell me about the Eiffel Tower`
- `Look up the history of the Internet`
- `Who is Alan Turing?`

**Chained / multi-tool**

- `What is the temperature in London and convert it to Fahrenheit?`

---

## Local run steps (Git Bash on Windows)

1. Clone the repository and enter it.

   ```bash
   git clone <repo-url>
   cd tool-calling-ai-agent
   ```

2. Create a virtual environment and activate it.

   ```bash
   python -m venv .venv
   source .venv/Scripts/activate
   ```

3. Install dependencies.

   ```bash
   pip install -r requirements.txt
   ```

4. Copy the example environment file and add your Groq API key.

   ```bash
   cp .env.example .env
   # Open .env and set GROQ_API_KEY=your_actual_key
   ```

5. Run the tests.

   ```bash
   pytest
   ```

6. Start the app.

   ```bash
   streamlit run app.py
   ```

   Open `http://localhost:8501` in your browser.

---

## Streamlit Cloud deployment

1. Push the repository to GitHub.

2. Go to [share.streamlit.io](https://share.streamlit.io) and create a new app
   pointing to `app.py`.

3. In the app settings, open **Secrets** and add each variable from
   `.env.example` using TOML format:

   ```toml
   GROQ_API_KEY = "your_actual_key"
   GROQ_MODEL = "openai/gpt-oss-120b"
   ```

4. Deploy. `src/config.py` reads from `st.secrets` as a fallback, so no
   `.env` file is needed in the cloud.

---

## Design decisions

**Groq SDK with native tool calling.** The `openai/gpt-oss-120b` model
supports reliable parallel tool use.

**AST-based calculator.** Using `ast.parse` with an explicit allowlist of
node types eliminates any risk of arbitrary code execution that `eval` carries.

**Open-Meteo.** Free, no API key required, well-documented REST endpoints for
both geocoding and forecast data.

**Tool registry pattern.** Each tool file exports exactly one `SCHEMA` dict
and one `handle` function. Adding a new tool means creating one file and adding
one entry to `TOOL_REGISTRY` in `registry.py`. Nothing else changes.

**Error isolation.** Every external call is wrapped and raises a typed
exception. The `handle` function in each tool catches that exception and
returns a structured `error: ...` string to the model, which then explains the
problem to the user. The app never crashes on a tool failure.

---

## Known limitations

- Weather data is current conditions only. No forecasts, hourly, or historical
  data are exposed through this tool.
- Wikipedia lookups are English-only and use the exact article title match.
  Ambiguous or misspelled topics may return a 404.
- The calculator supports only basic arithmetic. Functions such as `sqrt`,
  `log`, or trigonometry are not supported.
- Groq free-tier accounts have rate limits. High-traffic usage will produce
  rate-limit errors surfaced to the user.
- The agent loop cap (`MAX_AGENT_STEPS`) prevents infinite loops but may cut
  off complex multi-step tasks if the cap is too low.
- Conversation history is stored in `st.session_state` and is lost on page
  reload.
