"""
JSON Exporter - Export Isolation Data

Exports isolation operation data in JSON format for integration
with SIEM, analytics platforms, and other systems.
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path


class JSONExporter:
    """Exports isolation data to JSON format."""

    def __init__(self, pretty: bool = True):
        """
        Initialize JSON exporter.

        Args:
            pretty: Use pretty printing (indented JSON)
        """
        self.pretty = pretty

    def export_render(
        self,
        render_data: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> str:
        """
        Export a single render operation to JSON.

        Args:
            render_data: Render operation data
            output_path: Optional output file path

        Returns:
            JSON string
        """
        # Ensure datetime objects are serialized
        render_data = self._prepare_for_json(render_data)

        json_str = json.dumps(
            render_data,
            indent=2 if self.pretty else None,
            sort_keys=True
        )

        if output_path:
            self.save_json(json_str, output_path)

        return json_str

    def export_multiple(
        self,
        renders: List[Dict[str, Any]],
        output_path: Optional[str] = None
    ) -> str:
        """
        Export multiple render operations to JSON.

        Args:
            renders: List of render operations
            output_path: Optional output file path

        Returns:
            JSON string
        """
        # Prepare all renders
        prepared_renders = [self._prepare_for_json(r) for r in renders]

        # Build export structure
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "total_renders": len(prepared_renders),
            "format_version": "1.0",
            "renders": prepared_renders
        }

        json_str = json.dumps(
            export_data,
            indent=2 if self.pretty else None,
            sort_keys=True
        )

        if output_path:
            self.save_json(json_str, output_path)

        return json_str

    def export_siem_format(
        self,
        render_data: Dict[str, Any],
        siem_type: str = "generic"
    ) -> str:
        """
        Export in SIEM-compatible format.

        Args:
            render_data: Render operation data
            siem_type: SIEM type ('generic', 'splunk', 'elk', 'sentinel')

        Returns:
            SIEM-formatted JSON string
        """
        render_data = self._prepare_for_json(render_data)

        if siem_type == "splunk":
            # Splunk HEC format
            siem_data = {
                "time": datetime.now().timestamp(),
                "source": "browser_isolation",
                "sourcetype": "isolation:render",
                "event": render_data
            }
        elif siem_type == "elk":
            # ELK format
            siem_data = {
                "@timestamp": datetime.now().isoformat(),
                "@version": "1",
                "type": "browser_isolation",
                "event": render_data
            }
        elif siem_type == "sentinel":
            # Azure Sentinel format
            siem_data = {
                "TimeGenerated": datetime.now().isoformat(),
                "Type": "BrowserIsolation",
                "Category": "SecurityEvent",
                **render_data
            }
        else:
            # Generic format
            siem_data = {
                "timestamp": datetime.now().isoformat(),
                "log_type": "browser_isolation",
                "severity": self._map_risk_to_severity(
                    render_data.get('risk_score', 0)
                ),
                "data": render_data
            }

        return json.dumps(siem_data, indent=2 if self.pretty else None)

    def export_statistics(
        self,
        stats: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> str:
        """
        Export statistics in JSON format.

        Args:
            stats: Statistics dictionary
            output_path: Optional output file path

        Returns:
            JSON string
        """
        stats = self._prepare_for_json(stats)
        
        json_str = json.dumps(
            stats,
            indent=2 if self.pretty else None,
            sort_keys=True
        )

        if output_path:
            self.save_json(json_str, output_path)

        return json_str

    def save_json(self, json_str: str, output_path: str) -> None:
        """
        Save JSON string to file.

        Args:
            json_str: JSON content
            output_path: Output file path
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w') as f:
            f.write(json_str)

    def _prepare_for_json(self, data: Any) -> Any:
        """
        Prepare data for JSON serialization.

        Converts datetime objects and other non-serializable types.
        """
        if isinstance(data, dict):
            return {k: self._prepare_for_json(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._prepare_for_json(item) for item in data]
        elif isinstance(data, datetime):
            return data.isoformat()
        elif hasattr(data, '__dict__'):
            return self._prepare_for_json(data.__dict__)
        else:
            return data

    def _map_risk_to_severity(self, risk_score: float) -> str:
        """Map risk score to severity level."""
        if risk_score >= 7.0:
            return "critical"
        elif risk_score >= 5.0:
            return "high"
        elif risk_score >= 3.0:
            return "medium"
        else:
            return "low"

