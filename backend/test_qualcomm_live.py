import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.ai.qualcomm_client import qualcomm_client

async def main():
    print("Testing Qualcomm AI Client...")
    print(f"API Key Present: {bool(qualcomm_client.api_key)} (length: {len(qualcomm_client.api_key)})")
    print(f"Endpoint: {qualcomm_client.endpoint}")
    print(f"Hardware: {qualcomm_client.target_hardware}")
    print("Sending live test completion request...")
    res = await qualcomm_client.generate_completion(
        system_prompt="You are an autonomous AI security gateway evaluator.",
        user_prompt="Classify risk for: DELETE FROM users WHERE active = 0",
        temperature=0.0
    )
    print(f"Mode: {res.get('mode')}")
    print(f"Telemetry: {res.get('telemetry')}")
    print(f"Text Response: {res.get('text')}")

if __name__ == "__main__":
    asyncio.run(main())
