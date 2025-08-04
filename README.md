# ML-in-Resolution-Inference

> **Using Machine Learning to Improve the Time Complexity of Resolution-Based Theorem Proving**  
> Master's Thesis Project by Vahagn Voskanyan

---

## 📘 Overview

This project combines classical logic with modern machine learning to enhance the performance of **resolution-based theorem provers**. It includes a full pipeline that:

- Generates synthetic logic problems in TPTP format.
- Performs unification and resolution on clauses.
- Builds a supervised learning dataset using automated ATP tools (like Vampire).
- Trains a **Graph Neural Network (GNN)** model to guide the resolution process.
- Compares traditional and ML-guided resolution strategies.

---

## 🧠 Architecture Summary

```
Synthetic Axioms + Conjectures
        │
        ▼
 Resolution Pipeline (Unification + Clause Pairing)
        │
        ▼
 JSONL Dataset Creation (resolvable_pairs + best_pair)
        │
        ▼
    Proof Solver (Vampire via Docker)
        │
        ▼
Label Extraction → Labeled Dataset
        │
        ▼
      GNN Model (GraphSAGE)
        │
        ▼
Guided Resolution + Evaluation
```

---

## 📁 Project Structure

```
ML-in-Resolution-Inference/
│
├── generate_axioms.py            # Creates synthetic axioms with predicates, functions
├── generate_problems.py          # Generates synthetic problems with negated conjectures
├── unification_resolution.py     # Literal unification and resolution logic
├── solve_problems_ATP.py         # Runs Vampire ATP in Docker on problems
├── extract_literals_from_solution.py  # Extracts clause pairs from proof trace
├── scoring_and_dataset_gnn_1.py  # Builds labeled dataset (resolvable_pairs + best_pair)
├── train_model.py                # Trains GNN to classify resolvable clause pairs
├── compare_solvers.py            # Evaluates GNN-guided vs brute-force resolution
│
├── Res_Pairs/                    # JSONL training data (clauses, labels)
├── Gen_Problems/                 # .p TPTP-formatted synthetic problems
├── Output/                       # Vampire ATP outputs
├── Models/                       # Saved GNN model checkpoints
└── requirements.txt              # Dependencies
```

---

## 🔧 Installation

```bash
git clone https://github.com/VahagnVoskanyan/ML-in-Resolution-Inference.git
cd ML-in-Resolution-Inference
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 🚀 Usage

### 1. Generate Synthetic Data
```bash
python _1_generate_axioms.py
python _2_create_problem_examples.py
```

### 2. Solve with Vampire (Docker required)
```bash
python _3_solve_problems_using_ATP.py
```

### 3. Find candidate resolvable pairs
```bash
python _4_resolvable_pair_finder.py
```

### 4. Extract best clause pairs from proofs
```bash
python _5_extract_literals_from_solution.py
```

### 5. Train GNN Model
```bash
python _6_train_model_GNN.py --data Res_Pairs --epochs 30 --lr 1e-3 --checkpoint Models/gnn_model.pt
```

---

## 🧪 Resolution Strategy Comparison

| Metric                         | Brute Force | GNN-Guided |
|-------------------------------|-------------|------------|
| Avg. Resolution Steps         | Higher      | Lower      |
| Proof Success Rate            | Similar     | Higher on hard cases |
| Speedup on Complex Problems   | ❌          | ✅          |

---

## 📊 GNN Model Summary

- **Architecture**: GraphSAGE with two `SAGEConv` layers and edge classification MLP
- **Input**: Literal pair vectors (sign, predicate embedding, argument types)
- **Output**: Best resolvable clause pair
- **Accuracy**: ~93% test accuracy on unseen examples
- **Hardware Support**: CPU and GPU via PyTorch Geometric

---

## 🧬 Data Format Example

```json
{
  "clauses": [[...], [...], ...],
  "resolvable_pairs": [[0,1,2,0], [1,0,3,2], ...],
  "best_pair": [0,1,2,0]
}
```

---

## 📦 Requirements

- Python 3.8+
- `torch`, `torch-geometric`, `networkx`, `numpy`, `pandas`
- Docker (for Vampire ATP execution)

---

## 📌 Notes

- Vampire is run inside Docker and outputs full proof traces.
- Generated data is fully synthetic and not domain-specific.
- Clause unification avoids trivial contradictions and redundancy.
- JSONL format enables efficient streaming and training with PyTorch/TensorFlow.
