import subprocess
import os

output_dir = r'C:\\Users\\vahag\\Desktop\\BaseFolder\\University\\Thesis\\GitFiles1\\Generator_04_09\\Gen_Problems_Clausified'
input_dir = r'C:\\Users\\vahag\\Desktop\\BaseFolder\\University\\Thesis\\GitFiles1\\Generator_04_09\\Gen_Problems'

#output_dir = r'C:\\Users\\USER\\Desktop\\Thesis\\Resolution1\\Generator_04_09\\Gen_Problems_Copy'
#input_dir = r'C:\\Users\\USER\\Desktop\\Thesis\\Resolution1\\Generator_04_09\\Gen_Problems'
os.makedirs(output_dir, exist_ok=True)

command = [
    "docker", "run", "--rm", "-it",
    "-v", f"{input_dir}:/vampire/examples/Axioms",
    "-v", f"{output_dir}:/vampire/examples/Output",
    "--name", "vampire_clausify", "vahagn22/vampire",
    "/bin/bash", "-c",
    (
        'for f in /vampire/examples/Axioms/*.p; do '
        'base=$(basename "$f" .p); '
        'echo "Clausifing ${base}.p…"; '
        './vampire --mode clausify -t 100 "$f" > /vampire/examples/Output/"${base}".p; '
        'done'
    )
]

# Run the command
subprocess.run(command)


# import os
# import json

# def renumber_clause_ids_in_file(file_path):
#     # Read & parse all lines first
#     with open(file_path, 'r', encoding='utf-8') as f:
#         lines = f.readlines()

#     updated_lines = []
#     for line in lines:
#         data = json.loads(line)

#         # 1) Build mapping old_id → sequential new_id (u1, u2, …)
#         clauses = data.get("clauses", [])
#         id_map = {}
#         for idx, clause in enumerate(clauses, start=1):
#             old_id = clause[0]
#             new_id = f"u{idx}"
#             id_map[old_id] = new_id
#             clause[0] = new_id

#         # 2) If you have IDs elsewhere (e.g. in resolvable_pairs/best_pair), recurse and remap
#         # def remap_ids(obj):
#         #     if isinstance(obj, dict):
#         #         for k, v in obj.items():
#         #             if isinstance(v, str) and v in id_map:
#         #                 obj[k] = id_map[v]
#         #             else:
#         #                 remap_ids(v)
#         #     elif isinstance(obj, list):
#         #         for item in obj:
#         #             remap_ids(item)

#         # for key in ("resolvable_pairs", "best_pair_index"):
#         #     if key in data:
#         #         remap_ids(data[key])

#         # Push the rewritten object back into our output buffer:
#         updated_lines.append(json.dumps(data, ensure_ascii=False) + "\n")

#     # 3) Overwrite the same file
#     with open(file_path, 'w', encoding='utf-8') as f:
#         f.writelines(updated_lines)

# def renumber_folder(folder_path):
#     for fname in os.listdir(folder_path):
#         if fname.endswith(".jsonl"):
#             full_path = os.path.join(folder_path, fname)
#             renumber_clause_ids_in_file(full_path)
#             print(f"Rewritten: {full_path}")

# if __name__ == "__main__":
#     folder = "Res_Pairs"
#     renumber_folder(folder)
