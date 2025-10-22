"""Data models for the multi-agent debate system."""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class DebateMessage(BaseModel):
    """A single message in the debate."""
    agent: str
    message: str
    round: int


class DebateInput(BaseModel):
    """Input structure for initiating a debate."""
    question: str
    context: Optional[str] = None


class DebateOutput(BaseModel):
    """Output structure containing the complete debate results."""
    debate_log: List[DebateMessage]
    final_judgment: str
    reasoning: str
    confidence: float = Field(ge=0.0, le=1.0)


class DebateState(BaseModel):
    """State object that tracks the debate flow through the graph."""
    # Input
    question: str
    context: Optional[str] = None

    # Debate tracking
    current_round: int = 0
    debate_log: List[DebateMessage] = Field(default_factory=list)

    # Agent responses
    agent1_opening: str = ""
    agent2_opening: str = ""
    agent1_rebuttal1: str = ""
    agent2_rebuttal1: str = ""
    agent1_rebuttal2: str = ""
    agent2_rebuttal2: str = ""
    agent1_conclusion: str = ""
    agent2_conclusion: str = ""

    # Final judgment
    final_judgment: str = ""
    reasoning: str = ""
    confidence: float = 0.0

    class Config:
        """Pydantic config."""
        arbitrary_types_allowed = True


class JudgmentResponse(BaseModel):
    """Structured response from the judge."""
    judgment: str = Field(description="The judge's final answer to the debate question")
    reasoning: str = Field(description="Detailed reasoning for the judgment")
    confidence: float = Field(description="Confidence score between 0 and 1", ge=0.0, le=1.0)
