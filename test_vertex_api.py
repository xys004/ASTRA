import asyncio
from core.llm_client import ASTRAIntelligence

async def main():
    print("Initializing ASTRA with Vertex AI provider...")
    astra = ASTRAIntelligence(provider="vertexai")
    
    conjecture = "Explain the Alcubierre metric briefly."
    print("\n--- TEST: VERTEX AI CONNECTION ---")
    try:
        response = await astra.generate_conjecture(conjecture)
        print(response)
        print("\nVertex AI connection successful!")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
