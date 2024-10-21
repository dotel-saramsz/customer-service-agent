from openai import OpenAI
from config import openai_api_key, openai_org_id, openai_project_id

oai_client = OpenAI(
    api_key=openai_api_key, organization=openai_org_id, project=openai_project_id
)
