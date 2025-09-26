import requests
from typing import List, Optional, Dict, Any

class APIClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    def get_students(self, group_id: Optional[int] = None, science_id: Optional[int] = None) -> List[Dict]:
        params = {}
        if group_id is not None:
            params['group_id'] = group_id
        if science_id is not None:
            params['science_id'] = science_id

        print(f"DEBUG: Sending params - group_id: {group_id}, science_id: {science_id}")  # Отладка

        response = requests.get(f"{self.base_url}/api/students", params=params)
        response.raise_for_status()
        return response.json()

    def create_student(self, student_data: Dict) -> Dict:
        response = requests.post(f"{self.base_url}/api/students", json=student_data)
        response.raise_for_status()
        return response.json()

    def delete_student(self, student_id: int) -> bool:
        response = requests.delete(f"{self.base_url}/api/students/{student_id}")
        response.raise_for_status()
        return response.status_code == 200

    def get_statistics(self) -> Dict:
        response = requests.get(f"{self.base_url}/api/statistics")
        response.raise_for_status()
        return response.json()

    def get_groups(self) -> List[Dict]:
        response = requests.get(f"{self.base_url}/api/groups")
        response.raise_for_status()
        return response.json()

    def get_sciences(self) -> List[Dict]:
        response = requests.get(f"{self.base_url}/api/sciences")
        response.raise_for_status()
        return response.json()