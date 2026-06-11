"""
Intent router — determines which skill should handle user input.

Uses a two-phase strategy:
1. Keyword matching (fast, free — no API call)
2. LLM-based routing (fallback for ambiguous cases)

The router dynamically adapts to whatever skills are registered.
No hardcoded skill names.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from skills.registry import SkillRegistry


# Default keyword match threshold: if a skill scores >= this,
# skip the LLM routing call and use it directly.
DEFAULT_KEYWORD_THRESHOLD = 0.25


class Router:
    """Routes user input to the most appropriate skill.

    Strategy (two-phase):
    1. Keyword matching: iterate all registered skills, compute
       match_score() for each. If one skill clearly dominates
       (score >= threshold), route to it directly — zero API cost.
    2. LLM routing: if no skill matched clearly, send a dynamically
       generated prompt to the LLM listing all available skills,
       and let it decide. Falls back to 'chat' on any error.
    """

    def __init__(
        self,
        keyword_threshold: float = DEFAULT_KEYWORD_THRESHOLD,
    ):
        self.keyword_threshold = keyword_threshold
        self._client = None  # Set lazily by Agent

    def set_client(self, client) -> None:
        """Inject the OpenAI-compatible client for LLM routing."""
        self._client = client

    def route(
        self,
        user_input: str,
        skill_registry: "SkillRegistry",
        model: str = "",
    ) -> str:
        """Determine the best skill for the given user input.

        Args:
            user_input: The raw user input text.
            skill_registry: The SkillRegistry with all available skills.
            model: Model name to use for LLM routing.

        Returns:
            The name of the best-matching skill (guaranteed to exist).
        """
        all_skills = skill_registry.list_skills()

        if not all_skills:
            return "chat"

        # ── Phase 1: Keyword matching ────────────────────────
        scores: dict[str, float] = {}
        for skill in all_skills:
            score = skill.match_score(user_input)
            if score > 0:
                scores[skill.name] = score

        if scores:
            best_skill = max(scores, key=scores.get)
            best_score = scores[best_skill]
            if best_score >= self.keyword_threshold:
                print(f"  [Router] Keyword match → {best_skill} (score={best_score:.2f})")
                return best_skill

        # ── Phase 2: LLM routing ─────────────────────────────
        print(f"  [Router] Keyword scores: {scores if scores else 'none'}")
        print(f"  [Router] Falling back to LLM routing...")

        llm_result = self._llm_route(user_input, all_skills, model)

        # Validate against known skills
        known_names = skill_registry.get_skill_names()
        if llm_result in known_names:
            print(f"  [Router] LLM → {llm_result}")
            return llm_result

        # If LLM returned something unrecognized, try fuzzy matching
        for name in known_names:
            if name in llm_result:
                print(f"  [Router] LLM fuzzy match → {name}")
                return name

        # Safe fallback
        print(f"  [Router] LLM returned '{llm_result}', falling back to chat")
        return "chat"

    def _llm_route(
        self,
        user_input: str,
        skills: list,
        model: str,
    ) -> str:
        """Use LLM to classify which skill fits best."""
        if self._client is None:
            return "chat"

        skill_list = self._build_skill_list(skills)

        prompt = f"""你是 Agent 路由器。根据用户输入选择最合适的技能。

可用技能：
{skill_list}

规则：
- 只返回技能名称，不要解释
- 如果用户在进行一般对话，返回 chat
- 如果没有任何技能匹配，返回 chat

用户输入：
{user_input}

返回技能名："""

        try:
            response = self._client.chat.completions.create(
                model=model or "deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
            )
            result = response.choices[0].message.content.strip().lower()
        except Exception as e:
            print(f"  [Router] LLM routing error: {e}")
            return "chat"

        return result

    @staticmethod
    def _build_skill_list(skills: list) -> str:
        """Build a human-readable skill list for the LLM prompt."""
        lines = []
        for skill in skills:
            keywords_str = ", ".join(skill.keywords[:8]) if skill.keywords else "无"
            lines.append(
                f"• {skill.name} — {skill.description}\n"
                f"  触发词: {keywords_str}"
            )
        return "\n".join(lines)
