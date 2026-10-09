from typing import Dict, Any

class FilesTool:
    @staticmethod
    def read_file(path: str) -> Dict[str, Any]:
        return {
            "status": "SUCCESS",
            "tool": "read_file",
            "path": path,
            "content": f"[Mock file content for {path}]",
            "size_bytes": 1024
        }

    @staticmethod
    def export_data(dataset_name: str, destination_url: str) -> Dict[str, Any]:
        return {
            "status": "SUCCESS",
            "tool": "export_data",
            "dataset_name": dataset_name,
            "destination_url": destination_url,
            "message": f"Exported {dataset_name} to {destination_url}."
        }
