import os
import re
import html
import httpx
from typing import List, Dict, Any

def web_search(query: str) -> List[Dict[str, Any]]:
    """
    Perform web search using Serper.dev API if key is present,
    otherwise fallback to DuckDuckGo/Mock search.
    """
    serper_key = os.getenv("SERPER_API_KEY")
    if serper_key:
        try:
            url = "https://google.serper.dev/search"
            headers = {
                "X-API-KEY": serper_key,
                "Content-Type": "application/json"
            }
            payload = {"q": query}
            response = httpx.post(url, headers=headers, json=payload, timeout=10.0)
            if response.status_code == 200:
                data = response.json()
                results = []
                # Parse organic results
                for item in data.get("organic", [])[:5]:
                    results.append({
                        "title": item.get("title", ""),
                        "link": item.get("link", ""),
                        "snippet": item.get("snippet", "")
                    })
                if results:
                    return results
        except Exception as e:
            print(f"Serper search failed: {e}")

    # Fallback: DuckDuckGo HTML parser using regex
    try:
        url = "https://html.duckduckgo.com/html/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        data = {"q": query}
        response = httpx.post(url, headers=headers, data=data, timeout=8.0)
        if response.status_code == 200:
            # Simple regex parser to find organic results
            # Results are contained in result blocks. Let's find snippets and titles.
            # Typical structure:
            # <a class="result__a" href="[LINK]">[TITLE]</a>
            # <a class="result__snippet" ...>[SNIPPET]</a>
            
            # Find snippets
            snippets_raw = re.findall(r'<a class="result__snippet"[^>]*>(.*?)</a>', response.text, re.DOTALL)
            # Find links and titles
            links_titles_raw = re.findall(r'<a class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>', response.text, re.DOTALL)
            
            results = []
            for i in range(min(len(snippets_raw), len(links_titles_raw), 5)):
                link, title_raw = links_titles_raw[i]
                snippet_raw = snippets_raw[i]
                
                # Clean HTML tags and entities
                title = re.sub(r'<[^>]*>', '', title_raw).strip()
                title = html.unescape(title)
                snippet = re.sub(r'<[^>]*>', '', snippet_raw).strip()
                snippet = html.unescape(snippet)
                
                # Unquote URL if necessary
                import urllib.parse
                parsed_url = urllib.parse.urlparse(link)
                actual_link = link
                if parsed_url.netloc == "duckduckgo.com" and "uddg=" in parsed_url.query:
                    qs = urllib.parse.parse_qs(parsed_url.query)
                    if "uddg" in qs:
                        actual_link = qs["uddg"][0]
                        
                results.append({
                    "title": title,
                    "link": actual_link,
                    "snippet": snippet
                })
                
            if results:
                return results
    except Exception as e:
        print(f"DuckDuckGo fallback search failed: {e}")

    # Simulated fallback if no internet or scraper failed
    return [
        {
            "title": f"Information about '{query}'",
            "link": "https://example.com/search-fallback",
            "snippet": f"This is a simulated fallback search result for the query: '{query}'. The system could not connect to Serper or DuckDuckGo."
        }
    ]

if __name__ == "__main__":
    import sys
    query_str = sys.argv[1] if len(sys.argv) > 1 else "FastAPI web search"
    print(web_search(query_str))
