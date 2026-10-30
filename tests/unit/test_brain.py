import importlib.util
import json
from pathlib import Path
import subprocess
import unittest
from unittest import mock
import uuid

from neuro_fly.brain import (BrainSetupError, BrainStepError, GF_IDS, REFERENCE_COMMIT,
                             NeuroHexBrainAdapter, check_reference, validate_connectome)


class ReferenceChecksTests(unittest.TestCase):
    def test_missing_reference_fails_before_import(self):
        missing = Path.cwd() / ('missing-reference-' + uuid.uuid4().hex)
        with self.assertRaisesRegex(BrainSetupError, "missing"):
            check_reference(missing)

    def test_wrong_commit_and_modified_source_are_rejected(self):
        root = (Path.cwd() / 'reference-fixture').resolve()
        with mock.patch.object(Path, 'is_file', return_value=True):
            def git_result(_root, *args):
                if '--show-toplevel' in args:
                    return subprocess.CompletedProcess(args, 0, str(root), '')
                if '--verify' in args:
                    return subprocess.CompletedProcess(args, 0, 'wrong-commit', '')
                return subprocess.CompletedProcess(args, 0, '', '')
            with mock.patch('neuro_fly.brain._git', side_effect=git_result):
                with self.assertRaisesRegex(BrainSetupError, 'commit'):
                    check_reference(root)
            def dirty_git(_root, *args):
                if '--show-toplevel' in args:
                    return subprocess.CompletedProcess(args, 0, str(root), '')
                if '--verify' in args:
                    return subprocess.CompletedProcess(args, 0, REFERENCE_COMMIT, '')
                return subprocess.CompletedProcess(args, 1, '', '')
            with mock.patch('neuro_fly.brain._git', side_effect=dirty_git):
                with self.assertRaisesRegex(BrainSetupError, 'changed'):
                    check_reference(root)

    def test_git_unavailable_is_reported(self):
        root = Path.cwd() / 'reference-fixture'
        with mock.patch.object(Path, 'is_file', return_value=True):
            with mock.patch('neuro_fly.brain.subprocess.run', side_effect=FileNotFoundError('git')):
                with self.assertRaisesRegex(BrainSetupError, 'Git could not inspect'):
                    check_reference(root)


@unittest.skipUnless(importlib.util.find_spec('numpy'), 'NumPy is needed for structural data tests')
class ConnectomeValidationTests(unittest.TestCase):
    """Tiny generated fixtures verify validation only; they are not real data."""
    def setUp(self):
        import numpy as np
        self.np = np
        self.path = Path('test-only-connectome')
        groups = ['GF', 'GF', 'LC4', 'LPLC2', 'DN', 'TTMn'] + ['other'] * 19
        self.metadata = [
            {'id': GF_IDS[i] if i < 2 else f'VFB_fixture_{i}', 'index': i, 'group': group}
            for i, group in enumerate(groups)
        ]
        self.connections = [
            {'source_id': GF_IDS[0], 'target_id': self.metadata[4]['id'], 'weight': 4},
            {'source_id': GF_IDS[1], 'target_id': self.metadata[5]['id'], 'weight': 3},
        ]
        self.matrix = np.zeros((25, 25), dtype=int)
        self.matrix[0, 4], self.matrix[1, 5] = 4, 3

    def validate_fixture(self, *, array_error=None):
        def read_json(path, *args, **kwargs):
            if path.name == 'neuron_metadata.json':
                return json.dumps(self.metadata)
            if path.name == 'connection_list.json':
                return json.dumps(self.connections)
            raise FileNotFoundError(path)
        with mock.patch.object(Path, 'read_text', autospec=True, side_effect=read_json):
            with mock.patch.object(self.np, 'load', return_value=self.matrix, side_effect=array_error):
                return validate_connectome(self.path)

    def test_consistent_fixture_and_mismatched_matrix(self):
        info = self.validate_fixture()
        self.assertEqual((info.neurons, info.directed_edges), (25, 2))
        self.matrix[0, 4] = 5
        with self.assertRaisesRegex(BrainSetupError, 'do not match'):
            self.validate_fixture()

    def test_dummy_size_is_rejected(self):
        self.metadata = self.metadata[:20]
        self.matrix = self.matrix[:20, :20]
        with self.assertRaisesRegex(BrainSetupError, 'dummy/incomplete'):
            self.validate_fixture()

    def test_missing_groups_and_motor_paths_are_rejected(self):
        self.metadata[2]['group'] = 'other'
        with self.assertRaisesRegex(BrainSetupError, 'groups are incomplete'):
            self.validate_fixture()
        self.metadata[2]['group'] = 'LC4'
        self.connections.pop()
        self.matrix[1, 5] = 0
        with self.assertRaisesRegex(BrainSetupError, 'no connection to a motor group'):
            self.validate_fixture()

    def test_gf_ids_must_actually_belong_to_gf_group(self):
        self.metadata[0]['group'] = 'other'
        self.metadata[6]['group'] = 'GF'
        with self.assertRaisesRegex(BrainSetupError, 'must belong to the GF group'):
            self.validate_fixture()

    def test_corrupt_array_is_reported_clearly(self):
        with self.assertRaisesRegex(BrainSetupError, 'Invalid Connectome data'):
            self.validate_fixture(array_error=EOFError())
        self.matrix = object()
        with self.assertRaisesRegex(BrainSetupError, 'Invalid Connectome data'):
            self.validate_fixture()


class BrainAdapterStepTests(unittest.TestCase):
    def test_exact_neurohex_call_and_output(self):
        backend = mock.Mock()
        backend.step.return_value = {'escape_magnitude': 0.75}
        adapter = NeuroHexBrainAdapter.__new__(NeuroHexBrainAdapter)
        adapter._brain = backend
        self.assertEqual(adapter.step(0.6), 0.75)
        backend.step.assert_called_once_with(visual_input=0.6, mechanosensory_input=0.0, duration_ms=20.0)

    def test_bad_inputs_outputs_and_backend_errors_are_explicit(self):
        backend = mock.Mock()
        adapter = NeuroHexBrainAdapter.__new__(NeuroHexBrainAdapter)
        adapter._brain = backend
        for value in (-1.0, 1.1, float('nan'), True):
            with self.subTest(value=value), self.assertRaises(BrainStepError):
                adapter.step(value)
        for result in ({}, {'escape_magnitude': float('nan')}, {'escape_magnitude': 1.1}, {'escape_magnitude': True}):
            backend.step.return_value = result
            with self.subTest(result=result), self.assertRaises(BrainStepError):
                adapter.step(0.5)
        backend.step.side_effect = RuntimeError('failed step')
        with self.assertRaisesRegex(BrainStepError, 'failed step'):
            adapter.step(0.5)


if __name__ == '__main__':
    unittest.main()
