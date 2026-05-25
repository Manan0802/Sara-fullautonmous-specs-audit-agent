"""
Web search using Parallel AI API.
"""
import os
from parallel import Parallel


def web_search(query: str, additional_queries: list = None, max_chars: int = 5000) -> dict:
    """
    Perform web search using Parallel AI.
    Returns structured results with titles, urls, excerpts.
    """
    try:
        api_key = os.environ.get("PARALLEL_API_KEY", "")
        if not api_key:
            return {
                "query":   query,
                "results": [],
                "count":   0,
                "error":   "PARALLEL_API_KEY not set in environment"
            }

        client = Parallel(api_key=api_key)

        search_queries = [query]
        if additional_queries:
            search_queries += additional_queries

        search = client.beta.search(
            objective=query,
            search_queries=search_queries,
            mode="fast",
            excerpts={"max_chars_per_result": max_chars}
        )

        results = []
        for r in search.results:
            results.append({
                "title":   getattr(r, "title",   ""),
                "url":     getattr(r, "url",     ""),
                "excerpt": getattr(r, "excerpt", str(r)),
            })

        return {
            "query":   query,
            "results": results,
            "count":   len(results)
        }

    except Exception as e:
        return {
            "query":   query,
            "results": [],
            "count":   0,
            "error":   str(e)
        }


if __name__ == "__main__":
    # Quick test
    result = web_search(
        query="Aluminium Profiles specifications India B2B",
        additional_queries=["aluminium profile standard sizes India"]
    )
    print(f"Results: {result['count']}")
    for r in result["results"]:
        print(f"  - {r['title']}: {r['url']}")