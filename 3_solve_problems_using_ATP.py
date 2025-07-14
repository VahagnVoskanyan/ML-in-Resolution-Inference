import subprocess
import os
import constants

# Runs Vampire in Docker to solve generated probelms
def run_solve_command():
    input_dir = constants.GENERATED_PROBLEM_FULL
    output_dir = constants.SOLVED_PROBLEM_FULL

    os.makedirs(output_dir, exist_ok=True)

    command = [
        "docker", "run", "-it", "--rm",
        "-v", f"{input_dir}:/vampire/examples/Gen_Problems",
        "-v", f"{output_dir}:/vampire/examples/Output",
        "--name", "vampire_solve", "vahagn22/vampire",
        "/bin/bash", "-c",
        (
            'for f in /vampire/examples/Gen_Problems/*.p; do '
              'base=$(basename "$f" .p); '
              'echo "Solving ${base}.p…"; '
              './vampire --mode casc --proof_extra full -t 100 "$f" '
                '> /vampire/examples/Output/"${base}"_solved.txt; '
            'done'
        )
    ]

    subprocess.run(command)

if __name__ == '__main__':
    run_solve_command()