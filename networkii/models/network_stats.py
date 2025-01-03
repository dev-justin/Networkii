from dataclasses import dataclass
from collections import deque
from typing import Optional
from enum import Enum

class NetworkMetric:
    def __init__(self, name: str, weight: float, threshold: float, excellent: float, good: float, fair: float):
        self.name = name
        self.weight = weight
        self.threshold = threshold
        self.excellent = excellent
        self.good = good
        self.fair = fair

class NetworkMetrics:
    # Define network metrics with their weights and thresholds
    PING = NetworkMetric("ping", 0.4, 100, 20, 50, 80)
    JITTER = NetworkMetric("jitter", 0.3, 50, 5, 15, 30)
    PACKET_LOSS = NetworkMetric("packet_loss", 0.3, 5, 0.1, 1, 3)

    @staticmethod
    def calculate_metric_score(value: float, metric: NetworkMetric) -> float:
        """Calculate a score (0-100) for a metric value."""
        if value <= metric.excellent:
            return 100
        elif value <= metric.good:
            return 75
        elif value <= metric.fair:
            return 50
        elif value <= metric.threshold:
            return 25
        else:
            return 0

    @staticmethod
    def get_health_threshold(metric_type: str) -> float:
        """Get the threshold value for a metric type."""
        if metric_type == "ping":
            return NetworkMetrics.PING.threshold
        elif metric_type == "jitter":
            return NetworkMetrics.JITTER.threshold
        elif metric_type == "packet_loss":
            return NetworkMetrics.PACKET_LOSS.threshold
        else:
            raise ValueError(f"Unknown metric type: {metric_type}")

@dataclass
class NetworkStats:
    timestamp: float
    ping_history: deque
    jitter_history: deque
    packet_loss_history: deque
    speed_test_status: bool
    speed_test_timestamp: float
    download_speed: float
    upload_speed: float
    interface: str
    interface_ip: str
    ping_target: str
    
    @property
    def ping(self) -> float:
        """Get the most recent ping value"""
        return self.ping_history[-1] if self.ping_history else 0
    
    @property
    def jitter(self) -> float:
        """Get the most recent jitter value"""
        return self.jitter_history[-1] if self.jitter_history else 0
    
    @property
    def packet_loss(self) -> float:
        """Get the most recent packet loss value"""
        return self.packet_loss_history[-1] if self.packet_loss_history else 0 