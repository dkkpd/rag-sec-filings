from dotenv import load_dotenv
from google import genai

load_dotenv()

client=genai.Client()

interaction = client.interactions.create(
    model="gemini-3.7-flash",
    input="Reply with just 'gemini api call is working' and nothing else"
)

print(interaction.output_text)