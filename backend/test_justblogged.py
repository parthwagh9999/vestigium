import asyncio
import re

async def test():
    import dns.resolver
    import httpx
    
    raw = "[JustBlogged - Free Blogging Platform | Start a Blog in 2 Minutes](https://justblogged.com/)"
    
    # Check if raw input is markdown link
    md_match = re.search(r"\[(.*?)\]\((https?://[^\s)]+)\)", raw)
    if md_match:
        label = md_match.group(1)
        url = md_match.group(2)
        print(f"Extracted markdown -> Label: '{label}', URL: '{url}'")
    else:
        url = raw
        
    domain = url.replace("https://", "").replace("http://", "").split("/")[0]
    print(f"Extracted domain: '{domain}'")
    
    # 1. DNS A record
    try:
        ans = dns.resolver.resolve(domain, 'A')
        print("DNS A:", [str(r) for r in ans])
    except Exception as e:
        print("DNS A Error:", e)
        
    # 2. HTTP
    async with httpx.AsyncClient(verify=False, follow_redirects=True, timeout=10.0) as client:
        try:
            resp = await client.get(f"https://{domain}")
            print(f"HTTP Status: {resp.status_code}, Length: {len(resp.text)}")
        except Exception as e:
            print("HTTP Error:", e)

if __name__ == "__main__":
    asyncio.run(test())
