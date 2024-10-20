# load the env variables from .env file
from dotenv import load_dotenv
import os

# Load the environment variables from the .env file
load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
openai_org_id = os.getenv("OPENAI_ORG_ID")
openai_project_id = os.getenv("OPENAI_PROJECT_ID")
