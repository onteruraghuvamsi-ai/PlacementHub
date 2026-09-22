
import requests


def get_github_organization(org_name):
    url = f"https://api.github.com/orgs/{org_name}"

    try:
        response = requests.get(
            url,
            timeout=5,
            headers={"Accept": "application/vnd.github+json"}
        )

        if response.status_code == 404:
            return {
                "error": "GitHub organization not found"
            }, 404

        response.raise_for_status()
        data = response.json()

        return {
            "name": data.get("name"),
            "login": data.get("login"),
            "description": data.get("description"),
            "public_repositories": data.get("public_repos"),
            "website": data.get("blog"),
            "location": data.get("location"),
            "github_url": data.get("html_url")
        }, 200

    except requests.Timeout:
        return {"error": "GitHub API request timed out"}, 504

    except requests.RequestException:
        return {"error": "Unable to retrieve organization details"}, 502