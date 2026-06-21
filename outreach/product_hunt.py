import requests
from datetime import date, timedelta
from config import PRODUCT_HUNT_TOKEN, TARGET_TITLES

GRAPHQL_ENDPOINT = "https://api.producthunt.com/v2/api/graphql"

POSTS_QUERY = """
query TopPosts($postedAfter: DateTime!, $postedBefore: DateTime!) {
  posts(order: VOTES, postedAfter: $postedAfter, postedBefore: $postedBefore, first: 10) {
    edges {
      node {
        id
        name
        tagline
        votesCount
        makers {
          id
          name
          username
          headline
          twitterUsername
          websiteUrl
        }
      }
    }
  }
}
"""


def is_target_title(headline: str | None) -> bool:
    if not headline:
        return False
    h = headline.lower()
    return any(t in h for t in TARGET_TITLES)


def get_top_products() -> list[dict]:
    today = date.today()
    variables = {
        "postedAfter":  today.isoformat() + "T00:00:00Z",
        "postedBefore": (today + timedelta(days=1)).isoformat() + "T00:00:00Z",
    }
    headers = {
        "Authorization": f"Bearer {PRODUCT_HUNT_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    resp = requests.post(
        GRAPHQL_ENDPOINT,
        json={"query": POSTS_QUERY, "variables": variables},
        headers=headers,
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()

    if "errors" in data:
        raise RuntimeError(f"Product Hunt API error: {data['errors']}")

    products = []
    for rank, edge in enumerate(data["data"]["posts"]["edges"], start=1):
        node = edge["node"]
        node["rank"] = rank
        products.append(node)
    return products


def filter_target_makers(products: list[dict]) -> list[dict]:
    targets = []
    for product in products:
        for maker in product.get("makers", []):
            if not is_target_title(maker.get("headline")):
                continue
            username = maker.get("username", "")
            targets.append({
                "product_name":    product["name"],
                "product_rank":    product["rank"],
                "maker_name":      maker["name"],
                "maker_username":  username,
                "headline":        maker.get("headline", ""),
                "twitter_username": maker.get("twitterUsername"),
                "website_url":     maker.get("websiteUrl"),
                "ph_profile_url":  f"https://www.producthunt.com/@{username}",
            })
    return targets
