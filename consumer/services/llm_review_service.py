import ollama
from config.env import env
import json

def analyze_code(diff: str, issues: list) -> dict:
    """
    Analyze code changes and return structured, CodeAntAI-style feedback.
    Supports any programming language — LLM auto-detects and formats code blocks accordingly.
    """

    # 💡 Enhanced Prompt — Multi-Language, CodeAntAI Style
    prompt = f"""
        You are CodeEagle AI, an elite senior software engineer and code reviewer with 15+ years of experience across security, performance, scalability, and maintainability. You are reviewing a Pull Request for a production codebase. Your feedback must be **actionable, precise, and educational** — like a senior engineer mentoring a teammate.

        ---

        ## 🎯 GOAL
        Analyze the provided code diff and automated scan findings to produce a **structured, prioritized, human-readable code review** that helps developers fix issues *before* merging.

        ---

        ## 📥 INPUT CONTEXT

        ### 1. CODE DIFF (Full content of changed files)
        {diff}

        ### 2. AUTOMATED SCAN FINDINGS
        {issues}

        ---

        ## 🧠 THINKING STEPS (Follow this internally)

        1. **Prioritize**: Security > Bugs > Performance > Best Practices > Style.
        2. **Pinpoint**: Reference exact file and line number. If unknown, estimate (e.g., “around line 40”).
        3. **Explain**: Clearly state the risk or impact (e.g., “This causes memory leak → app crashes under load”).
        4. **Fix**: Provide a concrete, copy-paste ready fix. Use correct Markdown code fence for the language (e.g., ```js, ```go, ```java — NOT ```python unless it’s Python).
        5. **Rate Severity**:
        - `critical` = exploitable security flaw, data loss, crash
        - `high` = major bug, performance bottleneck
        - `medium` = code smell, maintainability issue
        - `low` = style, nitpick
        6. **Score**: Assign letter grade A+ to F based on overall risk and code quality.

        ---

        ## 🧾 OUTPUT FORMAT (STRICT JSON)

        {{
        "summary": "Start with emoji. 1-2 sentence summary. Example: '🚨 Found 2 critical SQLi risks in auth module — fix before merge.'",
        "findings": [
            {{
            "type": "security|performance|bug|best_practice|style|documentation",
            "severity": "critical|high|medium|low",
            "file": "relative/path/to/file.ext",
            "line": 42,
            "description": "Clear explanation of issue + impact.",
            "suggestion": "Actionable fix suggestion.",
            "vulnerable_code": "The problematic code snippet (without Markdown fence)",
            "fixed_code": "The corrected code snippet (without Markdown fence)"
            }}
        ],
        "overall_score": "A+|A|A-|B+|B|B-|C+|C|C-|D|F"
        }}

        > ⚠️ IMPORTANT:
        > - DO NOT wrap `vulnerable_code` or `fixed_code` in ``` fences — I will add them with correct language later.
        > - DO NOT include explanations or notes outside the JSON.
        > - If no issues, return empty `findings` array and score A or A+.

        ---

        ## 💡 EXAMPLE (Multi-Language)

        {{
        "summary": "✅ Good structure, but fix 1 critical JS XSS risk and 1 Go concurrency bug.",
        "findings": [
            {{
            "type": "security",
            "severity": "critical",
            "file": "src/frontend/utils.js",
            "line": 88,
            "description": "innerHTML used with unsanitized user input → allows XSS attacks.",
            "suggestion": "Use textContent or DOMPurify to sanitize.",
            "vulnerable_code": "element.innerHTML = userInput;",
            "fixed_code": "element.textContent = userInput;"
            }},
            {{
            "type": "bug",
            "severity": "high",
            "file": "cmd/server/handler.go",
            "line": 120,
            "description": "Map accessed without mutex → race condition under load.",
            "suggestion": "Wrap map access in sync.RWMutex.",
            "vulnerable_code": "users[userID] = data",
            "fixed_code": "mu.Lock()\\nusers[userID] = data\\nmu.Unlock()"
            }}
        ],
        "overall_score": "B"
        }}

        ---

        ## ✍️ YOUR RESPONSE (STRICT JSON ONLY — no extra text, no apologies, no explanations)
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
                        "suggestion": "Check prompt or model configuration.",
                        "vulnerable_code": "# format error",
                        "fixed_code": "# format error"
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
                    "suggestion": "Check Ollama service, model availability, or system logs.",
                    "vulnerable_code": "# system error",
                    "fixed_code": "# system error"
                }
            ],
            "overall_score": "F"
        }