"""Optional Linux/WSL test: real pinned brain and data with mock I/O."""

import os
from pathlib import Path
import sys
import unittest

from neuro_fly.brain import DEFAULT_REFERENCE, NeuroHexBrainAdapter
from neuro_fly.output import MockOutput, PulseController
from neuro_fly.pipeline import Pipeline, run_pipeline
from neuro_fly.sensor import ApproachEncoder, MockDistanceSensor


REFERENCE = Path(os.environ.get('NEUROHEX_REFERENCE', str(DEFAULT_REFERENCE)))
DATA = REFERENCE / 'connectome_data'
AVAILABLE = (sys.platform.startswith('linux') and (REFERENCE / 'snn_brain.py').is_file()
             and all((DATA / name).is_file() for name in
                     ('adjacency_matrix.npy', 'neuron_metadata.json', 'connection_list.json')))


@unittest.skipUnless(AVAILABLE, 'Linux/WSL and pinned reference with real data required')
class RealNeuroHexIntegrationTests(unittest.TestCase):
    def test_mock_sensor_real_brain_mock_output(self):
        brain = NeuroHexBrainAdapter(REFERENCE)
        self.assertGreater(brain.connectome.neurons, 20)

        still_output = MockOutput()
        still_control = PulseController(still_output)
        still = Pipeline(MockDistanceSensor('still'), ApproachEncoder(), brain, still_control)
        still_cycles, _ = run_pipeline(still)
        self.assertEqual(still_control.trigger_count, 0)
        self.assertFalse(any(c.triggered for c in still_cycles))

        output = MockOutput()
        controller = PulseController(output)
        approach = Pipeline(MockDistanceSensor('approach'), ApproachEncoder(), brain, controller)
        cycles, _ = run_pipeline(approach)
        self.assertGreater(max(c.looming_strength for c in cycles), 0.9)
        self.assertGreater(max(c.escape_magnitude for c in cycles), 0.5)
        triggers = [cycle for cycle in cycles if cycle.triggered]
        self.assertGreaterEqual(len(triggers), 1)
        self.assertTrue(all(c.escape_magnitude > 0.5 for c in triggers))
        self.assertEqual(controller.trigger_count, len(triggers))
        self.assertFalse(output.active)
        self.assertEqual(sum(event.active for event in output.events), len(triggers))


if __name__ == '__main__':
    unittest.main()
