from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.arize_api_key = os.getenv("ARIZE_API_KEY")
        self.arize_space_id = os.getenv("ARIZE_SPACE_ID")
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")
        self._validate()

    def _validate(self):
        missing = []
        if not self.openai_api_key:
            missing.append("OPENAI_API_KEY")
        if not self.tavily_api_key:
            missing.append("TAVILY_API_KEY")

        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}. "
                f"Please update your .env file."
            )

settings = Settings()