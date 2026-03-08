"""Compliance Reviewer Agent

Reviews the letter for CVM compliance — no direct buy/sell language,
includes disclaimer, no guaranteed returns. Acts as a quality gate.
Uses GPT-4o API.
"""

import os
import re
from openai import OpenAI


SYSTEM_PROMPT = """You are a CVM compliance officer at XP Investimentos.
Review the investment letter below for regulatory compliance issues.

CHECK FOR THESE VIOLATIONS:
1. DIRECT RECOMMENDATIONS: Words like "compre", "venda", "recomendo que compre/venda",
   "deve comprar/vender", "comprar agora", "vender imediatamente"
2. GUARANTEED RETURNS: Phrases implying certainty like "vai render", "certamente",
   "garantido", "com certeza", "retorno garantido", "sem risco"
3. MISSING DISCLAIMER: The letter MUST end with a proper disclaimer about risks
4. MISLEADING COMPARISONS: Unfair benchmark comparisons or cherry-picked data
5. MISSING RISK WARNINGS: Investment letters must acknowledge risks
6. IMPROPER TONE: Overly aggressive, pressuring, or fear-based language

OUTPUT FORMAT:
- PASS/FAIL overall status
- List of specific violations found (with exact quotes)
- Suggested fixes for each violation
- Compliance score (0-100)

Be strict but fair. Minor phrasing issues are warnings, not failures.
Output in English for internal use."""


# Regex patterns for common CVM violations (Portuguese)
VIOLATION_PATTERNS = [
    (r"\b(compre|comprar)\b", "direct_buy", "Direct buy language detected"),
    (r"\b(venda|vender)\b", "direct_sell", "Direct sell language detected"),
    (r"\brecomendo\s+(a\s+)?(compra|venda)\b", "direct_recommendation", "Direct recommendation detected"),
    (r"\b(garantido|garantia\s+de\s+retorno)\b", "guaranteed_return", "Guaranteed return language"),
    (r"\b(sem\s+risco|risco\s+zero)\b", "no_risk", "No-risk language detected"),
    (r"\b(certamente|com\s+certeza)\b", "certainty", "Certainty language detected"),
    (r"\b(vai\s+render|vai\s+valorizar)\b", "future_guarantee", "Future return guarantee"),
    (r"\b(deve\s+comprar|deve\s+vender)\b", "imperative_trade", "Imperative trade instruction"),
]


class ComplianceReviewer:
    """Reviews letters for CVM regulatory compliance."""

    name = "Compliance Reviewer"

    def __init__(self):
        api_key = os.environ.get("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key) if api_key else None

    def run(self, letter_text: str, client_name: str) -> dict:
        """
        Review a letter for CVM compliance.

        Args:
            letter_text: The full letter text to review
            client_name: Client name for reference

        Returns:
            Dict with compliance results, violations, and score
        """
        # --- Rule-based checks (always run, no LLM needed) ---
        violations = []
        warnings = []

        # Check for violation patterns
        for pattern, violation_type, message in VIOLATION_PATTERNS:
            matches = re.findall(pattern, letter_text, re.IGNORECASE)
            if matches:
                # Some of these patterns are OK in context (e.g., "vender" in
                # "não se trata de recomendação de vender"). Use simple heuristics.
                context_ok = self._check_context(letter_text, pattern)
                if not context_ok:
                    violations.append({
                        "type": violation_type,
                        "severity": "high",
                        "message": message,
                        "matches": [str(m) if isinstance(m, str) else str(m[0]) for m in matches[:3]],
                    })

        # Check for disclaimer
        has_disclaimer = any(
            phrase in letter_text.lower()
            for phrase in [
                "não constitui recomendação",
                "rentabilidade passada",
                "envolvem riscos",
                "perda do capital",
                "material informativo",
            ]
        )
        if not has_disclaimer:
            violations.append({
                "type": "missing_disclaimer",
                "severity": "critical",
                "message": "Letter is missing the required risk disclaimer",
                "matches": [],
            })

        # Check for client name personalization
        if client_name.split()[0].lower() not in letter_text.lower():
            warnings.append({
                "type": "missing_personalization",
                "severity": "low",
                "message": f"Letter does not appear to address the client by name ({client_name})",
            })

        # Check for advisor signature
        has_signature = any(
            phrase in letter_text.lower()
            for phrase in ["cnpi", "assessor de investimentos", "atenciosamente"]
        )
        if not has_signature:
            warnings.append({
                "type": "missing_signature",
                "severity": "medium",
                "message": "Letter is missing advisor signature/credentials",
            })

        # --- LLM-based review (if available) ---
        llm_review = None
        if self.client and letter_text:
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    max_tokens=800,
                    temperature=0.1,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {
                            "role": "user",
                            "content": f"Review this investment letter:\n\n{letter_text}",
                        },
                    ],
                )
                llm_review = response.choices[0].message.content
            except Exception:
                llm_review = None

        # --- Calculate compliance score ---
        score = 100
        for v in violations:
            if v["severity"] == "critical":
                score -= 30
            elif v["severity"] == "high":
                score -= 15
            elif v["severity"] == "medium":
                score -= 5
        for w in warnings:
            score -= 2
        score = max(0, min(100, score))

        passed = score >= 70 and not any(v["severity"] == "critical" for v in violations)

        return {
            "agent": self.name,
            "client_name": client_name,
            "passed": passed,
            "score": score,
            "violations": violations,
            "warnings": warnings,
            "llm_review": llm_review,
            "summary": (
                f"{'PASSED' if passed else 'FAILED'} — Score: {score}/100, "
                f"{len(violations)} violation(s), {len(warnings)} warning(s)"
            ),
        }

    def _check_context(self, text: str, pattern: str) -> bool:
        """Check if a pattern match is OK in context (e.g., negated)."""
        # Find matches and check surrounding text
        for match in re.finditer(pattern, text, re.IGNORECASE):
            start = max(0, match.start() - 50)
            context = text[start:match.end() + 50].lower()
            # OK if preceded by negation or CVM-compliant framing
            safe_contexts = [
                "não constitui recomendação de",
                "não se trata de",
                "não significa que deve",
                "avaliar",
                "considerar",
                "pode ser oportuno",
                "pode ser interessante",
            ]
            if any(safe in context for safe in safe_contexts):
                return True
        return False
