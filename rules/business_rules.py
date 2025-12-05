# rules/business_rules.py
from dataclasses import dataclass


@dataclass
class BusinessRuleConfig:
    stock_mismatch_threshold: float = 10.0   # units
    yield_loss_default_threshold: float = 5.0  # percent
    high_severity_gap: float = 50.0         # units or %
    medium_severity_gap: float = 20.0


RULES = BusinessRuleConfig()
