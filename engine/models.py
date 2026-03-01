from dataclasses import dataclass
from datetime import datetime, date, time
from decimal import Decimal
from typing import Optional


@dataclass
class CdrRecord:
    start_time: datetime
    end_time: datetime
    calling_party: str
    called_party: str
    call_direction: str
    disposition: str
    duration: int
    billable_sec: int
    charge: Decimal
    account_code: str
    call_id: str
    trunk_name: str


@dataclass
class Tariff:
    prefix: str
    destination: str
    rate_per_min: Decimal
    connection_fee: Decimal
    timeband: tuple[time, time]
    weekday: set[int]
    priority: int
    effective_date: date
    expiry_date: date


@dataclass
class TarifiedRecord:
    cdr: CdrRecord
    tariff: Optional[Tariff]
    cost: Optional[Decimal]
    subscriber_name: Optional[str]
