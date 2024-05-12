from typing import Any

import pytest


@pytest.fixture
def sc_proj_response1() -> dict[str, Any]:
    return {
        "paging": {"pageIndex": 1, "pageSize": 1, "total": 2},
        "components": [
            {
                "organization": "statisticsnorway",
                "key": "statisticsnorway_ssb-timeseries",
                "name": "ssb-timeseries",
                "qualifier": "TRK",
                "visibility": "public",
                "lastAnalysisDate": "2024-05-07T21:54:30+0200",
                "revision": "ede94d2fd8f2d39857bdd691f1cd6afa22cbfce4",
            }
        ],
    }


@pytest.fixture
def sc_proj_response2() -> dict[str, Any]:
    return {
        "paging": {"pageIndex": 2, "pageSize": 1, "total": 2},
        "components": [
            {
                "organization": "statisticsnorway",
                "key": "statisticsnorway_tech-coach-examples",
                "name": "tech-coach-examples",
                "qualifier": "TRK",
                "visibility": "public",
            }
        ],
    }
