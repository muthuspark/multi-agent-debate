"""Example script demonstrating the multi-agent debate system."""

import json
from pathlib import Path

# Add parent directory to path to import src
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.debate_graph import DebateOrchestrator
from src.models import DebateInput


def print_debate_output(output):
    """Pretty print the debate output."""
    print("\n" + "=" * 80)
    print("DEBATE TRANSCRIPT")
    print("=" * 80 + "\n")

    current_round = 0
    for msg in output.debate_log:
        if msg.round != current_round:
            current_round = msg.round
            print(f"\n{'─' * 80}")
            print(f"ROUND {current_round}")
            print(f"{'─' * 80}\n")

        print(f"\n{msg.agent}:")
        print(f"{msg.message}\n")

    print("\n" + "=" * 80)
    print("FINAL JUDGMENT")
    print("=" * 80 + "\n")

    print(f"DECISION: {output.final_judgment}\n")
    print(f"REASONING:\n{output.reasoning}\n")
    print(f"CONFIDENCE: {output.confidence:.2f}\n")


def main():
    """Run example debates."""
    # Initialize the debate orchestrator
    print("Initializing debate orchestrator...")
    orchestrator = DebateOrchestrator()

    # Example 1: Nuclear energy and climate change
    # print("\n" + "=" * 80)
    # print("DEBATE 1: Nuclear Energy and Climate Change")
    # print("=" * 80)

    debate1 = DebateInput(
    question="Is blockchain technology essential for the future of secure digital transactions?",
    context="Consider energy usage, alternative security approaches, practical applications, and centralization concerns."
)


    print(f"\nQuestion: {debate1.question}")
    print(f"Context: {debate1.context}")
    print("\nStarting debate... (this may take 1-2 minutes)\n")

    result1 = orchestrator.run_debate(debate1)
    print_debate_output(result1)

    # Save results to JSON
    output_path = Path(__file__).parent / "debate_output.json"
    with open(output_path, "w") as f:
        json.dump(result1.model_dump(), f, indent=2)

    print(f"\nFull output saved to: {output_path}")

    # Example 2: Another debate topic (optional)
    # print("\n\n" + "=" * 80)
    # print("DEBATE 2: Universal Basic Income")
    # print("=" * 80)

    # debate2 = DebateInput(
    #     question="Should governments implement universal basic income?",
    #     context=None  # No additional context
    # )

    # print(f"\nQuestion: {debate2.question}")
    # print("\nStarting debate... (this may take 1-2 minutes)\n")

    # result2 = orchestrator.run_debate(debate2)
    # print_debate_output(result2)


if __name__ == "__main__":
    main()
