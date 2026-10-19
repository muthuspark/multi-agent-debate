# Multi-Agent Debate System

A lightweight system that orchestrates debates between two AI agents on any given question, with a third agent acting as judge to determine the most accurate answer. Built with LangGraph and the locally installed Codex CLI, using its saved ChatGPT sign-in.

## Concept

Multi-agent debate systems leverage adversarial collaboration to improve reasoning quality and reduce AI hallucinations. The core idea is that by having multiple AI agents argue different perspectives on a question, weaknesses in individual arguments get exposed through critique, while stronger reasoning emerges through iterative refinement.

This approach draws from research showing that debate between LLMs can:
- **Reduce factual errors** by surfacing contradictions and forcing agents to defend claims
- **Improve reasoning depth** through multiple rounds of critique and response
- **Mitigate individual biases** by incorporating diverse reasoning styles
- **Increase transparency** by making the reasoning process explicit and traceable

### Practical Applications

Multi-agent debate systems are particularly valuable in domains requiring:

- **Decision Support**: Complex business decisions, policy analysis, or strategic planning where multiple valid perspectives exist
- **Research Analysis**: Evaluating competing hypotheses, assessing scientific claims, or synthesizing contradictory evidence
- **Content Verification**: Fact-checking, claim validation, and detecting logical fallacies in arguments
- **Educational Tools**: Teaching critical thinking, exploring complex topics from multiple angles, or generating balanced study materials
- **Risk Assessment**: Identifying potential failure modes by having agents argue for and against proposed solutions
- **Creative Ideation**: Generating and refining ideas through constructive criticism and iteration
- **Legal/Ethical Analysis**: Examining arguments from different ethical frameworks or legal perspectives

The system works best for questions with nuance, where multiple valid approaches exist, rather than simple factual lookups with single correct answers.

## Features

- **Two Debater Agents** with distinct reasoning approaches:
  - **Agent 1**: Analytical and data-driven (focuses on empirical evidence and practical outcomes)
  - **Agent 2**: Philosophical and ethical (considers broader implications and values)
- **Judge Agent**: Impartial evaluator that assesses arguments and provides reasoned judgment
- **Structured Debate Flow**: Opening arguments → Rebuttals (2 rounds) → Conclusions → Judgment
- **Clean JSON Output**: Structured debate logs with confidence scores

## Installation

