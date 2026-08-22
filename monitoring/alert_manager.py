# -*- coding: utf-8 -*-
"""
alert_manager.py — Real-time Anomaly Alerting & Notification Manager
"""

from typing import Dict, Any, List

logger = __import__("logging").getLogger("nexa.monitoring.alerts")


class AlertManager:
    def __init__(self):
        self.alerts_history: List[Dict[str, Any]] = []

    def dispatch_alert(self, severity: str, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        alert = {
            "severity": severity,
            "message": message,
            "context": context,
            "timestamp": __import__("datetime").datetime.now().isoformat()
        }
        self.alerts_history.append(alert)
        if severity == "CRITICAL":
            logger.critical("ALERT [CRITICAL]: %s", message)
        else:
            logger.warning("ALERT [%s]: %s", severity, message)
        return alert
