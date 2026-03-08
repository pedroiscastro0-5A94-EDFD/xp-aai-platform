"""XP AAI Platform — Skill Agents

Six specialized agents orchestrated by Claude Opus 4.6:
1. Portfolio Analyst — calculates returns with code, never LLM-generated numbers
2. Macro Analyst — extracts key projections from XP's macro report
3. Recommendation Engine — drift analysis + CVM-compliant suggestions
4. Letter Writer — generates the monthly client letter in Portuguese
5. Compliance Reviewer — CVM compliance quality gate
6. Doc Formatter — generates professional .docx output
"""

from agents.portfolio_analyst import PortfolioAnalyst
from agents.macro_analyst import MacroAnalyst
from agents.recommendation_engine import RecommendationEngine
from agents.letter_writer import LetterWriter
from agents.compliance_reviewer import ComplianceReviewer
from agents.doc_formatter import DocFormatter

__all__ = [
    "PortfolioAnalyst",
    "MacroAnalyst",
    "RecommendationEngine",
    "LetterWriter",
    "ComplianceReviewer",
    "DocFormatter",
]
