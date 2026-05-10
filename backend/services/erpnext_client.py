import httpx
from backend.config import settings


class ERPNextClient:
    def __init__(self):
        self.base_url = settings.erpnext_url
        self.headers = {
            "Authorization": f"token {settings.erpnext_api_key}:{settings.erpnext_api_secret}",
            "Content-Type": "application/json",
        }

    def get(self, endpoint: str, params: dict = None) -> dict:
        url = f"{self.base_url}/{endpoint}"
        try:
            response = httpx.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            try:
                error_detail = e.response.json()
            except Exception:
                error_detail = e.response.text
            raise Exception(f"ERPNext GET error {e.response.status_code}: {error_detail}")
        except Exception as e:
            raise Exception(f"ERPNext GET failed: {str(e)}")

    def post(self, endpoint: str, data: dict) -> dict:
        url = f"{self.base_url}/{endpoint}"
        try:
            response = httpx.post(url, headers=self.headers, json=data, timeout=30)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            try:
                error_detail = e.response.json()
            except Exception:
                error_detail = e.response.text
            raise Exception(f"ERPNext POST error {e.response.status_code}: {error_detail}")
        except Exception as e:
            raise Exception(f"ERPNext POST failed: {str(e)}")

    def put(self, endpoint: str, data: dict) -> dict:
        url = f"{self.base_url}/{endpoint}"
        try:
            response = httpx.put(url, headers=self.headers, json=data, timeout=30)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            try:
                error_detail = e.response.json()
            except Exception:
                error_detail = e.response.text
            raise Exception(f"ERPNext PUT error {e.response.status_code}: {error_detail}")
        except Exception as e:
            raise Exception(f"ERPNext PUT failed: {str(e)}")


erpnext_client = ERPNextClient()