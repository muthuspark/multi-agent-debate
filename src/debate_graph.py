"""LangGraph-based debate orchestration system."""

import os
import re
from typing import Dict, Any, TypedDict, Annotated
from operator import add

from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, END

from src.models import DebateState, DebateMessage, DebateInput, DebateOutput, JudgmentResponse
from src.agents import (
    get_debater_1_prompt,
    get_debater_2_prompt,
    get_judge_prompt,
    format_debate_history,
)


class GraphState(TypedDict):
    """State definition for LangGraph."""
    question: str
    context: str | None
    current_round: int
    debate_log: Annotated[list, add]
    agent1_opening: str
    agent2_opening: str
    agent1_rebuttal1: str
    agent2_rebuttal1: str
    agent1_rebuttal2: str
    agent2_rebuttal2: str
    agent1_conclusion: str
    agent2_conclusion: str
    final_judgment: str
    reasoning: str
    confidence: float


class DebateOrchestrator:
    """Orchestrates a multi-agent debate using LangGraph."""

    def __init__(self, api_key: str | None = None, model: str = "claude-3-5-sonnet-20241022"):
        """Initialize the debate orchestrator.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Claude model to use for all agents
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY must be set in environment or passed as argument")

        self.model = model
        self.llm = ChatAnthropic(
            model=self.model,
            api_key=self.api_key,
            temperature=0.7,
        )
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine for debate orchestration."""
        workflow = StateGraph(GraphState)

        # Add nodes for each debate phase
        workflow.add_node("agent1_opening", self._agent1_opening)
        workflow.add_node("agent2_opening", self._agent2_opening)
        workflow.add_node("agent1_rebuttal1", self._agent1_rebuttal1)
        workflow.add_node("agent2_rebuttal1", self._agent2_rebuttal1)
        workflow.add_node("agent1_rebuttal2", self._agent1_rebuttal2)
        workflow.add_node("agent2_rebuttal2", self._agent2_rebuttal2)
        workflow.add_node("agent1_conclusion", self._agent1_conclusion)
        workflow.add_node("agent2_conclusion", self._agent2_conclusion)
        workflow.add_node("judge", self._judge)

        # Define the debate flow
        workflow.set_entry_point("agent1_opening")
        workflow.add_edge("agent1_opening", "agent2_opening")
        workflow.add_edge("agent2_opening", "agent1_rebuttal1")
        workflow.add_edge("agent1_rebuttal1", "agent2_rebuttal1")
        workflow.add_edge("agent2_rebuttal1", "agent1_rebuttal2")
        workflow.add_edge("agent2_rebuttal2", "agent1_conclusion")
        workflow.add_edge("agent1_rebuttal2", "agent2_rebuttal2")
        workflow.add_edge("agent1_conclusion", "agent2_conclusion")
        workflow.add_edge("agent2_conclusion", "judge")
        workflow.add_edge("judge", END)

        return workflow.compile()

    def _add_to_log(self, agent: str, message: str, round: int) -> Dict[str, Any]:
        """Add a message to the debate log."""
        return {"debate_log": [{
            "agent": agent,
            "message": message,
            "round": round
        }]}

    def _agent1_opening(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Agent 1 presents opening argument."""
        history = format_debate_history(state.get("debate_log", []))
        prompt = get_debater_1_prompt(state["question"], state.get("context"), history)

        response = self.llm.invoke(prompt)
        message = response.content

        updates = {
            "agent1_opening": message,
            "current_round": 1,
        }
        updates.update(self._add_to_log("Agent 1 (Analytical)", message, 1))
        return updates

    def _agent2_opening(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Agent 2 presents opening argument."""
        history = format_debate_history(state.get("debate_log", []))
        prompt = get_debater_2_prompt(state["question"], state.get("context"), history)

        response = self.llm.invoke(prompt)
        message = response.content

        updates = {"agent2_opening": message}
        updates.update(self._add_to_log("Agent 2 (Philosophical)", message, 1))
        return updates

    def _agent1_rebuttal1(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Agent 1 first rebuttal."""
        history = format_debate_history(state.get("debate_log", []))
        prompt = get_debater_1_prompt(state["question"], state.get("context"), history)

        response = self.llm.invoke(prompt)
        message = response.content

        updates = {
            "agent1_rebuttal1": message,
            "current_round": 2,
        }
        updates.update(self._add_to_log("Agent 1 (Analytical)", message, 2))
        return updates

    def _agent2_rebuttal1(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Agent 2 first rebuttal."""
        history = format_debate_history(state.get("debate_log", []))
        prompt = get_debater_2_prompt(state["question"], state.get("context"), history)

        response = self.llm.invoke(prompt)
        message = response.content

        updates = {"agent2_rebuttal1": message}
        updates.update(self._add_to_log("Agent 2 (Philosophical)", message, 2))
        return updates

    def _agent1_rebuttal2(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Agent 1 second rebuttal."""
        history = format_debate_history(state.get("debate_log", []))
        prompt = get_debater_1_prompt(state["question"], state.get("context"), history)

        response = self.llm.invoke(prompt)
        message = response.content

        updates = {
            "agent1_rebuttal2": message,
            "current_round": 3,
        }
        updates.update(self._add_to_log("Agent 1 (Analytical)", message, 3))
        return updates

    def _agent2_rebuttal2(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Agent 2 second rebuttal."""
        history = format_debate_history(state.get("debate_log", []))
        prompt = get_debater_2_prompt(state["question"], state.get("context"), history)

        response = self.llm.invoke(prompt)
        message = response.content

        updates = {"agent2_rebuttal2": message}
        updates.update(self._add_to_log("Agent 2 (Philosophical)", message, 3))
        return updates

    def _agent1_conclusion(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Agent 1 presents conclusion."""
        history = format_debate_history(state.get("debate_log", []))
        prompt = get_debater_1_prompt(state["question"], state.get("context"), history)

        response = self.llm.invoke(prompt)
        message = response.content

        updates = {
            "agent1_conclusion": message,
            "current_round": 4,
        }
        updates.update(self._add_to_log("Agent 1 (Analytical)", message, 4))
        return updates

    def _agent2_conclusion(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Agent 2 presents conclusion."""
        history = format_debate_history(state.get("debate_log", []))
        prompt = get_debater_2_prompt(state["question"], state.get("context"), history)

        response = self.llm.invoke(prompt)
        message = response.content

        updates = {
            "agent2_conclusion": message,
            "current_round": 5,
        }
        updates.update(self._add_to_log("Agent 2 (Philosophical)", message, 5))
        return updates

    def _judge(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Judge evaluates the debate and provides final judgment."""
        history = format_debate_history(state.get("debate_log", []))
        prompt = get_judge_prompt(state["question"], state.get("context"), history)

        response = self.llm.invoke(prompt)
        judge_response = response.content

        # Parse the structured response
        judgment_match = re.search(r"JUDGMENT:\s*(.+?)(?=\n\nREASONING:|$)", judge_response, re.DOTALL)
        reasoning_match = re.search(r"REASONING:\s*(.+?)(?=\n\nCONFIDENCE:|$)", judge_response, re.DOTALL)
        confidence_match = re.search(r"CONFIDENCE:\s*(0?\.\d+|1\.0|0|1)", judge_response)

        judgment = judgment_match.group(1).strip() if judgment_match else "Unable to determine"
        reasoning = reasoning_match.group(1).strip() if reasoning_match else judge_response
        confidence = float(confidence_match.group(1)) if confidence_match else 0.5

        return {
            "final_judgment": judgment,
            "reasoning": reasoning,
            "confidence": confidence,
        }

    def run_debate(self, debate_input: DebateInput | Dict[str, Any]) -> DebateOutput:
        """Run a complete debate and return the results.

        Args:
            debate_input: Either a DebateInput model or a dict with 'question' and optional 'context'

        Returns:
            DebateOutput containing the complete debate log and judgment
        """
        # Convert to dict if needed
        if isinstance(debate_input, DebateInput):
            initial_state = debate_input.model_dump()
        else:
            initial_state = debate_input

        # Add required state fields
        initial_state.update({
            "current_round": 0,
            "debate_log": [],
            "agent1_opening": "",
            "agent2_opening": "",
            "agent1_rebuttal1": "",
            "agent2_rebuttal1": "",
            "agent1_rebuttal2": "",
            "agent2_rebuttal2": "",
            "agent1_conclusion": "",
            "agent2_conclusion": "",
            "final_judgment": "",
            "reasoning": "",
            "confidence": 0.0,
        })

        # Run the debate through the graph
        final_state = self.graph.invoke(initial_state)

        # Return structured output
        return DebateOutput(
            debate_log=[DebateMessage(**msg) for msg in final_state["debate_log"]],
            final_judgment=final_state["final_judgment"],
            reasoning=final_state["reasoning"],
            confidence=final_state["confidence"],
        )
