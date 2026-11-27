import requests
from app.config import settings

def search_web(company: str, industry: str, target_market: str, research_goal: str) -> list[dict]:
    """Retrieve source snippets from Tavily. Returns [] when no key is configured."""
    if not settings.tavily_api_key:
        return []
    queries = [
        f"{industry} market size trends {target_market}",
        f"{industry} competitors companies {target_market}",
        f"{industry} customer demand opportunities {target_market}",
        f"{company} company competitors products",
    ]
    collected = []
    seen = set()
    for query in queries:
        try:
            response = requests.post(
            "https://api.tavily.com/search",
            headers={"Authorization": f"Bearer {settings.tavily_api_key}"},
            json={
                "query": query,
                "search_depth": "basic",
                "topic": "general",
                "max_results": 5,
                "chunks_per_source": 2,
                "include_answer": False,
                "include_raw_content": False,
            },
                timeout=25,
            )
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException:
            continue
        for item in payload.get("results", []):
            url = item.get("url", "")
            if not url or url in seen:
                continue
            seen.add(url)
            collected.append({
                "title": item.get("title", "")[:500],
                "url": url[:2000],
                "snippet": item.get("content", "")[:2500],
                "score": item.get("score"),
            })
    return collected[:15]
