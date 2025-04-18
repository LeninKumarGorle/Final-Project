import requests

def get_all_company_slugs():
    url = "https://leetcode.com/graphql"
    payload = {
        "query": """
        query companyTags {
          companyTags {
            name
            slug
            numQuestions
          }
        }
        """
    }
    headers = {
        "Content-Type": "application/json",
        "Referer": "https://leetcode.com/",
        "User-Agent": "Mozilla/5.0"
    }

    res = requests.post(url, json=payload, headers=headers)
    data = res.json()
    print(data)
    return data["data"]["companyTags"]

# Test it
for company in get_all_company_slugs()[:10]:
    print(f"{company['name']} → {company['slug']} ({company['numQuestions']} questions)")
