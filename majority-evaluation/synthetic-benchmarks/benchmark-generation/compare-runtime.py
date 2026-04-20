import subprocess
import re
import csv
from pathlib import Path
import sys

# Import your generators
from generate_depth_test_instances import generate_depth_test
from generate_conj_test_instances import generate_rdf_owl

# Spell location (relative to this script)
SPELL = ["python", "../../spell_cli.py"]

# Paths to OWL files and P/N.txt
DATA_DIR = Path("synthetic-benchmarks")  # subfolder containing P/N.txt and OWL folders
DEPTH_DIR = DATA_DIR / "depth-test-instances"
CONJ_DIR  = DATA_DIR / "conj-test-instances"
P_FILE_DEPTH    = DATA_DIR / "depth-test-instances/P.txt"
N_FILE_DEPTH   = DATA_DIR / "depth-test-instances/N.txt"
P_FILE_CONJ    = DATA_DIR / "conj-test-instances/P.txt"
N_FILE_CONJ  = DATA_DIR / "conj-test-instances/N.txt"

# Ensure output folders exist
DEPTH_DIR.mkdir(parents=True, exist_ok=True)
CONJ_DIR.mkdir(parents=True, exist_ok=True)

# Regex to parse SPELL output
TIME_REGEX = re.compile(r"\s*([0-9.]+)s for solving", re.IGNORECASE)
COVERAGE_REGEX = re.compile(r"Coverage:\s*([0-9]+/[0-9]+)", re.IGNORECASE)

RESULTS_FILE = "benchmark_results.csv"

def run_spell(owl_file, bool_depth):
    cmd_DEPTH = SPELL + [str(owl_file), str(P_FILE_DEPTH), str(N_FILE_DEPTH)]
    cmd_CONJ = SPELL + [str(owl_file), str(P_FILE_CONJ), str(N_FILE_CONJ)]

    if bool_depth:
        try:
            # Run SPELL, capture both stdout and stderr
            result = subprocess.run(cmd_DEPTH, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
            output = result.stdout
            errors = result.stderr

            print("---- SPELL OUTPUT ----")
            print(output)
            print("---------------------")

            # Print everything to see what SPELL is doing
            print(f"\n=== Running SPELL on {owl_file} ===")
            print("Command:", " ".join(cmd_DEPTH))
            print("--- STDOUT ---")
            print(output.strip() or "<no output>")
            print("--- STDERR ---")
            print(errors.strip() or "<no errors>")
            print("--- END OUTPUT ---\n")

            # Extract solving time
            time_match = TIME_REGEX.search(output + errors)
            solve_time = float(time_match.group(1)) if time_match else None

            # Extract coverage
            cov_match = COVERAGE_REGEX.search(output + errors)
            coverage = cov_match.group(1) if cov_match else "?"

            return solve_time, coverage, output + errors

        except Exception as e:
            print(f"ERROR running SPELL on {owl_file}: {e}")
            return None, "?", ""
    else:
        try:
            # Run SPELL, capture both stdout and stderr
            result = subprocess.run(cmd_CONJ, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
            output = result.stdout
            errors = result.stderr

            print("---- SPELL OUTPUT ----")
            print(output)
            print("---------------------")

            # Print everything to see what SPELL is doing
            print(f"\n=== Running SPELL on {owl_file} ===")
            print("Command:", " ".join(cmd_CONJ))
            print("--- STDOUT ---")
            print(output.strip() or "<no output>")
            print("--- STDERR ---")
            print(errors.strip() or "<no errors>")
            print("--- END OUTPUT ---\n")

            # Extract solving time
            time_match = TIME_REGEX.search(output + errors)
            solve_time = float(time_match.group(1)) if time_match else None

            # Extract coverage
            cov_match = COVERAGE_REGEX.search(output + errors)
            coverage = cov_match.group(1) if cov_match else "?"

            return solve_time, coverage, output + errors

        except Exception as e:
            print(f"ERROR running SPELL on {owl_file}: {e}")
            return None, "?", ""

def run_depth(n):
    owl_path = DEPTH_DIR / f"depth-{n}.owl"
    rdf = generate_depth_test(n)
    owl_path.write_text(rdf)
    return run_spell(owl_path, 1)

def run_conjunction(n):
    owl_path = CONJ_DIR / f"conj-{n}.owl"
    rdf = generate_rdf_owl(n)
    owl_path.write_text(rdf)
    return run_spell(owl_path, 0)

def main():
    with open(RESULTS_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["size", "type", "solve_time", "coverage"])

        for n in range(1, 41):
            print(f"\n=== Running size {n} ===")

            # Depth test
            t, cov, out = run_depth(n)
            print(f"Depth {n}: {t}s, coverage {cov}")
            writer.writerow([n, "depth", t, cov])

            # Conjunction test
            t, cov, out = run_conjunction(n)
            print(f"Conjunction {n}: {t}s, coverage {cov}")
            writer.writerow([n, "conjunction", t, cov])

    print("\nBenchmark complete →", RESULTS_FILE)

if __name__ == "__main__":
    main()
