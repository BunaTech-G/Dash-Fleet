"""
Centralized Marshmallow schemas for API validation.

All request/response schema definitions for DashFleet API.
"""

from marshmallow import Schema, fields


class ReportSchema(Schema):
    """Validates fleet agent metric reports.
    
    Fields:
        machine_id (str): Unique machine identifier
        report (dict): Metrics dictionary containing CPU, RAM, Disk, etc.
    """
    machine_id = fields.Str(required=True)
    report = fields.Dict(required=True)


class MetricsSchema(Schema):
    """Validates individual metric fields in a report.
    
    Fields:
        cpu_percent (float): CPU usage percentage
        ram_percent (float): RAM usage percentage
        disk_percent (float): Disk usage percentage
        timestamp (str, optional): ISO timestamp
        ram_used_gib (float, optional): RAM used in GiB
        ram_total_gib (float, optional): Total RAM in GiB
        disk_used_gib (float, optional): Disk used in GiB
        disk_total_gib (float, optional): Total disk in GiB
        uptime_seconds (float, optional): System uptime in seconds
        uptime_hms (str, optional): Human-readable uptime (H:M:S)
        health (dict, optional): Health score and status
    """
    cpu_percent = fields.Float(required=True)
    ram_percent = fields.Float(required=True)
    disk_percent = fields.Float(required=True)
    timestamp = fields.Str(required=False)
    ram_used_gib = fields.Float(required=False)
    ram_total_gib = fields.Float(required=False)
    disk_used_gib = fields.Float(required=False)
    disk_total_gib = fields.Float(required=False)
    uptime_seconds = fields.Float(required=False)
    uptime_hms = fields.Str(required=False)
    health = fields.Dict(required=False)


# Instantiate schemas for use in endpoints
report_schema = ReportSchema()
metrics_schema = MetricsSchema()
