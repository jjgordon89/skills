import unittest
from unittest import mock

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import tesla  # noqa: E402


class FlakyVehicle:
    def __init__(self, fail_times=1):
        self.fail_times = fail_times
        self.calls = 0

    def get_vehicle_data(self):
        self.calls += 1
        if self.calls <= self.fail_times:
            raise RuntimeError("transient API error")
        return {"ok": True, "calls": self.calls}


class FetchVehicleDataRetriesTests(unittest.TestCase):
    def test_fetch_vehicle_data_retries_then_succeeds(self):
        v = FlakyVehicle(fail_times=2)
        with mock.patch.object(tesla.time, "sleep") as sleep:
            out = tesla.fetch_vehicle_data(v, retries=3, retry_delay_s=0.01)

        self.assertEqual(out["ok"], True)
        self.assertEqual(v.calls, 3)
        # Should have slept twice (after the first and second failure)
        self.assertEqual(sleep.call_count, 2)

    def test_fetch_vehicle_data_raises_after_exhausting_retries(self):
        v = FlakyVehicle(fail_times=5)
        with mock.patch.object(tesla.time, "sleep"):
            with self.assertRaises(RuntimeError):
                tesla.fetch_vehicle_data(v, retries=2, retry_delay_s=0)


if __name__ == "__main__":
    unittest.main()
