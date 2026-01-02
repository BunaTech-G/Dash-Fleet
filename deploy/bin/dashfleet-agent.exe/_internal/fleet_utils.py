"""
Shared utility functions for DashFleet fleet monitoring.
These functions are used by both the main Flask app and the fleet agents.
"""

def calculate_health_score(stats: dict) -> dict:
    """
    Calculate a health score (0-100) and status based on system metrics.
    
    Args:
        stats: Dictionary with cpu_percent, ram_percent, disk_percent
    
    Returns:
        Dictionary with score, status, and component scores
    """
    def clamp(x: float) -> float:
        return max(0.0, min(1.0, x))

    cpu = float(stats["cpu_percent"])
    ram = float(stats["ram_percent"])
    disk = float(stats["disk_percent"])

    # Component scores (1 = perfect, 0 = critical)
    cpu_score = clamp(1 - max(0.0, (cpu - 50) / 50))  # Linear from 50% to 100%
    ram_score = clamp(1 - max(0.0, (ram - 60) / 40))  # Linear from 60% to 100%
    disk_score = clamp(1 - max(0.0, (disk - 70) / 30))  # Linear from 70% to 100%

    # Weighted overall score
    weights = {"cpu": 0.35, "ram": 0.35, "disk": 0.30}
    overall = (
        cpu_score * weights["cpu"]
        + ram_score * weights["ram"]
        + disk_score * weights["disk"]
    )

    score = round(overall * 100)
    if score >= 80:
        status = "ok"
    elif score >= 60:
        status = "warn"
    else:
        status = "critical"

    return {
        "score": score,
        "status": status,
        "components": {
            "cpu": round(cpu_score * 100),
            "ram": round(ram_score * 100),
            "disk": round(disk_score * 100),
        },
    }


def format_bytes_to_gib(bytes_value: float) -> float:
    """Convert bytes to GiB with 2 decimal places."""
    return round(bytes_value / (1024 ** 3), 2)


def format_uptime_hms(seconds: float) -> str:
    """Format uptime in H:M:S format."""
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"
