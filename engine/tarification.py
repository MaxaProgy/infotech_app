import math
from decimal import Decimal
from typing import Callable, Optional

from engine.models import CdrRecord, Tariff, TarifiedRecord


class TrieNode:
    __slots__ = ("children", "tariffs")

    def __init__(self):
        self.children: dict[str, TrieNode] = {}
        self.tariffs: list[Tariff] = []


def build_trie(tariffs: list[Tariff]) -> TrieNode:
    root = TrieNode()
    for tariff in tariffs:
        node = root
        for ch in tariff.prefix:
            if ch not in node.children:
                node.children[ch] = TrieNode()
            node = node.children[ch]
        node.tariffs.append(tariff)
    return root


def _find_longest_prefix_tariffs(root: TrieNode, number: str) -> list[Tariff]:
    """Walk the trie collecting all tariffs, return those at the deepest match."""
    node = root
    best: list[Tariff] = root.tariffs[:]
    for ch in number:
        if ch not in node.children:
            break
        node = node.children[ch]
        if node.tariffs:
            best = node.tariffs[:]
    return best


def _matches_timeband(call_time, timeband: tuple) -> bool:
    start, end = timeband
    if start <= end:
        return start <= call_time < end
    # Night tariff crossing midnight: e.g. 22:00-06:00
    return call_time >= start or call_time < end


def tarify(
    cdr_records: list[CdrRecord],
    tariffs: list[Tariff],
    subscribers: dict[str, str],
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> list[TarifiedRecord]:
    root = build_trie(tariffs)
    results: list[TarifiedRecord] = []
    total = len(cdr_records)

    for i, cdr in enumerate(cdr_records):
        if progress_callback:
            progress_callback(i, total)

        subscriber_name = subscribers.get(cdr.calling_party)

        if cdr.call_direction != "outgoing" or cdr.disposition != "answered":
            results.append(TarifiedRecord(
                cdr=cdr, tariff=None, cost=None,
                subscriber_name=subscriber_name,
            ))
            continue

        called = cdr.called_party
        candidates = _find_longest_prefix_tariffs(root, called)

        call_date = cdr.start_time.date()
        call_time = cdr.start_time.time()
        call_weekday = cdr.start_time.isoweekday()

        matched: list[Tariff] = []
        for t in candidates:
            if t.effective_date <= call_date <= t.expiry_date \
                    and call_weekday in t.weekday \
                    and _matches_timeband(call_time, t.timeband):
                matched.append(t)

        if not matched:
            results.append(TarifiedRecord(
                cdr=cdr, tariff=None, cost=None,
                subscriber_name=subscriber_name,
            ))
            continue

        best = max(matched, key=lambda t: t.priority)

        minutes = math.ceil(cdr.billable_sec / 60)
        cost = best.connection_fee + Decimal(minutes) * best.rate_per_min

        results.append(TarifiedRecord(
            cdr=cdr, tariff=best, cost=cost,
            subscriber_name=subscriber_name,
        ))

    if progress_callback:
        progress_callback(total, total)

    return results
