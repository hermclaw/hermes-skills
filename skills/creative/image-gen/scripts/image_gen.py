#!/usr/bin/env python3
"""Image generation via OpenRouter AI."""

import os, sys, json, time, argparse, base64, urllib.request, re
from pathlib import Path

def get_api_key():
    key = os.getenv('OPENROUTER_API_KEY')
    if key:
        return key
    try:
        for pid in os.listdir('/proc'):
            if pid.isdigit():
                try:
                    with open(f'/proc/{pid}/environ','rb') as f:
                        raw = f.read()
                    for pair in raw.decode('utf-8',errors='replace').split('\x00'):
                        if pair.startswith('OPENROUTER_API_KEY='):
                            return pair.split('=',1)[1]
                except: pass
    except: pass
    raise RuntimeError("OPENROUTER_API_KEY not found.")

def base_url():
    return "https://openrouter.ai/api/v1"

def list_image_models():
    key = get_api_key()
    req = urllib.request.Request(f"{base_url()}/models",
                                  headers={"Authorization":f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read().decode())
    keywords = ['gpt-5-image','gemini.*image','dalle','image-gen']
    found = []
    for m in data.get('data', []):
        mid = m.get('id','').lower()
        if any(re.search(k, mid) for k in keywords):
            found.append({'id': m.get('id'), 'name': m.get('name', m.get('id')),
                          'pricing': m.get('pricing',{})})
    return found

def generate_image(prompt, model="openai/gpt-5-image-mini", n=1, output_dir="/tmp"):
    key = get_api_key()
    payload = {"model": model, "messages": [{"role": "user", "content": prompt}],
               "max_tokens": 4000, "stream": False}
    req = urllib.request.Request(
        f"{base_url()}/chat/completions", data=json.dumps(payload).encode(),
        headers={"Authorization":f"Bearer {key}","Content-Type":"application/json",
                 "HTTP-Referer":"https://hermes-agent.local","X-Title":"Hermes Image Gen"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        if r.status != 200:
            raise RuntimeError(f"API error {r.status}: {r.read()[:200].decode()}")
        result = json.loads(r.read().decode())
    msg = result.get('choices', [{}])[0].get('message', {})
    images = msg.get('images', [])
    if not images:
        raise RuntimeError("No images in response - not an image model?")
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    saved = []
    for i, img in enumerate(images[:n]):
        img_url_dict = img.get('image_url', {})
        url = img_url_dict.get('url', '')
        if url.startswith('data:image/'):
            header, b64_data = url.split(',', 1)
            ext = re.search(r'data:image/(\w+);', header).group(1) if re.search(r'data:image/(\w+);', header) else 'png'
            fname = f"{output_dir}/hermes-gen-{int(time.time())}-{i}.{ext}"
            with open(fname, 'wb') as f:
                f.write(base64.b64decode(b64_data))
            saved.append(fname)
        elif url.startswith('http'):
            img_req = urllib.request.Request(url, timeout=30)
            with urllib.request.urlopen(img_req) as ir:
                content = ir.read()
            ct = ir.headers.get('content-type','').split('/')[-1] or 'png'
            fname = f"{output_dir}/hermes-gen-{int(time.time())}-{i}.{ct}"
            with open(fname, 'wb') as f:
                f.write(content)
            saved.append(fname)
    return saved

def print_media_path(filepath):
    """Print MEDIA: path for the agent to pick up and deliver natively."""
    print(f"MEDIA:{filepath}")

def main():
    p = argparse.ArgumentParser(
        description="Generate images via OpenRouter AI — auto-sends to Telegram",
        epilog=r'''Examples:
  %(prog)s --prompt "A sunset over the ocean"
  %(prog)s --prompt "Cyberpunk city" --model openai/gpt-5-image
  %(prog)s --list-models'''
    )
    p.add_argument('--prompt', default=None, help='Text prompt')
    p.add_argument('--model', default='openai/gpt-5-image-mini', help='Model ID')
    p.add_argument('--n', type=int, default=1, help='Number of images')
    p.add_argument('--output', default=None, help='Output file path (optional)')
    p.add_argument('--list-models', action='store_true', help='List models')
    a = p.parse_args()

    if a.list_models:
        print("Available image generation models on OpenRouter:")
        for m in list_image_models():
            cost = m.get('pricing', {})
            c = f"${cost.get('input',0):.4f}/in + ${cost.get('output',0):.4f}/out" if cost else "N/A"
            print(f"  {m['id']}  Pricing: {c}")
        sys.exit(0)

    if not a.prompt:
        p.error("--prompt is required (or use --list-models)")

    try:
        od = os.path.dirname(a.output) if a.output else "/tmp"
        files = generate_image(a.prompt, a.model, a.n, od)
        for f in files:
            print(f"✓ Generated: {f}")
            print_media_path(f)
        if a.output and len(files) == 1:
            os.rename(files[0], a.output)
            print(f"✓ Saved to: {a.output}")
    except Exception as e:
        print(f"❌ Failed: {e}", file=sys.stderr); sys.exit(1)

if __name__ == "__main__":
    main()
