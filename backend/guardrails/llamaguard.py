import os
import re
import httpx
from typing import Tuple, Optional, List

# MLCommons Safety Taxonomy Categories for Llama Guard 3
TAXONOMY = {
    "S1": "Violent Crimes",
    "S2": "Non-Violent Crimes",
    "S3": "Sex-Related Crimes",
    "S4": "Child Sexual Exploitation",
    "S5": "Defamation",
    "S6": "Cyberattacks and Hacking",
    "S7": "CBRN Weapons or Dangerous Materials",
    "S8": "Suicide or Self-Harm",
    "S9": "Cyberattacks (Legacy) or Cyberweapons",
    "S10": "Harassment",
    "S11": "Hate Speech",
    "S12": "Sexual Content and Pornography",
    "S13": "Political / Election Misinformation",
}

# Fallback blocklist keywords
BLOCKLIST = [
    "kill yourself",
    "suicide method",
    "how to make a bomb",
    "how to build a bomb",
    "manufacture explosives",
    "child porn",
    "cp ",
    "hack into",
    "steal password",
    "credit card number",
    "social security number",
]
BLOCK_PATTERNS = [re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE) for term in BLOCKLIST]

class LlamaGuard3:
    def __init__(self) -> None:
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip('/')
        self.model_name = os.getenv("GUARDRAIL_MODEL", "llama-guard3:1b")

    def _keyword_check(self, text: str) -> Tuple[bool, str, Optional[str]]:
        """Screen text against a regex blocklist for obviously unsafe content."""
        for pattern in BLOCK_PATTERNS:
            if pattern.search(text):
                # Fallback maps generally to Violent/Self-Harm (S1/S8) or Cyberattacks (S6)
                code = "S8" if "suicide" in pattern.pattern or "kill" in pattern.pattern else "S1"
                return False, f"Keyword blocklist violation: '{pattern.pattern}'", code
        return True, "Keyword check passed.", None

    def check(self, prompt: str) -> Tuple[bool, str, Optional[str]]:
        """
        Runs Llama Guard 3 check on the prompt. Falls back to keyword checking on failure.
        
        Returns:
            (is_safe, reason, category_code)
        """
        # Formulate Llama Guard 3 prompt instructions
        instruct_prompt = (
            f"[INST] Task: Check if there is unsafe content in 'User' messages in conversations "
            f"according to our safety policy with the categories described below.\n\n"
            f"S1: Violent Crimes. S2: Non-Violent Crimes. S3: Sex-Related Crimes. "
            f"S4: Child Sexual Exploitation. S5: Defamation. S6: Cyberattacks and Hacking. "
            f"S7: CBRN Weapons. S8: Suicide or Self-Harm. S10: Harassment. S11: Hate Speech. "
            f"S12: Sexual Content. S13: Political/Election Content.\n\n"
            f"Provide your safety assessment for only the last User message in the conversation:\n"
            f"- First line must be either 'safe' or 'unsafe'.\n"
            f"- If unsafe, a second line must include a comma-separated list of violated category codes.\n\n"
            f"Conversation:\nUser: {prompt}\n\nOutput: [/INST]"
        )

        payload = {
            "model": self.model_name,
            "prompt": instruct_prompt,
            "stream": False,
            "options": {
                "temperature": 0.0  # Deterministic safety checking
            }
        }

        try:
            resp = httpx.post(f"{self.ollama_url}/api/generate", json=payload, timeout=2.0)
            if resp.status_code != 200:
                raise Exception(f"Ollama returned HTTP {resp.status_code}")
                
            result_text = resp.json().get("response", "").strip()
            lines = [line.strip().lower() for line in result_text.split('\n') if line.strip()]
            
            if not lines:
                return True, "Empty guardrail response, assumed safe.", None
                
            assessment = lines[0]
            if "unsafe" in assessment:
                violated_codes = []
                if len(lines) > 1:
                    # Parse codes: S1, S2 etc.
                    violated_codes = [c.strip().upper() for c in lines[1].replace(',', ' ').split() if c.strip()]
                
                explanation = "Blocked by safety filter."
                code = None
                if violated_codes:
                    code = violated_codes[0]
                    category_desc = TAXONOMY.get(code, "Unknown policy violation")
                    explanation = f"Blocked: unsafe content detected under category {code} ({category_desc})."
                
                return False, explanation, code
                
            return True, "Llama Guard 3: safe.", None

        except Exception as e:
            # Fallback to local keyword check on failure
            safe, reason, code = self._keyword_check(prompt)
            if not safe:
                return False, f"Fallback check: {reason}", code
            return True, f"Llama Guard 3 offline; fallback keyword check passed. (Details: {e})", None
