import os
from dotenv import load_dotenv

load_dotenv("keys.env")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
CX = os.getenv("GOOGLE_CX_ID")
