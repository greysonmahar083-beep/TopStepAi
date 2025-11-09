import os
import sys
from datetime import datetime, timedelta, timezone

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from data.gold_data import GoldDataPuller


class FakeClient:
    def __init__(self, bars_by_contract):
        self.bars_by_contract = bars_by_contract

    def authenticate(self):  # pragma: no cover - not used in tests
        return True

    def get_contract_by_id(self, contract_id):
        if contract_id in self.bars_by_contract:
            return {"id": contract_id}
        return None

    def retrieve_bars(
        self,
        contract_id,
        live,
        start_time,
        end_time,
        unit,
        unit_number,
        limit,
        include_partial_bar,
    ):
        timeframe_lookup = {
            (3, 1): "1hour",
            (4, 1): "1day",
        }
        key = timeframe_lookup.get((unit, unit_number))
        bars = self.bars_by_contract.get(contract_id, {}).get(key, [])
        return {"success": True, "bars": bars[:limit]}


def make_bar(ts, price):
    return {
        "t": ts.isoformat(),
        "o": price,
        "h": price + 1,
        "l": price - 1,
        "c": price + 0.5,
        "v": 100,
    }


def test_collect_stitched_candles_trims_to_days_back():
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=10)

    z25_bars = [
        make_bar(now - timedelta(hours=2), 10),
        make_bar(now - timedelta(hours=30), 11),
        make_bar(now - timedelta(hours=80), 12),
    ]
    q25_bars = [
        make_bar(now - timedelta(hours=30), 20),  # duplicate timestamp across contracts
        make_bar(now - timedelta(hours=90), 21),
        make_bar(now - timedelta(hours=400), 22),  # should be trimmed
    ]

    fake_client = FakeClient(
        {
            "CON.F.US.MGC.Z25": {"1hour": z25_bars},
            "CON.F.US.MGC.Q25": {"1hour": q25_bars},
        }
    )

    puller = GoldDataPuller(client=fake_client)
    puller.contract_id = "CON.F.US.MGC.Z25"

    stitched, per_contract = puller.collect_stitched_candles(
        timeframes=["1hour"],
        bars_per_contract=10,
        contracts_to_pull=2,
        include_partial_bar=False,
        include_current=True,
        min_year=20,
        use_all_month_codes=True,
        days_back=10,
        target_bars={"1hour": 4},
    )

    assert "1hour" in stitched
    df = stitched["1hour"]
    assert len(df) == 4
    assert df["timestamp"].min() >= cutoff
    assert (df["timestamp"] < cutoff).sum() == 0
    # Ensure duplicate timestamp appears only once
    duplicate_count = (df["timestamp"] == now - timedelta(hours=30)).sum()
    assert duplicate_count == 1

    # Per-contract frames should respect the days_back filter
    assert "CON.F.US.MGC.Z25" in per_contract
    assert "CON.F.US.MGC.Q25" in per_contract
    assert len(per_contract["CON.F.US.MGC.Q25"]["1hour"]) == 2
    assert all(ts >= cutoff for ts in per_contract["CON.F.US.MGC.Q25"]["1hour"]["timestamp"])