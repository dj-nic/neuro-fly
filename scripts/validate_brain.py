"""Validate real reference data and measure an unmodified NeuroHex brain."""
import argparse
import platform
import collections
import importlib.util
import json
import pathlib
import resource
import time

import numpy as np
import brian2

PROJECT = pathlib.Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--reference', type=pathlib.Path, default=PROJECT.parent / 'neurohex-reference')
parser.add_argument('--output', type=pathlib.Path, default=PROJECT / 'artifacts/benchmark.json')
args = parser.parse_args()
ROOT = args.reference.resolve()
args.output.parent.mkdir(parents=True, exist_ok=True)
cache = PROJECT / 'artifacts/cache/cython'
cache.mkdir(parents=True, exist_ok=True)
DATA = ROOT / 'connectome_data'
metadata = json.loads((DATA / 'neuron_metadata.json').read_text())
connections = json.loads((DATA / 'connection_list.json').read_text())
matrix = np.load(DATA / 'adjacency_matrix.npy', allow_pickle=False)
n = len(metadata)
assert n > 20, 'Dummy or incomplete data'
assert matrix.shape == (n, n)
assert [m['index'] for m in metadata] == list(range(n))
ids = {m['id']: m['index'] for m in metadata}
assert len(ids) == n
assert all(m['id'].startswith('VFB_') for m in metadata)
assert {'VFB_jrmc30my', 'VFB_jrmc30mz'} <= ids.keys()
counts = collections.Counter(m['group'] for m in metadata)
assert counts['GF'] == 2 and counts['LC4'] and counts['LPLC2']
assert counts['DN'] and counts['TTMn']
expected = np.zeros_like(matrix)
for c in connections:
    assert c['weight'] >= 3
    expected[ids[c['source_id']], ids[c['target_id']]] += c['weight']
assert np.array_equal(matrix, expected)
for gf in ('VFB_jrmc30my', 'VFB_jrmc30mz'):
    assert any(matrix[ids[gf], m['index']] > 0 for m in metadata
               if m['group'] in ('DN', 'TTMn'))
print('Validated data:', n, 'neurons,', len(connections), 'connection records,',
      int(np.count_nonzero(matrix)), 'directed edges', flush=True)
print('Groups:', dict(counts), flush=True)

# Keep compilation caches outside the read-only home and the reference source.
brian2.prefs.codegen.runtime.cython.cache_dir = str(cache)
brian2.prefs.codegen.target = 'cython'
spec = importlib.util.spec_from_file_location('snn_brain', ROOT / 'snn_brain.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
started = time.perf_counter()
brain = module.NeuroHexBrain(connectome_dir=str(DATA))
initialization_s = time.perf_counter() - started
steps = []
outputs = []
approach_started = None
escape_latency_ms = None
loop_started = time.perf_counter()
for i, stimulus in enumerate([0.0] * 5 + [i / 20 for i in range(20)] + [1.0] * 10):
    started = time.perf_counter()
    if stimulus > 0 and approach_started is None:
        approach_started = started
    out = brain.step(visual_input=stimulus, mechanosensory_input=0.0, duration_ms=20.0)
    elapsed = (time.perf_counter() - started) * 1000
    magnitude = float(out['escape_magnitude'])
    assert np.isfinite(magnitude) and 0 <= magnitude <= 1
    steps.append(elapsed)
    outputs.append(magnitude)
    if magnitude > 0.5 and escape_latency_ms is None:
        escape_latency_ms = (time.perf_counter() - approach_started) * 1000
    print(f'Step {i}: input={stimulus:.2f} escape={magnitude:.4f} wall_ms={elapsed:.2f}', flush=True)
assert max(outputs[:5]) == 0, 'Unexpected resting motor output'
assert max(outputs[5:]) > 0.5, 'Strong stimulus did not trigger escape'
loop_wall_s = time.perf_counter() - loop_started
report = {
    'neurons': n, 'connection_records': len(connections), 'groups': dict(counts),
    'motor_neurons': len(brain.motor_indices), 'initialization_s': initialization_s,
    'first_step_ms_including_compilation': steps[0],
    'subsequent_step_mean_ms': float(np.mean(steps[1:])),
    'subsequent_step_p95_ms': float(np.percentile(steps[1:], 95)),
    'wall_to_simulated_time_ratio': float(np.mean(steps[1:]) / 20),
    'peak_rss_mib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024 * 1024 if platform.system() == 'Darwin' else 1024),
    'maximum_escape': max(outputs), 'platform': platform.platform(),
    'backend': str(brian2.prefs.codegen.target),
    'loop_wall_s': loop_wall_s, 'simulated_duration_s': len(steps) * 0.020,
    'loop_wall_to_simulated_ratio': loop_wall_s / (len(steps) * 0.020),
    'approach_to_escape_wall_ms': escape_latency_ms,
    'step_wall_ms': steps, 'escape_outputs': outputs,
}
args.output.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
