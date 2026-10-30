import math
import unittest

from neuro_fly.interfaces import DistanceSample
from neuro_fly.sensor import ApproachConfig, ApproachEncoder, MockDistanceSensor


class ApproachEncoderTests(unittest.TestCase):
    def setUp(self):
        self.encoder = ApproachEncoder(ApproachConfig(
            median_window=1, smoothing_alpha=1.0, full_scale_rate_per_s=2.0,
        ))

    def test_relative_closing_rate_and_direction(self):
        self.assertEqual(self.encoder.update(DistanceSample(1000.0, 0.0)), 0.0)
        self.assertFalse(self.encoder.sample_usable)
        self.assertAlmostEqual(self.encoder.update(DistanceSample(900.0, 0.1)), 1000 / 900 / 2)
        self.assertTrue(self.encoder.sample_usable)
        self.assertEqual(self.encoder.update(DistanceSample(900.0, 0.2)), 0.0)
        self.assertEqual(self.encoder.update(DistanceSample(1000.0, 0.3)), 0.0)

    def test_rate_is_clamped_and_minimum_distance_is_only_a_denominator_floor(self):
        self.encoder.update(DistanceSample(60.0, 0.0))
        self.assertEqual(self.encoder.update(DistanceSample(10.0, 0.1)), 1.0)
        self.assertEqual(self.encoder.update(DistanceSample(10.0, 0.2)), 0.0)

    def test_invalid_samples_clear_filter_and_baseline(self):
        invalid = [None, 0.0, -1.0, float('nan'), float('inf')]
        for value in invalid:
            with self.subTest(value=value):
                self.encoder.update(DistanceSample(1000.0, 1.0))
                self.assertEqual(self.encoder.update(DistanceSample(value, 1.1)), 0.0)
                self.assertFalse(self.encoder.sample_usable)
                self.assertEqual(self.encoder.update(DistanceSample(500.0, 1.2)), 0.0)
                self.assertFalse(self.encoder.sample_usable)
        self.assertEqual(self.encoder.update(DistanceSample(500.0, 1.3, False)), 0.0)
        self.assertEqual(self.encoder.update(DistanceSample(500.0, float('nan'))), 0.0)

    def test_nonincreasing_and_stale_timestamps_start_a_new_baseline(self):
        self.encoder.update(DistanceSample(1000.0, 1.0))
        for timestamp in (1.0, 0.5, 2.0):
            self.assertEqual(self.encoder.update(DistanceSample(500.0, timestamp)), 0.0)
            self.assertFalse(self.encoder.sample_usable)
        self.assertEqual(self.encoder.update(DistanceSample(500.0, 2.1)), 0.0)
        self.assertTrue(self.encoder.sample_usable)

    def test_default_filters_limit_jitter_and_keep_values_bounded(self):
        for scenario in ("jitter", "approach", "far", "still", "receding", "invalid"):
            sensor, encoder = MockDistanceSensor(scenario), ApproachEncoder()
            values = []
            while (sample := sensor.read()) is not None:
                values.append(encoder.update(sample))
            with self.subTest(scenario=scenario):
                self.assertTrue(values)
                self.assertTrue(all(math.isfinite(v) and 0 <= v <= 1 for v in values))
                if scenario == "approach":
                    self.assertGreater(max(values), 0.9)
                elif scenario == "jitter":
                    self.assertLess(max(values), 0.1)
                else:
                    self.assertEqual(max(values), 0.0)

    def test_config_rejects_invalid_values(self):
        for kwargs in ({"min_distance_mm": 0}, {"max_sample_gap_s": float('nan')},
                       {"smoothing_alpha": 0}, {"median_window": 0}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                ApproachConfig(**kwargs)


if __name__ == "__main__":
    unittest.main()
