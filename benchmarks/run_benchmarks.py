import os
import re
import csv
import subprocess
from pathlib import Path

# === Paths ===
SPELL_PATH = Path("/Users/helenawendler/Documents/TU/07_Semester_2025W/PR_Bkk/spell-cardinality-extension")
BENCHMARKS_ROOT = Path("/Users/helenawendler/Documents/TU/07_Semester_2025W/PR_Bkk/05_Evaluation/SPELL-benchmarks-main")

# === Output file ===
OUTPUT_CSV = SPELL_PATH / "spell-maj-benchmark_results.csv"

# === CSV Header ===
header = [
    "Version",
    "Dataset",
    "Coverage IS",
    "Coverage GOAL",
    "Coverage %",
    "Query Size",
    "Running Time",
    "Majority (y/n)",
    "Query"
]

def extract_info(stdout: str):
    """Extract coverage, time, query and majority info from stdout."""
    coverage_is = coverage_goal = coverage_pct = query_size = running_time = "NA"
    query_str = "NA"
    majority_flag = "n"

    coverage_match = re.search(r"coverage\s+(\d+)/(\d+)", stdout)
    time_match = re.search(r"Took\s+([\d.]+)s.*?([\d.]+)s", stdout)
    query_match = re.search(r"(SELECT DISTINCT.*?WHERE\s*{.*?})", stdout, re.DOTALL)

    if coverage_match:
        coverage_is = coverage_match.group(1)
        coverage_goal = coverage_match.group(2)
        pct = (int(coverage_is) / int(coverage_goal)) * 100 if int(coverage_goal) != 0 else 0
        coverage_pct = f"{pct:.2f}%"

    if time_match:
        total_time = float(time_match.group(1)) + float(time_match.group(2))
        running_time = f"{total_time:.3f}"

    if query_match:
        query_str = query_match.group(1).strip().replace("\n", " ")
        query_size = compute_query_size(query_match.group(1))
        # Detect if MAJ occurs in the query
        if "MAJ" in query_str:
            majority_flag = "y"

    return coverage_is, coverage_goal, coverage_pct, query_size, running_time, majority_flag, query_str


def run_benchmark(bench_dir: Path, writer):
    """Run a single benchmark."""
    name = bench_dir.name
    owl_file = bench_dir / "owl" / "data" / f"{name}.owl"
    pos_file = bench_dir / "owl" / "lp" / "1" / "pos.txt"
    neg_file = bench_dir / "owl" / "lp" / "1" / "neg.txt"

    if not owl_file.exists() or not pos_file.exists() or not neg_file.exists():
        print(f"Missing file in {bench_dir}")
        return

    print(f"Running benchmark: {name}")

    process = subprocess.run(
        ["python3.10", str(SPELL_PATH / "spell_cli.py"), str(owl_file), str(pos_file), str(neg_file)],
        capture_output=True,
        text=True
    )

    coverage_is, coverage_goal, coverage_pct, query_size, running_time, majority_flag, query_str = extract_info(process.stdout)

    writer.writerow([
        "SPELL-MAJ",
        f"{name}.owl",
        coverage_is,
        coverage_goal,
        coverage_pct,
        query_size,
        running_time,
        majority_flag,
        query_str
    ])

def compute_query_size(query_str):
    """
    Compute query size as number of existential variables + 1
    """
    lines = query_str.splitlines()
    vars_set = set()
    for line in lines:
        # match triples like "?0 <prop> ?1"
        match = re.findall(r'\?[\w\d]+', line)
        if match:
            # alle Variablen außer der ersten (Startvariable) zählen als Existenzquantoren
            vars_set.update(match)
    if not vars_set:
        return "NA"
    # Query size = (#existential variables) + 1
    # Existential variables = alle Variablen außer der Startvariable (?0)
    size = len(vars_set) - 1 + 1  # = len(vars_set)
    return str(size)



def main():
    with open(OUTPUT_CSV, mode="w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(header)

        for subfolder in ["owl2bench", "strength-weakness", "yago-gen", "yago-perf"]:
            folder_path = BENCHMARKS_ROOT / subfolder
            if not folder_path.exists():
                print(f" Skip: {folder_path} (directory not found)")
                continue

            print(f"\nChecking folder: {folder_path}")

            for bench_dir in sorted(folder_path.glob("*")):
                if bench_dir.is_dir():
                    run_benchmark(bench_dir, writer)

    print(f"\nDone! Results saved in:\n{OUTPUT_CSV}")


if __name__ == "__main__":
    main()

