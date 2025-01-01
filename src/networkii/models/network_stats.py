from dataclasses import dataclass
from collections import deque
from typing import Optional

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