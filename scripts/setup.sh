#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
reference_dir="${REFERENCE_DIR:-$(dirname "$project_dir")/neurohex-reference}"
venv_dir="${VENV_DIR:-$project_dir/.venv}"
reference_commit=5d1052b995db12fa1baf8d42f6a94c3f0695817d

if [[ ! -e "$reference_dir" ]]; then
    git clone --depth 1 --no-checkout https://github.com/shakeabhishek/project-neurohex.git "$reference_dir"
    git -C "$reference_dir" fetch --depth 1 origin "$reference_commit"
    git -C "$reference_dir" checkout --detach "$reference_commit"
fi
if [[ "$(git -C "$reference_dir" rev-parse --verify 'HEAD^{commit}')" != "$reference_commit" ]]; then
    echo "Referenz hat einen anderen Commit; bestehenden Checkout unverändert gelassen." >&2
    exit 1
fi

export CC="${CC:-gcc}" CXX="${CXX:-g++}"
export MPLBACKEND=Agg MPLCONFIGDIR="$project_dir/artifacts/matplotlib"
export PIP_CACHE_DIR="$project_dir/artifacts/cache/pip"
export XDG_CACHE_HOME="$project_dir/artifacts/cache"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
mkdir -p "$MPLCONFIGDIR" "$PIP_CACHE_DIR"
python3 -m venv "$venv_dir"
"$venv_dir/bin/python" -m pip install -r "$project_dir/requirements-dev.lock"
"$venv_dir/bin/python" -m pip check
if [[ ! -f "$reference_dir/connectome_data/adjacency_matrix.npy" || ! -f "$reference_dir/connectome_data/neuron_metadata.json" || ! -f "$reference_dir/connectome_data/connection_list.json" ]]; then
    "$venv_dir/bin/python" -u "$reference_dir/fetch_connectome.py"
fi
"$venv_dir/bin/python" -u "$project_dir/scripts/validate_brain.py" --reference "$reference_dir" --output "$project_dir/artifacts/benchmark.json"
