"""Limit a subprocess group to a duty fraction of one CPU, without root.

SIGSTOP/SIGCONT enforce the budget; this does not emulate ARM hardware.
Usage: python cpu_limit.py FRACTION COMMAND [ARGS...]
"""
import os
import signal
import subprocess
import sys
import time

fraction = float(sys.argv[1])
assert 0 < fraction <= 1
cpus = sorted(os.sched_getaffinity(0))
target_cpu = cpus[0]
if len(cpus) > 1:
    os.sched_setaffinity(0, cpus[1:])
child = subprocess.Popen(['taskset', '-c', str(target_cpu), *sys.argv[2:]], start_new_session=True)
period = 0.010
try:
    deadline = time.monotonic()
    while child.poll() is None:
        deadline += period
        os.killpg(child.pid, signal.SIGCONT)
        time.sleep(period * fraction)
        os.killpg(child.pid, signal.SIGSTOP)
        time.sleep(max(0, deadline - time.monotonic()))
except ProcessLookupError:
    pass
finally:
    try:
        os.killpg(child.pid, signal.SIGCONT)
    except ProcessLookupError:
        pass
    # On interrupted runs never leave a paused orphan behind.
    if sys.exc_info()[0] is not None and child.poll() is None:
        os.killpg(child.pid, signal.SIGTERM)
    status = child.wait()
sys.exit(status if status >= 0 else 128 - status)
