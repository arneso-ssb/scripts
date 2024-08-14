import os
from datetime import datetime
from pathlib import Path
from typing import TypedDict

import pandas as pd
import requests
from dotenv import load_dotenv
from tenacity import retry
from tenacity import retry_if_exception_type
from tenacity import stop_after_attempt
from tenacity import wait_exponential

projects_url = "https://sonarcloud.io/api/projects/search"
metrics_url = "https://sonarcloud.io/api/metrics/search"
measures_url = "https://sonarcloud.io/api/measures/component"


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


def get_selected_projects(file: Path) -> list[str]:
    with file.open("r") as f:
        projects = [line.strip() for line in f.readlines()]
    return projects


def get_all_projects(
    data_dir: Path, headers: dict[str, str], params: ProjParams
) -> pd.DataFrame:
    projects_data = fetch_all_pages(projects_url, headers, params)
    projects_df = pd.DataFrame(projects_data)
    save_project_keys(data_dir, projects_df)

    current_date = datetime.now().date()
    projects_df.to_excel(data_dir / f"sc-projects-{current_date}.xlsx", index=False)
    projects_df.to_csv(data_dir / f"sc-projects-{current_date}.csv", index=False)

    print(f"Number of projects: {len(projects_df)}")
    # print(projects_df.head()[["key", "lastAnalysisDate"]])
    return pd.DataFrame(projects_data)


def save_project_keys(data_dir: Path, df: pd.DataFrame) -> None:
    current_date = datetime.now().date()
    if components := sorted(df["key"].tolist()):
        with open(
            data_dir / f"components-{current_date}.txt", "w", encoding="utf-8"
        ) as file:
            for item in components:
                file.write(f"{item}\n")


def get_and_save_metrics(data_dir: Path, headers: dict[str, str]) -> None:
    # TODO: Add implementation
    params = {"p": 1, "ps": 500}


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(requests.exceptions.RequestException),
)
def get_project_measures(project: str, headers: dict[str, str]) -> dict[str, str]:
    metric_keys = (
        "ncloc,"
        "functions,"
        "classes,"
        "files,"
        "coverage,"
        "duplicated_lines_density,"
        "complexity,"
        "tests,"
        "alert_status,"
        "violations,"
        "blocker_violations,"
        "critical_violations,"
        "info_violations,"
        "major_violations,"
        "minor_violations,"
        "code_smells,"
        "maintainability_issues,"
        "sqale_index,"
        "sqale_rating,"
        "bugs,"
        "reliability_issues,"
        "reliability_rating,"
        "vulnerabilities,"
        "security_issues,"
        "security_rating,"
    )
    params = {
        "component": project,
        "metricKeys": metric_keys,
    }

    try:
        response = requests.get(measures_url, headers=headers, params=params, timeout=10)  # type: ignore
        response.raise_for_status()  # Raises HTTPError for bad responses
    except requests.exceptions.HTTPError as e:
        if e.response.status_code != 429:
            raise requests.exceptions.HTTPError(
                f"Failed to retrieve data: Status code {e.response.status_code}"
            ) from e

        print("Rate limit exceeded. Retrying...")
        raise requests.exceptions.RequestException("Rate limit exceeded") from e

    data = response.json()
    measures = data["component"]["measures"]
    return {"key": project} | {item["metric"]: item["value"] for item in measures}


def get_all_project_measures(headers: dict[str, str]) -> pd.DataFrame:
    projects = get_selected_projects(Path("reportprojects.txt"))
    projects_measures = []

    for idx, project in enumerate(projects, start=1):
        print(f"Getting data for [{idx}/{len(projects)}] {project}...")
        projects_measures.append(get_project_measures(project, headers))
    return pd.DataFrame(projects_measures)


def main() -> None:
    """The main function."""
    data_dir = Path(__file__).parent.parent.parent / "data"
    data_dir.mkdir(exist_ok=True)

    # Load environment variables from .env file
    load_dotenv()
    api_token = os.getenv("SONAR_TOKEN")
    headers = {"Authorization": f"Bearer {api_token}"}

    project_params: ProjParams = {
        "organization": "statisticsnorway",
        "p": 1,  # page
        "ps": 100,  # page-size [0-500]
    }

    # projects_df = get_all_projects(data_dir, headers, project_params)
    # get_and_save_metrics(data_dir, headers)
    # get_project_measures("statisticsnorway_ssb-component-library", headers)

    projects = get_selected_projects(Path("reportprojects.txt"))
    projects_measures_df = get_all_project_measures(headers)

    # metrics_df = pd.DataFrame(data["metrics"])
    # metrics_df.to_excel(data_dir / "sc-metrics.xlsx", index=False)
    # metrics_df.to_csv(data_dir / "sc-metrics.csv", index=False)

    print(projects_measures_df.head())


if __name__ == "__main__":
    main()