Requires Python 3.11+, [uv](https://github.com/astral-sh/uv), and an authenticated Codex CLI with access to a supported model.

### 1. Install uv (if not already installed)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Open your local checkout

```bash
cd multi-agent-debate
```

### 3. Install Dependencies

```bash
uv sync
```

This will create a virtual environment and install all required packages.

### 4. Install Codex CLI and sign in with ChatGPT

On macOS or Linux, use the [official Codex CLI installer](https://learn.chatgpt.com/docs/codex/cli):

```bash
curl -fsSL https://chatgpt.com/codex/install.sh | sh
codex --version
codex login
codex login status
```

Complete the browser sign-in with your ChatGPT account. Confirm that `codex login status` reports ChatGPT authentication before running a debate. For Windows and other installation options, follow the official CLI guide above.

Codex manages and reuses its saved authentication; this project does not require an API key, `.env` file, or dotenv loading. Use the same OS user and CLI environment for sign-in and Python execution. Check status through the CLI without opening or copying credential files. See [official authentication guidance](https://learn.chatgpt.com/docs/auth) for account and workspace requirements.

## Usage

### Running the Example Script

The easiest way to see the system in action:

```bash
uv run python examples/run_debate.py
```

This runs one blockchain debate: eight argument turns and one judgment (nine sequential Codex CLI calls). It prints the transcript and judgment, then writes `examples/debate_output.json`, replacing that file if it exists. Use the library example below if you only want results in memory. Live runs consume your Codex usage allowance; duration and usage vary by model, question, and service availability.

### Using in Your Own Code

Save this as `my_debate.py` in the project root and run `uv run python my_debate.py` after signing in. This uses the model configured in Codex CLI and keeps results in memory.

```python
from src.debate_graph import DebateOrchestrator
from src.models import DebateInput

# Initialize orchestrator
orchestrator = DebateOrchestrator()

# Create a debate
debate = DebateInput(
    question="Is nuclear energy a good solution to climate change?",
    context="Consider safety, cost, timeline, and alternatives."
)

# Run the debate
result = orchestrator.run_debate(debate)

# Access results
print(f"Judgment: {result.final_judgment}")
print(f"Confidence: {result.confidence}")

# Iterate through debate log
for msg in result.debate_log:
    print(f"Round {msg.round} - {msg.agent}: {msg.message}")
```

## Project Structure

```
multi-agent-debate/
├── src/
│   ├── __init__.py           # Package exports
│   ├── models.py             # Pydantic models for data structures
│   ├── codex_cli.py          # Noninteractive Codex CLI adapter
│   ├── agents.py             # Agent system prompts and formatters
│   └── debate_graph.py       # LangGraph orchestration logic
├── examples/
│   └── run_debate.py         # Example debate runner
├── tests/                    # Offline fake-CLI verification
├── pyproject.toml            # Project dependencies
└── README.md                 # This file
```

## Debate Flow

1. **Opening Arguments** (Round 1)
   - Agent 1 presents initial position
   - Agent 2 presents initial position

2. **Rebuttal Phase** (Rounds 2-3)
   - Each agent responds to opposing arguments twice
   - Agents build upon their previous arguments

3. **Conclusions** (Round 4)
   - Each agent provides final summary

4. **Judgment** (Round 5)
   - Judge evaluates all arguments
   - Provides final answer with reasoning and confidence

## Output Format

```json
{
  "debate_log": [
    {
      "agent": "Agent 1 (Analytical)",
      "message": "...",
      "round": 1
    },
    ...
  ],
  "final_judgment": "Based on the arguments...",
  "reasoning": "The judge's detailed reasoning...",
  "confidence": 0.85
}
```

## Configuration

### Model and executable overrides

`DebateOrchestrator()` resolves `codex` on `PATH` and leaves model selection to Codex CLI. The library accepts two optional keyword arguments:

- `model`: a Codex model identifier available to your account, passed to each CLI call as `--model`. Omit it (or use `None`) to retain CLI configuration.
- `codex_executable`: an executable name on `PATH` or a full path to the Codex binary. Default: `"codex"`. Pass the path alone, without shell quotes or additional flags.

For an explicit override, set `DEBATE_MODEL` to a model your Codex account supports. Optionally set `DEBATE_CODEX_EXECUTABLE` to your installed binary's full path. These are example variables read by the snippet, not built-in project settings. Save as `configured_debate.py` in the project root, then run `uv run python configured_debate.py`:

```python
import os
from src.debate_graph import DebateOrchestrator
from src.models import DebateInput

orchestrator = DebateOrchestrator(
    model=os.environ["DEBATE_MODEL"],
    codex_executable=os.environ.get("DEBATE_CODEX_EXECUTABLE", "codex"),
)
result = orchestrator.run_debate(DebateInput(
    question="Should cities invest in more public transport?",
    context="Consider accessibility, emissions, and budget constraints.",
))
print(result.model_dump_json(indent=2))
```

The wrapper does not expose a temperature option. It sends prompts on stdin using `codex exec --sandbox read-only --skip-git-repo-check --output-last-message ... -` and reads the final assistant message rather than CLI progress output.

## Limitations

- Text-based reasoning only (no external tool use)
- No real-time fact checking
- Context length depends on the selected Codex model
- No persistent memory between separate debates
- Judgment and confidence are generated assessments, not independently verified facts

## Troubleshooting

### Codex executable not found (`FileNotFoundError`)

Run `codex --version` in the same terminal as Python. If it is unavailable, install the CLI using the instructions above and ensure it is on `PATH`. For a nonstandard installation, set `codex_executable` to the full binary path as shown in Configuration.

### Sign-in or CLI failure (`CalledProcessError`)

Run `codex login status` in the same user environment. If signed out, run `codex login` and complete ChatGPT sign-in. If status shows another authentication method, follow the [official authentication guide](https://learn.chatgpt.com/docs/auth) to select ChatGPT sign-in. The application does not prompt for authentication during a debate.

For headless login, consult the guide's device-code instructions and account requirements. Do not inspect or copy credential files to diagnose sign-in.

The wrapper suppresses CLI diagnostics, so a nonzero exit alone does not identify the cause. Confirm model access and account usage limits in Codex; retry without a `model` override if it is unavailable. If needed, run `codex` interactively to inspect its reported issue; sending a prompt there consumes usage.

### Timeout or missing final assistant message

Each CLI call has a 300-second timeout. A timeout raises `subprocess.TimeoutExpired`; an empty or missing final message raises `ValueError`. The debate stops rather than using CLI progress text as an argument. Check CLI installation/version, sign-in status, model availability, and connectivity before retrying.

### Import errors

Ensure you're using `uv run` or have activated the virtual environment:

```bash
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate  # Windows
```

### Module not found

Make sure you're running from the project root directory:

```bash
cd /path/to/multi-agent-debate
uv run python examples/run_debate.py
```

## Contributing

Feel free to open issues or submit pull requests for improvements!

## License

MIT
