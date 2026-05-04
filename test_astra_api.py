import asyncio
from core.llm_client import ASTRAIntelligence
from dotenv import load_dotenv
import os

async def main():
    load_dotenv()
    print(f"Loaded API KEY: {os.environ.get('GEMINI_API_KEY')[:10]}...")
    astra = ASTRAIntelligence(provider="gemini")
    
    conjecture = "Test whether a static spherically symmetric Schwarzschild metric with f(r)=1-2M/r has vanishing Ricci scalar outside r=2M."
    print("\n--- PHASE 2: TRANSLATE TO CODE ---")
    code = await astra.translate_to_code(conjecture)
    print(code)

if __name__ == "__main__":
    asyncio.run(main())
