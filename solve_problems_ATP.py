import subprocess
import os

def run_docker_solve_command():
    output_dir = r'C:\\Users\\vahag\\Desktop\\BaseFolder\\University\\Thesis\\GitFiles1\\Generator_04_09\\Output'
    input_dir = r'C:\\Users\\vahag\\Desktop\\BaseFolder\\University\\Thesis\\GitFiles1\\Generator_04_09\\Gen_Problems_Copy'
    
    #output_dir = r'C:\\Users\\USER\\Desktop\\Thesis\\Resolution1\\Generator_04_09\\Output'
    #input_dir = r'C:\\Users\\USER\\Desktop\\Thesis\\Resolution1\\Generator_04_09\\Gen_Problems'
    #input_dir = r'C:\\Users\\USER\\Desktop\\Thesis\\Resolution1\\Generator_04_09\\Gen_Problems_Copy'
    os.makedirs(output_dir, exist_ok=True)

    command = [
        "docker", "run", "-it", "--rm",
        "-v", f"{input_dir}:/vampire/examples/Gen_Problems",
        "-v", f"{output_dir}:/vampire/examples/Output",
        "--name", "vampire_solve", "vahagn22/vampire",
        "/bin/bash", "-c",
        # (
        #     'for f in /vampire/examples/Gen_Problems/*.p; do '
        #     'base=$(basename "$f" .p); '
        #     './vampire --mode casc --proof_extra full  -t 100 "$f" > /vampire/examples/Output/"${base}"_solved.txt; '
        #     'done'
        # )
        (
            'for f in /vampire/examples/Gen_Problems/*.p; do '
              'base=$(basename "$f" .p); '
              'echo "Solving ${base}.p…"; '
              './vampire --mode casc --proof_extra full -t 100 "$f" '
                '> /vampire/examples/Output/"${base}"_solved.txt; '
            'done'
        )
    ]

    # command = [
    #     "docker", "run", "-it",
    #     "-v", f"{input_dir}:/vampire/examples/Gen_Problems",
    #     "-v", f"{output_dir}:/vampire/examples/Output",
    #     "--name", "vampire_clausify", "vampire",
    #     "/bin/bash", "-c",
    #     (
    #         'for f in /vampire/examples/Gen_Problems/*.p; do '
    #         'base=$(basename "$f" .p); '
    #         './vampire --mode casc --proof_extra full -t 100 "$f" | tee /vampire/examples/Output/"${base}"_solved.txt; '
    #         'done'
    #     )
    # ]

    # Run the command
    subprocess.run(command)

if __name__ == '__main__':
    run_docker_solve_command()