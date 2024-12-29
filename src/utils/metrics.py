from dataclasses import dataclass
from ..config import METRIC_THRESHOLDS

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
    
    PING = MetricThresholds(**METRIC_THRESHOLDS['ping'])
    JITTER = MetricThresholds(**METRIC_THRESHOLDS['jitter'])
    PACKET_LOSS = MetricThresholds(**METRIC_THRESHOLDS['packet_loss'])
    
    @staticmethod
    def get_health_threshold(metric_type: str) -> float:
        thresholds = METRIC_THRESHOLDS[metric_type]
        if metric_type == 'ping':
            return thresholds['good']
        elif metric_type == 'jitter':
            return thresholds['fair']
        else:  # packet loss
            return thresholds['excellent']
    
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