import unittest

from flights.normalize import normalize_flight, normalize_flights

SAMPLE_DEPARTURE = {
    "id": "123456789",
    "flightName": "KL1001",
    "flightDirection": "D",
    "prefixIATA": "KL",
    "scheduleDateTime": "2026-11-18T14:35:00.000+01:00",
    "expectedTimeBoarding": "2026-11-18T14:55:00.000+01:00",
    "gate": "D5",
    "terminal": 1,
    "route": {"destinations": ["LHR"]},
    "publicFlightState": {"flightStates": ["DEL"]},
    "codeshares": {"codeshares": ["DL7654"]},
}

SAMPLE_ARRIVAL = {
    "flightName": "HV5612",
    "flightDirection": "A",
    "scheduleTime": "09:05:00",
    "route": {"destinations": ["AGP"]},
    "publicFlightState": {"flightStates": ["LND"]},
    "baggageClaim": {"belts": ["7"]},
}


class NormalizeTests(unittest.TestCase):
    def test_departure_fields(self):
        f = normalize_flight(SAMPLE_DEPARTURE)
        self.assertEqual(f["flight"], "KL1001")
        self.assertEqual(f["scheduled"], "14:35")
        self.assertEqual(f["expected"], "14:55")
        self.assertEqual(f["airports"], ["LHR"])
        self.assertEqual(f["gate"], "D5")
        self.assertEqual(f["status"], "Delayed")
        self.assertTrue(f["delayed"])
        self.assertFalse(f["cancelled"])

    def test_arrival_fields(self):
        f = normalize_flight(SAMPLE_ARRIVAL)
        self.assertEqual(f["scheduled"], "09:05")
        self.assertEqual(f["belt"], "7")
        self.assertEqual(f["status"], "Landed")

    def test_expected_hidden_when_same_as_scheduled(self):
        raw = dict(SAMPLE_DEPARTURE, expectedTimeBoarding="2026-11-18T14:35:00.000+01:00")
        self.assertIsNone(normalize_flight(raw)["expected"])

    def test_cancelled(self):
        raw = dict(SAMPLE_DEPARTURE, publicFlightState={"flightStates": ["CNX"]})
        f = normalize_flight(raw)
        self.assertTrue(f["cancelled"])
        self.assertEqual(f["status"], "Cancelled")

    def test_missing_fields_do_not_crash(self):
        f = normalize_flight({})
        self.assertEqual(f["flight"], "")
        self.assertIsNone(f["scheduled"])
        self.assertEqual(f["airports"], [])
        self.assertEqual(f["status"], "—")

    def test_none_input(self):
        self.assertEqual(normalize_flights(None), [])

    def test_unknown_state_code_passes_through(self):
        raw = dict(SAMPLE_DEPARTURE, publicFlightState={"flightStates": ["XYZ"]})
        self.assertEqual(normalize_flight(raw)["status"], "XYZ")


if __name__ == "__main__":
    unittest.main()
