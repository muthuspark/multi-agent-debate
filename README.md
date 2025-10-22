# Multi-Agent Debate System

A lightweight system that orchestrates debates between two AI agents on any given question, with a third agent acting as judge to determine the most accurate answer. Built with LangGraph and Claude (Anthropic).

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

This project uses [uv](https://github.com/astral-sh/uv) for fast, reliable package management.

### 1. Install uv (if not already installed)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone and Setup

```bash
cd multi-agent-debate
```

### 3. Install Dependencies

```bash
uv sync
```

This will create a virtual environment and install all required packages.

### 4. Configure API Key

Create a `.env` file from the template:

```bash
cp .env.example .env
```

Edit `.env` and add your Anthropic API key:

```
ANTHROPIC_API_KEY=your_actual_api_key_here
```

Get your API key from: https://console.anthropic.com/

## Usage

### Running the Example Script

The easiest way to see the system in action:

```bash
uv run python examples/run_debate.py
```

This will run two example debates and display the full transcripts with judgments.

### Using in Your Own Code

```python
from dotenv import load_dotenv
from src.debate_graph import DebateOrchestrator
from src.models import DebateInput

# Load environment variables
load_dotenv()

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
│   ├── agents.py             # Agent system prompts and formatters
│   └── debate_graph.py       # LangGraph orchestration logic
├── examples/
│   └── run_debate.py         # Example debate runner
├── .env.example              # Environment template
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

### Using Different Claude Models

```python
orchestrator = DebateOrchestrator(model="claude-3-opus-20240229")
```

Available models:
- `claude-3-5-sonnet-20241022` (default, recommended)
- `claude-3-opus-20240229` (most capable, slower)
- `claude-3-haiku-20240307` (fastest, less nuanced)

### Adjusting Temperature

Modify `debate_graph.py`:

```python
self.llm = ChatAnthropic(
    model=self.model,
    api_key=self.api_key,
    temperature=0.7,  # Adjust between 0.0-1.0
)
```

## Limitations

- Text-based reasoning only (no external tool use)
- No real-time fact checking
- Context length limited by underlying model (~200k tokens)
- No persistent memory between separate debates
- Debates complete in ~1-2 minutes depending on complexity

## Performance

- **Typical runtime**: 1-2 minutes per debate
- **Token usage**: ~10k-30k tokens per debate (depending on complexity)
- **Cost estimate**: $0.30-$0.90 per debate with Claude 3.5 Sonnet

## Troubleshooting

### "ANTHROPIC_API_KEY not found"

Make sure you've created a `.env` file with your API key:

```bash
cp .env.example .env
# Edit .env and add your key
```

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
