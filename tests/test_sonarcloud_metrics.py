from typing import Any

import pytest
import requests
from requests_mock import Mocker

from scripts.sonarcloud_metrics import ProjParams
from scripts.sonarcloud_metrics import fetch_all_pages


def test_fetch_all_pages(
    requests_mock: Mocker,
    sc_proj_response1: dict[str, Any],
    sc_proj_response2: dict[str, Any],
) -> None:
    base_url = "https://sonarcloud.io/api/projects/search"
    headers = {"Authorization": "Bearer token"}
    requests_mock.get(
        base_url,
        [
            {"json": sc_proj_response1, "status_code": 200},
            {"json": sc_proj_response2, "status_code": 200},
        ],
    )

    params: ProjParams = {
        "organization": "statisticsnorway",
        "p": 1,  # page
        "ps": 1,  # page-size [0-500]
    }
    result = fetch_all_pages(base_url, headers, params)
    assert requests_mock.call_count == 2
    assert len(result) == 2
    assert result[0]["key"] == "statisticsnorway_ssb-timeseries"
    assert result[1]["key"] == "statisticsnorway_tech-coach-examples"


def test_fetch_all_pages_error(
    requests_mock: Mocker, sc_proj_response1: dict[str, Any]
) -> None:
    base_url = "https://sonarcloud.io/api/projects/search"
    headers = {"Authorization": "Bearer token"}
    requests_mock.get(base_url, text="Not Found", status_code=404)

    params: ProjParams = {
        "organization": "statisticsnorway",
        "p": 1,  # page
        "ps": 1,  # page-size [0-500]
    }
    with pytest.raises(requests.exceptions.HTTPError):
        fetch_all_pages(base_url, headers, params)
    assert requests_mock.call_count == 1
