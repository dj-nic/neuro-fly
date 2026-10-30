"""Run a recorded mock sensor through the real NeuroHex model and mock output."""

import argparse
import json
from pathlib import Path
import sys
import time

from .brain import BrainSetupError, BrainStepError, DEFAULT_REFERENCE, NeuroHexBrainAdapter
from .output import MockOutput, PulseController
from .pipeline import Pipeline, make_report, run_pipeline
from .sensor import ApproachEncoder, MockDistanceSensor


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    demo = commands.add_parser("demo", help="run a finite synthetic distance recording")
    demo.add_argument("--scenario", choices=MockDistanceSensor.SCENARIOS, default="approach")
    demo.add_argument("--reference", type=Path, default=DEFAULT_REFERENCE,
                      help="separate pinned NeuroHex checkout (default: ../neurohex-reference)")
    demo.add_argument("--report", type=Path, help="optional JSON report path")
    args = parser.parse_args(argv)
    wall_started = time.monotonic()
    cpu_started = time.process_time()
    try:
        brain = NeuroHexBrainAdapter(args.reference)
        sensor = MockDistanceSensor(args.scenario)
        output = MockOutput()
        controller = PulseController(output)
        pipeline = Pipeline(sensor, ApproachEncoder(), brain, controller)
        cycles, overruns = run_pipeline(pipeline)
        report = make_report(
            scenario=args.scenario, brain=brain, output=output, controller=controller,
            cycles=cycles, overruns=overruns, wall_s=time.monotonic() - wall_started,
            cpu_s=time.process_time() - cpu_started,
        )
        if args.report is not None:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
        print(f"Scenario: {args.scenario}; cycles: {len(cycles)}; SNN-triggered pulses: {controller.trigger_count}")
        print(f"Simulated neural time: {report['simulated_duration_s']:.3f} s; wall time: {report['wall_duration_s']:.3f} s")
        print(f"20-ms cycle overruns: {overruns}; sensor and output are simulated")
        if args.report is not None:
            print(f"Report: {args.report}")
        return 0
    except (BrainSetupError, BrainStepError, ValueError, OSError, RuntimeError, TimeoutError) as exc:
        print(f"Demo failed: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Demo interrupted; output deactivated.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
