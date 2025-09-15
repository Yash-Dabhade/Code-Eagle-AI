import os
from dotenv import load_dotenv

class Environment:
    def __init__(self):
        load_dotenv()
        
        self.RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
        self.RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
        self.RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "guest")
        self.GITHUB_APP_ID=os.getenv("GITHUB_APP_ID")
        self.GITHUB_APP_PRIVATE_KEY_BASE64=os.getenv("GITHUB_APP_PRIVATE_KEY_BASE64")
        self.GITHUB_APP_INSTALLATION_ID=os.getenv("GITHUB_APP_INSTALLATION_ID")
        self.OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen-coder-2.5:7b")

env=Environment()