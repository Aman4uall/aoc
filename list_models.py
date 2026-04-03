import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    os.environ["GEMINI_API_KEY"] = api_key

client = genai.Client(
    vertexai=True,
    project="aocproject-492204",
    location="us-central1"
)

for model in client.models.list():
    print(model.name)
