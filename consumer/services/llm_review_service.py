import ollama
from config.env import env
import json

def analyze_code(diff: str, issues: list) -> dict:
    """
    Analyze code changes and return structured, CodeAntAI-style feedback.
    AST analysis is temporarily disabled — analysis based on diff + scan findings only.
    """

    # 💡 Enhanced Prompt — CodeAntAI Style (AST-Free)
    prompt = f"""
        You are CodeEagle AI, an elite senior software engineer and code reviewer with 15+ years of experience across security, performance, scalability, and maintainability. You are reviewing a Pull Request for a production codebase. Your feedback must be **actionable, precise, and educational** — like a senior engineer mentoring a teammate.

        ---

        ## 🎯 GOAL
        Analyze the provided code diff and automated scan findings to produce a **structured, prioritized, human-readable code review** that helps developers fix issues *before* merging.

        ---

        ## 📥 INPUT CONTEXT

        ### 1. CODE DIFF 
        {diff}

        ### 2. AUTOMATED SCAN FINDINGS (e.g., linters, scanners, static analyzers)
        {issues}

        ---

        ## 🧠 THINKING STEPS (Follow this internally)

        1. **Prioritize**: Security > Bugs > Performance > Best Practices > Style.
        2. **Pinpoint**: Always reference exact file and line number if possible. If line is unknown, say "near top/middle/end of file".
        3. **Explain**: Why is this an issue? What’s the risk?
        4. **Fix**: Provide a concrete code example or pattern to fix it. Use ```diff or ```python blocks.
        5. **Rate**: Assign severity accurately:
        - `critical` = exploitable security flaw, data loss, crash
        - `high` = major bug, performance bottleneck, incorrect logic
        - `medium` = code smell, maintainability issue, minor bug
        - `low` = style, nitpick, optional improvement
        6. **Score**: Assign letter grade A+ to F based on overall code quality and risk.

        ---

        ## 🧾 OUTPUT FORMAT (STRICT JSON)

        {{
        "summary": "1-2 sentence executive summary for the PR author. Start with emoji. Example: '🚨 Found 2 critical SQL injection risks — fix before merge.'",
        "findings": [
            {{
            "type": "security|performance|bug|best_practice|style|documentation",
            "severity": "critical|high|medium|low",
            "file": "relative/path/to/file.py",
            "line": line_number(like 42),
            "description": "Clear, concise explanation of the issue. Mention impact.",
            "suggestion": "Actionable fix with code example. Use Markdown code blocks if helpful."
            }}
        ],
        "overall_score": "A+|A|A-|B+|B|B-|C+|C|C-|D|F"
        }}

        ---

        ## 🚫 RULES

        - NEVER say “I think”, “maybe”, or “possibly” — be confident and authoritative.
        - NEVER omit line numbers unless truly impossible.
        - NEVER return invalid JSON.
        - If no issues found, return empty `findings` array and high score (A or A+).
        - Use professional but friendly tone — you’re helping, not scolding.

        ---

        ## 💡 EXAMPLE (for inspiration)

        {{
        "summary": "✅ Solid PR with minor improvements needed. Fix 1 security issue and 2 best practices.",
        "findings": [
            {{
            "type": "security",
            "severity": "critical",
            "file": "src/auth/login.py",
            "line": 28,
            "description": "Raw user input concatenated into SQL query — allows SQL injection. Attacker could drop tables or steal data.",
            "suggestion": "Use parameterized queries immediately:\\n```python\\n# ❌ Vulnerable\\nquery = f\\\"SELECT * FROM users WHERE email = '{{email}}'\\\"\\n\\n# ✅ Fixed\\ncursor.execute(\\\"SELECT * FROM users WHERE email = %s\\\", (email,))\\n```"
            }},
            {{
            "type": "best_practice",
            "severity": "medium",
            "file": "src/utils/cache.py",
            "line": 89,
            "description": "Missing error handling around Redis call — could crash app if Redis is down.",
            "suggestion": "Wrap in try-except:\\n```python\\ntry:\\n    cache.set(key, value)\\nexcept RedisError as e:\\n    logger.warning(\\\"Cache set failed\\\", exc_info=True)\\n    # fallback to db or default\\n```"
            }}
        ],
        "overall_score": "B+"
        }}

        ---

        ## ✍️ YOUR RESPONSE (STRICT JSON ONLY — no extra text, no apologies, no explanations outside JSON):
        REMEMBER: Respond ONLY with valid JSON. No extra text before or after.
        """

    try:
        response = ollama.generate(
            model=env.OLLAMA_MODEL,
            prompt=prompt,
            format="json",
            options={
                "temperature": 0.3,
                "top_p": 0.9,
                "num_ctx": 8192
            }
        )

        try:
            result = json.loads(response["response"])
            # Ensure minimal structure
            result.setdefault("summary", "Code review completed.")
            result.setdefault("findings", [])
            result.setdefault("overall_score", "B")
            return result

        except (json.JSONDecodeError, ValueError, KeyError):
            return {
                "summary": "⚠️ Code review completed — model response format invalid",
                "findings": [
                    {
                        "type": "system",
                        "severity": "medium",
                        "file": "unknown",
                        "line": 0,
                        "description": "Model failed to format response correctly.",
                        "suggestion": "Check prompt or model configuration."
                    }
                ],
                "overall_score": "C"
            }

    except Exception as e:
        return {
            "summary": "❌ System error during code analysis",
            "findings": [
                {
                    "type": "system",
                    "severity": "high",
                    "file": "system",
                    "line": 0,
                    "description": f"Failed to analyze code: {str(e)}",
                    "suggestion": "Check Ollama service, model availability, or system logs."
                }
            ],
            "overall_score": "F"
        }