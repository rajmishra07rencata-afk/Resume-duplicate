import json
import re
import time

from openai import OpenAI


class LLMExtractor:

    def __init__(self, api_keys):

        self.api_keys = [
            key.strip()
            for key in api_keys
            if key.strip()
        ]
        self.rotation_count = 0
        self.current_key_index = 0

        self.client = self.create_client()

    # =====================================
    # CREATE CLIENT
    # =====================================

    def create_client(self):

        current_key = self.api_keys[
            self.current_key_index
        ]

        print(
            f"[USING API KEY {self.current_key_index + 1}]"
        )

        return OpenAI(
            api_key=current_key,
            base_url="https://api.groq.com/openai/v1"
        )

    # =====================================
    # SWITCH KEY
    # =====================================

    def switch_key(self):

        self.current_key_index += 1

        if self.current_key_index >= len(self.api_keys):
            self.current_key_index = 0

        self.rotation_count += 1

        # ALL KEYS EXHAUSTED
        if self.rotation_count >= len(self.api_keys):

            print("\nALL API KEYS EXHAUSTED")
            print("Waiting 15 minutes...\n")

            time.sleep(900)

            self.rotation_count = 0

        print(
            f"[SWITCHING TO KEY "
            f"{self.current_key_index + 1}]"
        )

        self.client = self.create_client()

    # =====================================
    # EXTRACT
    # =====================================

    def extract(self, text):

        top_text = "\n".join(
            text.splitlines()[:12]
        )

        import json
import re
import time

from openai import OpenAI


class LLMExtractor:

    def __init__(self, api_keys):

        self.api_keys = [
            key.strip()
            for key in api_keys
            if key.strip()
        ]

        self.current_key_index = 0

        self.client = self.create_client()

    # =====================================
    # CREATE CLIENT
    # =====================================

    def create_client(self):

        current_key = self.api_keys[
            self.current_key_index
        ]

        print(
            f"[USING API KEY {self.current_key_index + 1}]"
        )

        return OpenAI(
            api_key=current_key,
            base_url="https://api.groq.com/openai/v1"
        )

    # =====================================
    # SWITCH KEY
    # =====================================

    def switch_key(self):

        self.current_key_index += 1

        # Cycle back
        if (
            self.current_key_index
            >= len(self.api_keys)
        ):
            self.current_key_index = 0

        print(
            f"[SWITCHING TO KEY "
            f"{self.current_key_index + 1}]"
        )

        self.client = self.create_client()

    # =====================================
    # EXTRACT
    # =====================================

    def extract(self, text):

        top_text = "\n".join(
            text.splitlines()[:80]
        )

        
        prompt = f"""
Extract candidate details.

Return ONLY valid JSON.

Format:
{{
  "candidate_name": "",
  "email": "",
  "phone_number": ""
}}

Rules:
- candidate_name must be the person's real name
- ignore headings and job titles
- prefer top-most name
- use empty string if missing

Resume text:
{text[:1500]}
"""
        # Total retries
        for attempt in range(10):

            try:

                response = (
                    self.client
                    .chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        temperature=0
                    )
                )

                content = (
                    response
                    .choices[0]
                    .message.content
                )

                # Remove markdown wrappers
                content = re.sub(
                    r"^```json|```$",
                    "",
                    content.strip(),
                    flags=re.MULTILINE
                ).strip()

                data = json.loads(content)

                return data

            except Exception as e:

                error_text = str(e).lower()

                print(
                    f"[LLM ERROR] {e}"
                )

                # =================================
                # RATE LIMIT / QUOTA HANDLING
                # =================================

                if (
                    "rate limit" in error_text
                    or "quota" in error_text
                    or "429" in error_text
                ):

                    print(
                        "[LIMIT HIT - SWITCHING KEY]"
                    )

                    self.switch_key()

                    time.sleep(2)

                    continue

                # =================================
                # OTHER TEMP ERRORS
                # =================================

                time.sleep(2)

        # =====================================
        # FINAL FAILSAFE
        # =====================================

       



        # Total retries
        for attempt in range(10):

            try:

                response = (
                    self.client
                    .chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        temperature=0
                    )
                )

                content = (
                    response
                    .choices[0]
                    .message.content
                )

                # Remove markdown wrappers
                content = re.sub(
                    r"^```json|```$",
                    "",
                    content.strip(),
                    flags=re.MULTILINE
                ).strip()

                data = json.loads(content)

                return data

            except Exception as e:

                error_text = str(e).lower()

                print(
                    f"[LLM ERROR] {e}"
                )

                # =================================
                # RATE LIMIT / QUOTA HANDLING
                # =================================

                if (
                    "rate limit" in error_text
                    or "quota" in error_text
                    or "429" in error_text
                ):

                    print(
                        "[LIMIT HIT - SWITCHING KEY]"
                    )

                    self.switch_key()

                    time.sleep(2)

                    continue

                # =================================
                # OTHER TEMP ERRORS
                # =================================

                time.sleep(2)

        # =====================================
        # FINAL FAILSAFE
        # =====================================

        return {
            "candidate_name": "",
            "email": "",
            "phone_number": ""
        }

