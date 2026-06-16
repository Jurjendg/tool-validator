from dataclasses import dataclass

import requests


@dataclass(slots=True)
class ApiClient:
    base_url: str
    token: str = ""

    def get_prediction(self, bag_id: str) -> dict:
        if not self.base_url:
            return {}

        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        response = requests.get(
            f"{self.base_url.rstrip('/')}/predictions/{bag_id}",
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
