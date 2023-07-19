from typing import Dict, Optional
import requests
import json


class CgApiClient:
    def __init__(self, base_url):
        self.base_url = base_url

    def apptag(self, tag_name, key=None, entry_point="/applications"):
        res = requests.get(self.base_url + entry_point + "/" + tag_name)

        if key:
            return json.loads(res.text)[key]
        else:
            return json.loads(res.text)

    def get_sequencing_metrics_for_flow_cell(
        self, flow_cell_name: str
    ) -> Optional[Dict]:
        """Retrieve sequencing metrics for a flow cell from the CG API."""
        metrics_endpoint: str = f"/flowcells/{flow_cell_name}/sequencing_metrics"
        try:
            response = requests.get(self.base_url + metrics_endpoint)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Failed to retrieve metrics for flowcell {flow_cell_name}: {e}")
