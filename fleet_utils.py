"""
Utilitaires partagés entre l'agent et l'API pour éviter les duplications.
"""


def format_bytes_to_gib(bytes_value: float) -> float:
    """Convertit des bytes en Gio avec deux décimales."""
    return round(bytes_value / (1024 ** 3), 2)


def format_uptime_hms(seconds: float) -> str:
    """Retourne l'uptime au format HH:MM:SS."""
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def calculate_health_score(stats: dict) -> dict:
    """
    Calcule un score de santé 0-100 et un statut (ok/warn/critical).
    
    Utilisé par l'agent ET l'API pour avoir une logique cohérente.
    
    Args:
        stats: dict avec cpu_percent, ram_percent, disk_percent
        
    Returns:
        dict avec score (0-100), status, et components détaillés
    """
    def clamp(x: float) -> float:
        return max(0.0, min(1.0, x))

    cpu = float(stats.get("cpu_percent", 0))
    ram = float(stats.get("ram_percent", 0))
    disk = float(stats.get("disk_percent", 0))

    # Scores par composant (1 = parfait, 0 = mauvais)
    cpu_score = clamp(1 - max(0.0, (cpu - 50) / 50))    # plein à 50%, tombe à 0 à 100%
    ram_score = clamp(1 - max(0.0, (ram - 60) / 40))    # plein à 60%, tombe à 0 à 100%
    disk_score = clamp(1 - max(0.0, (disk - 70) / 30))  # plein à 70%, 0 à 100%

    # Pondérations
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
