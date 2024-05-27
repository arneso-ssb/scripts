import os
from pathlib import Path
from typing import TypedDict

import pandas as pd
import requests
from dotenv import load_dotenv
from datetime import datetime


class ProjParams(TypedDict):  # noqa: D101
    organization: str
    p: int
    ps: int


def fetch_all_pages(
    url: str, headers: dict[str, str], params: ProjParams
) -> list[dict[str, str]]:
    """Fetches all pages of data from a paginated API endpoint.

    Args:
        url: The URL of the API endpoint.
        headers: The headers to be included in the request.
        params: The parameters to be sent with the request.

    Returns:
        A list of dictionaries containing the data from all pages.
    """
    data_list = []
    while True:
        response = requests.get(url, headers=headers, params=params, timeout=10)  # type: ignore
        if response.status_code != 200:
            raise requests.exceptions.HTTPError(
                f"Failed to retrieve data: Status code {response.status_code}"
            )
        data = response.json()
        data_list.extend(data["components"])

        # Check if there is a next page
        if "paging" in data and data["paging"]["total"] > params["p"] * params["ps"]:
            params["p"] += 1
        else:
            break  # No more pages, exit the loop
    return data_list


def main() -> None:
    """The main function."""
    data_dir = Path(__file__).parent.parent.parent / "data"
    data_dir.mkdir(exist_ok=True)

    # Load environment variables from .env file
    load_dotenv()
    api_token = os.getenv("SONAR_TOKEN")
    headers = {"Authorization": f"Bearer {api_token}"}

    base_url = "https://sonarcloud.io/api/projects/search"
    params: ProjParams = {
        "organization": "statisticsnorway",
        "p": 1,  # page
        "ps": 100,  # page-size [0-500]
    }

    projects_data = fetch_all_pages(base_url, headers, params)
    projects_df = pd.DataFrame(projects_data)

    current_date = datetime.now().date()
    projects_df.to_excel(data_dir / f"sc-projects-{current_date}.xlsx", index=False)
    projects_df.to_csv(data_dir / f"sc-projects-{current_date}.csv", index=False)

    print(f"Number of projects: {len(projects_df)}")
    print(projects_df.head()[["key", "lastAnalysisDate"]])


if __name__ == "__main__":
    main()
