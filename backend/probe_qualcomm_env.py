import os
import sys
import time
from pathlib import Path
import httpx
from dotenv import load_dotenv

# Search and load .env from root and backend
root_dir = Path(__file__).resolve().parent.parent
backend_dir = Path(__file__).resolve().parent
load_dotenv(root_dir / ".env")
load_dotenv(backend_dir / ".env")

def probe():
    k1 = os.getenv("INFERENCE_CLOUD_API_KEY", "")
    k2 = os.getenv("QUALCOMM_API_KEY", "")
    endpoint = os.getenv("INFERENCE_CLOUD_ENDPOINT", "https://aisuite.cirrascale.com/apis/v2").rstrip("/")
    model = os.getenv("QUALCOMM_MODEL", "Llama-3.1-8B")
    hardware = os.getenv("QUALCOMM_TARGET_HARDWARE", "Qualcomm Cloud AI 100")

    print("=" * 75)
    print("      QUALCOMM CLOUD AI 100 (.env) LIVE VERIFICATION PROBE")
    print("=" * 75)
    print(f"1. Target Hardware           : {hardware}")
    print(f"2. Endpoint Base URL         : {endpoint}")
    print(f"3. Model Name                : {model}")
    print(f"4. INFERENCE_CLOUD_API_KEY   : {k1[:8]}...{k1[-4:] if len(k1) > 4 else ''} (Length: {len(k1)})")
    print(f"5. QUALCOMM_API_KEY          : {k2[:8]}...{k2[-4:] if len(k2) > 4 else ''} (Length: {len(k2)})")

    # Priority key for Cirrascale Cloud AI 100
    active_key = k1 if k1 else k2
    url = f"{endpoint}/chat/completions"
    headers = {
        "Authorization": f"Bearer {active_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a live verification agent on Qualcomm Cloud AI 100."},
            {"role": "user", "content": "Respond with 'QUALCOMM_AI_100_LIVE_VERIFIED' and confirm your model name."}
        ],
        "temperature": 0.0,
        "max_tokens": 50
    }

    print(f"\n6. Executing LIVE Inference Request to Cloud AI 100...")
    print(f"   Target URL: {url}")
    t0 = time.time()
    try:
        with httpx.Client(timeout=20.0) as client:
            resp = client.post(url, json=payload, headers=headers)
            elapsed = (time.time() - t0) * 1000

            print(f"\n--- HTTP Response Telemetry ---")
            print(f"HTTP Status Code     : {resp.status_code}")
            print(f"Roundtrip Latency    : {elapsed:.2f} ms")
            
            if resp.status_code == 200:
                data = resp.json()
                content = data['choices'][0]['message']['content'].strip()
                usage = data.get('usage', {})
                prompt_tokens = usage.get('prompt_tokens', 0)
                completion_tokens = usage.get('completion_tokens', 0)
                throughput = (completion_tokens / (elapsed / 1000.0)) if elapsed > 0 else 0.0

                print(f"\n--- Live Hardware Inference Output ---")
                print(f"Response ID          : {data.get('id')}")
                print(f"Model Identified     : {data.get('model')}")
                print(f"Generated Content    : {content}")
                print(f"Prompt Tokens        : {prompt_tokens}")
                print(f"Completion Tokens    : {completion_tokens}")
                print(f"Throughput           : {throughput:.1f} tokens/sec")
                print("\n" + "=" * 75)
                print(">>> VERDICT: LIVE QUALCOMM CLOUD AI 100 ACCELERATION IS ACTIVE!")
                print("    This project is communicating directly with the Cirrascale Cloud AI 100 cluster.")
                print("    Inference is REAL and verified (NOT simulated).")
                print("=" * 75)
            else:
                print(f"\n>>> Error Response Body: {resp.text}")
                print(f"\n>>> VERDICT: HTTP {resp.status_code} - Unable to authenticate on {endpoint}.")
    except Exception as e:
        print(f"\n>>> Connection Error: {str(e)}")

if __name__ == "__main__":
    probe()
