import os
import sys
import time
import httpx
from dotenv import load_dotenv

load_dotenv()

def probe():
    api_key = os.getenv("INFERENCE_CLOUD_API_KEY", "")
    endpoint = os.getenv("INFERENCE_CLOUD_ENDPOINT", "https://aisuite.cirrascale.com/apis/v2").rstrip("/")
    model = os.getenv("QUALCOMM_MODEL", "Llama-3.1-8B")
    hardware = os.getenv("QUALCOMM_TARGET_HARDWARE", "Qualcomm Cloud AI 100")

    print("=" * 70)
    print("QUALCOMM CLOUD AI (.env) VERIFICATION PROBE")
    print("=" * 70)
    print(f"1. Target Hardware      : {hardware}")
    print(f"2. Endpoint URL          : {endpoint}")
    print(f"3. Model Name            : {model}")
    print(f"4. API Key               : {api_key[:8]}...{api_key[-4:]} (Total length: {len(api_key)})")

    url = f"{endpoint}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a verification test agent."},
            {"role": "user", "content": "Respond with 'QUALCOMM_ACTIVE' and confirm your model name."}
        ],
        "temperature": 0.0,
        "max_tokens": 50
    }

    print(f"\n5. Sending HTTP POST to: {url}...")
    t0 = time.time()
    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(url, json=payload, headers=headers)
            elapsed = (time.time() - t0) * 1000

            print(f"\n--- HTTP Response Summary ---")
            print(f"HTTP Status Code : {resp.status_code}")
            print(f"Roundtrip Latency: {elapsed:.2f} ms")
            print(f"Response Headers : {dict(resp.headers)}")
            
            if resp.status_code == 200:
                data = resp.json()
                print("\n--- Model Response Payload ---")
                print(f"ID     : {data.get('id')}")
                print(f"Model  : {data.get('model')}")
                print(f"Content: {data['choices'][0]['message']['content'].strip()}")
                print(f"Usage  : {data.get('usage')}")
                print("\n>>> VERDICT: The Qualcomm API Key IS WORKING and ACTIVE on Cirrascale Cloud AI 100!")
            else:
                print(f"\n>>> Error Response Body: {resp.text}")
                print(f"\n>>> VERDICT: HTTP {resp.status_code} - Key or endpoint returned an error.")
    except Exception as e:
        print(f"\n>>> Connection / Network Error: {str(e)}")

if __name__ == "__main__":
    probe()
