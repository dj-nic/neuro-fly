"""Rebuild the print set. Python 3.9+ and OpenSCAD 2021.01+."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import argparse
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent.parent
PARTS = {
    1: "base_bottom", 2: "base_lid", 3: "servo_mount_mg996r", 4: "swing_arm",
    5: "servo_horn_adapter", 6: "fly_body", 8: "fly_wing_left", 9: "fly_wing_right",
    10: "fly_arm_connector", 11: "sensor_mount", 12: "axis_support", 13: "axis_pin_hub",
    14: "guard_rear", 15: "guard_spacer", 16: "servo_cable_guide", 21: "servo_flange_fit",
    22: "horn_fit", 23: "bearing_fit", 24: "fastener_fit",
}

def export(item, exe):
    number, name = item
    dest = ROOT / ("TESTDRUCK" if number >= 20 else "STL") / f"{number:02d}_{name}.stl"
    dest.parent.mkdir(exist_ok=True)
    tmp = dest.with_suffix(".tmp.stl")
    cmd = [exe, "--export-format", "binstl", "-D", f"part={number}", "-o", str(tmp),
           str(ROOT / "CAD" / "NeuroFly.scad")]
    result = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    if result.returncode or "WARNING:" in result.stderr or "ERROR:" in result.stderr:
        raise RuntimeError(f"{name}\n{result.stderr}")
    tmp.replace(dest)
    print(dest.name, flush=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--openscad", default=shutil.which("openscad"))
    parser.add_argument("--part", type=int, choices=PARTS)
    args = parser.parse_args()
    if not args.openscad:
        parser.error("Supply the OpenSCAD executable using --openscad PATH.")
    selected = {args.part: PARTS[args.part]} if args.part else PARTS
    with ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(lambda item: export(item, args.openscad), selected.items()))
