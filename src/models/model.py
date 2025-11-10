from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class DataPoint:
    """
    Representa um ponto de dado de taxa de câmbio.

    Attributes:
        timestamp (datetime): Momento da coleta da taxa.
        source (str): Origem da informação (ex: 'API Layer').
        base (str): Moeda base (ex: 'USD').
        target (str): Moeda alvo (ex: 'BRL').
        rate (float): Valor da taxa de conversão.
    """
    timestamp: datetime
    source: str
    base: str
    target: str
    rate: float

    def __post_init__(self):
        if self.rate <= 0:
            raise ValueError("A taxa de câmbio deve ser positiva.")

    def to_dict(self) -> dict:
        """Converte o DataPoint em dicionário para fácil exportação."""
        d = asdict(self)
        d["timestamp"] = self.timestamp.isoformat()
        return d