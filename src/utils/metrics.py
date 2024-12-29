from dataclasses import dataclass

@dataclass
class MetricThresholds:
    """Thresholds for network metrics"""
    excellent: float
    good: float
    fair: float
    poor: float
    weight: float

class NetworkMetrics:
    """Centralized network metrics configuration"""
    
    PING = MetricThresholds(
        excellent=20,
        good=30,
        fair=60,
        poor=100,
        weight=0.4
    )
    
    JITTER = MetricThresholds(
        excellent=2,
        good=5,
        fair=10,
        poor=20,
        weight=0.4
    )
    
    PACKET_LOSS = MetricThresholds(
        excellent=0,
        good=0.1,
        fair=0.5,
        poor=1,
        weight=0.2
    )
    
    @staticmethod
    def get_health_threshold(metric_type: str) -> float:
        if metric_type == 'ping':
            return NetworkMetrics.PING.good
        elif metric_type == 'jitter':
            return NetworkMetrics.JITTER.fair
        else:  # packet loss
            return NetworkMetrics.PACKET_LOSS.excellent
    
    @staticmethod
    def calculate_metric_score(value: float, thresholds: MetricThresholds) -> float:
        if value <= thresholds.excellent:
            return 100
        elif value <= thresholds.good:
            return 75
        elif value <= thresholds.fair:
            return 50
        elif value <= thresholds.poor:
            return 25
        else:
            return 0 