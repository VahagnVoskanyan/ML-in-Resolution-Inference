import argparse
import glob, json, re, os, random
from typing import Dict, List, Any, Sequence

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.data import Data, Dataset
from torch_geometric.loader import DataLoader
from torch_geometric.nn import SAGEConv
from torch_geometric.utils import to_undirected

##############################################################################
# 1)  Literal helpers (unchanged)
##############################################################################
def parse_literal(literal: str):
    sign = +1
    core = literal.strip()
    if core.startswith("¬") or core.startswith("~"):
        sign = -1
        core = core[1:].strip()
    pred = core.split("(", 1)[0]
    inside = core[len(pred) + 1 : -1].strip()
    args = [] if inside == "" else [x.strip() for x in inside.split(",")]
    return sign, pred, args


def embed_literal(
    literal: str, predicate_to_idx: Dict[str, int], max_args: int = 3
) -> torch.Tensor:
    sign, pred, args = parse_literal(literal)

    feat = [0 if sign > 0 else 1]                                  # sign bit
    feat.append(float(predicate_to_idx.get(pred, 0)))               # predicate ID

    arg_types: List[int] = []
    for arg in args[:max_args]:
        if "(" in arg and arg.endswith(")"):
            arg_types.append(2)          # function term
        elif arg and arg[0].isupper():
            arg_types.append(0)          # variable
        else:
            arg_types.append(1)          # constant

    arg_types += [-1] * (max_args - len(arg_types))                 # pad
    feat.extend(float(x) for x in arg_types)

    return torch.tensor(feat, dtype=torch.float)


##############################################################################
# 2)  Core graph builder  ––  *now handles best_pair_index automatically*
##############################################################################
def _extract_best_pair(example: Dict[str, Any]) -> Dict[str, Any] | None:
    """Return a dict with clause*/literal* keys, or None if unavailable."""
    if "best_pair" in example and example["best_pair"] is not None:
        return example["best_pair"]

    idx = example.get("best_pair_index", None)
    if idx is not None:
        rp = example["resolvable_pairs"]
        if 0 <= idx < len(rp):
            return rp[idx]
    return None


def build_graph_from_example(
    example: Dict[str, Any], predicate_to_idx: Dict[str, int], max_args: int = 3
) -> Data:
    clauses           = example["clauses"]
    resolvable_pairs  = example["resolvable_pairs"]
    best_pair         = _extract_best_pair(example)

    node_map, node_features, g_idx = {}, [], 0
    for ci, clause in enumerate(clauses):
        for li, lit in enumerate(clause[2]):                        # clause[2] is list‑of‑literals
            node_map[(ci, li)] = g_idx
            node_features.append(embed_literal(lit, predicate_to_idx, max_args))
            g_idx += 1

    x = torch.stack(node_features, dim=0)

    edge_src, edge_dst, labels = [], [], []
    for pair in resolvable_pairs:
        i, a = pair["clauseA_index"], pair["literalA_index"]
        j, b = pair["clauseB_index"], pair["literalB_index"]

        # ── skip malformed pairs ───────────────────────────────
        if a is None or b is None:
            continue
        if (i, a) not in node_map or (j, b) not in node_map:
            continue
        # ───────────────────────────────────────────────────────

        src, dst = node_map[(i, a)], node_map[(j, b)]
        edge_src.append(src)
        edge_dst.append(dst)

        is_best = (
            best_pair is not None
            and best_pair.get("literalA_index") is not None
            and best_pair.get("literalB_index") is not None
            and i == best_pair["clauseA_index"]
            and a == best_pair["literalA_index"]
            and j == best_pair["clauseB_index"]
            and b == best_pair["literalB_index"]
        )
        labels.append(1 if is_best else 0)

    if len(edge_src) == 0:
        # No candidate resolution pairs ⇒ skip the example
        problem_id = example.get("problem_id", "<unknown>")
        print(f"⚠️  example {problem_id} had no valid edges after cleaning.")
        return None                         # caller can filter out Nones
    
    edge_index = torch.tensor([edge_src, edge_dst], dtype=torch.long)
    # make the graph symmetric
    num_fwd = edge_index.size(1)            # how many edges we had
    edge_index = to_undirected(edge_index)  # adds the missing reverse ones
    added = edge_index.size(1) - num_fwd
    labels = labels + labels[:added]        # keep the same class for each twin
    y = torch.tensor(labels, dtype=torch.long)

    return Data(x=x, edge_index=edge_index, y=y)


##############################################################################
# 3)  Dataset that can read *either* a single file or a whole directory
##############################################################################
def _load_jsonl(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        # one JSON object per line *or* one object in the file
        first = f.readline()
        f.seek(0)
        if first.strip().startswith("{") and first.strip().endswith("}"):
            # could be exactly one object or many lines; json.loads will handle
            try:
                return [json.loads(line) for line in f]
            except json.JSONDecodeError:
                f.seek(0)
                return [json.load(f)]
        return []


class ClauseResolutionDataset(Dataset):
    def __init__(
        self,
        paths: Sequence[str],
        predicate_list: List[str] | None = None,
        max_args: int = 3,
        use_cache = True
    ):
        super().__init__(root=None)
        self.max_args = max_args

        self._cache_enabled = use_cache
        self._cache: dict[int, Data] = {} # (optional) cache

        # 1) Load *all* examples FIRST
        examples: list[dict[str, Any]] = []
        for p in paths:
            if os.path.isdir(p):
                for fn in glob.glob(os.path.join(p, "*.jsonl")):
                    examples.extend(_load_jsonl(fn))
            else:
                examples.extend(_load_jsonl(p))

        filtered: list[dict[str, Any]] = []
        for ex in examples:
            if _extract_best_pair(ex) is None:
                pid = ex.get("problem_id", "<unknown>")
                print(f"⏭️  skipping {pid} – best_pair is None")
                continue
            filtered.append(ex)

        self.examples = filtered

        # 2) Build predicate vocabulary
        if predicate_list:
            pred_list = predicate_list
        else:
            # auto-collect from the dataset
            seen: set[str] = set()
            for ex in examples:
                for _cid, _ctype, lits in ex["clauses"]:
                    for lit in lits:
                        m = re.match(r'\s*[~¬]?\s*([A-Za-z0-9_]+)\(', lit)
                        if m:
                            seen.add(m.group(1))
            pred_list = sorted(seen)              # stable order
        self.predicate_to_idx = {p: i + 1 for i, p in enumerate(pred_list)}

        self.examples = examples
        
    # PyG expects these exact names
    def len(self):           return len(self.examples)

    def get(self, idx: int) -> Data:
        if self._cache_enabled:
            if idx not in self._cache:
                self._cache[idx] = build_graph_from_example(
                    self.examples[idx],
                    self.predicate_to_idx,
                    self.max_args
                )
            return self._cache[idx]

        # caching disabled → always rebuild
        return build_graph_from_example(
            self.examples[idx],
            self.predicate_to_idx,
            self.max_args
        )

##############################################################################
# 4)  GNN model
##############################################################################
class EdgeClassifierGNN(torch.nn.Module):
    #def __init__(self, in_dim: int, hidden_dim: int = 64, out_dim: int = 2):
    """
    Node‑wise input:
       sign bit (float 0/1)
       predicate_id  ← will be turned into an embedding vector
       arg_type[0‥k-1] (floats 0/1/2 or –1 for PAD)
    Edge label: 0 = non‑best, 1 = best resolvable pair
    """
    def __init__(
        self,
        num_predicates: int,
        max_args: int,
        d_pred: int      = 16,   # embedding size
        hidden_dim: int  = 64,
        out_dim: int     = 2,
        dropout: float   = 0.20
    ):
        super().__init__()
        # 1) predicate embedding table (+1 for UNK / out‑of‑vocab)
        self.pred_embed = nn.Embedding(num_predicates + 1, d_pred)
        # 2) compute input feature length (sign + args + embed)
        numeric_dim = 1 + max_args                # we will drop the raw pred‑id
        in_dim      = numeric_dim + d_pred
        # 3) GNN trunk
        self.conv1   = SAGEConv(in_dim, hidden_dim, normalize=True)
        self.conv2   = SAGEConv(hidden_dim, hidden_dim, normalize=True)
        self.dropout = nn.Dropout(dropout)
        # 4) Edge‑score MLP
        self.edge_mlp = nn.Sequential(
            nn.Linear(2 * hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, out_dim)
        )

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        """
        x : (N , 2+max_args)  – raw node features from the dataset
        edge_index : (2 , E)  – PyG convention
        """
        # 1) split the feature cols
        sign_and_args = torch.cat([x[:, :1],   # sign
                                   x[:, 2: ]], dim=1)   # arg types
        pid_idx       = x[:, 1].long()                  # predicate column as ints
        pvec          = self.pred_embed(pid_idx)        # (N , d_pred)
        # 2) concatenate → full node feature
        h0 = torch.cat([sign_and_args, pvec], dim=1)    # (N , numeric+d_pred)
        # 3) message passing
        h = self.dropout(F.relu(self.conv1(h0, edge_index)))
        h = self.dropout(F.relu(self.conv2(h,  edge_index)))
        # 4) edge‑wise representation
        src, dst = edge_index
        edge_rep = torch.cat([h[src], h[dst]], dim=1)   # (E , 2*hidden_dim)
        return self.edge_mlp(edge_rep)                  # logits (E , 2)
    
    #     super().__init__()
    #     self.conv1 = SAGEConv(in_dim, hidden_dim)
    #     self.conv2 = SAGEConv(hidden_dim, hidden_dim)
    #     self.edge_mlp = torch.nn.Sequential(
    #         torch.nn.Linear(2 * hidden_dim, hidden_dim),
    #         torch.nn.ReLU(),
    #         torch.nn.Linear(hidden_dim, out_dim),
    #     )

    # def forward(self, x, edge_index):
    #     h = F.relu(self.conv1(x, edge_index))
    #     h = F.relu(self.conv2(h, edge_index))
    #     src, dst = edge_index
    #     edge_rep = torch.cat([h[src], h[dst]], dim=1)
    #     return self.edge_mlp(edge_rep)


##############################################################################
# 5)  Training helpers  (imbalanced‑loss aware)
##############################################################################
def split_dataset(dataset: Dataset, train_ratio=0.8):
    idx = list(range(len(dataset)))
    random.shuffle(idx)
    k = int(len(idx) * train_ratio)
    return (
        torch.utils.data.Subset(dataset, idx[:k]),
        torch.utils.data.Subset(dataset, idx[k:]),
    )


def train_one_epoch(model, loader, optimizer, device):
    model.train()
    total_loss = 0.0
    ce = torch.nn.CrossEntropyLoss(weight=torch.tensor([1.0, 3.0]).to(device))
    for batch in loader:
        batch = batch.to(device)
        if batch.y.numel() == 0:
            continue
        optimizer.zero_grad()
        loss = ce(model(batch.x, batch.edge_index), batch.y)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    return total_loss / max(1, len(loader))


def evaluate(model, loader, device):
    model.eval()
    correct = total = 0
    with torch.no_grad():
        for batch in loader:
            batch = batch.to(device)
            if batch.y.numel() == 0:
                continue
            pred = model(batch.x, batch.edge_index).argmax(dim=1)
            correct += (pred == batch.y).sum().item()
            total += batch.y.size(0)
    return correct / total if total else 0.0


##############################################################################
# 6)  Main entry (CLI)
##############################################################################
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True, nargs="+",
                        help="One or more .jsonl files or directories")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--init",  help="path to checkpoint to LOAD (optional)")
    parser.add_argument("--checkpoint", default="Models/gnn_model.pt")
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--predicates", nargs="+")
    args = parser.parse_args()

    args.predicates = ["pred1", "pred2", "pred3", "pred4", "pred5"]
    max_args = 8

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    dataset = ClauseResolutionDataset(
        paths=args.data,
        predicate_list=args.predicates,
        max_args=max_args,
        use_cache=True
    )
    train_set, test_set = split_dataset(dataset, train_ratio=0.8)
    train_loader = DataLoader(train_set, batch_size=8, shuffle=True)
    test_loader  = DataLoader(test_set,  batch_size=8)

    num_preds = len(dataset.predicate_to_idx)      # vocabulary size
    model = EdgeClassifierGNN(num_predicates=num_preds,
            max_args=max_args, hidden_dim=64).to(device)
    load_path = args.init if args.init else (
    args.checkpoint if os.path.exists(args.checkpoint) else None
    )
    if load_path:
        model.load_state_dict(torch.load(load_path, map_location=device))
    print(f"✓ Loaded weights from {load_path}")
    # if os.path.exists(args.checkpoint):
    #     model.load_state_dict(torch.load(args.checkpoint, map_location=device))
    #     print(f"✓ Loaded checkpoint “{args.checkpoint}”")

    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)

    for epoch in range(1, args.epochs + 1):
        loss = train_one_epoch(model, train_loader, optimizer, device)
        tr_acc = evaluate(model, train_loader, device)
        te_acc = evaluate(model, test_loader,  device)
        print(f"[{epoch:02d}] loss {loss:.4f} | train {tr_acc:.3f} | test {te_acc:.3f}")

    os.makedirs(os.path.dirname(args.checkpoint), exist_ok=True)
    torch.save(model.state_dict(), args.checkpoint)
    print(f"✓ Saved updated model to “{args.checkpoint}”")


if __name__ == "__main__":
    main()

#If we still want a single mega‑file (e.g. for archival or cross‑tool sharing):
# import glob, json, sys, os

# out = "merged_dataset.jsonl"
# paths = sys.argv[1:] or ["*.jsonl"]

# with open(out, "w", encoding="utf-8") as fout:
#     for p in paths:
#         for fn in glob.glob(p):
#             obj = json.load(open(fn, "r", encoding="utf-8"))
#             idx = obj.pop("best_pair_index", None)
#             obj["best_pair"] = (
#                 obj["resolvable_pairs"][idx] if idx is not None else None
#             )
#             fout.write(json.dumps(obj, ensure_ascii=False) + "\n")

# print(f"Merged → {out}")

# Train from scratch on every JSONL in the current directory
# python train_model_GNN.py --data Res_Pairs_Copy --epochs 50 --lr 1e-3 --checkpoint Models/gnn_model4.pt
# python train_model_GNN.py --data Res_Pairs --epochs 30 --lr 1e-3 --checkpoint Models/gnn_model3.pt

# Keep overwriting the same file
# python train_model_GNN.py --data Res_Pairs --epochs 5 --lr 1e-4 --checkpoint Models/gnn_model.pt

# Fine‑tune and save as a new file
# python train_model_GNN.py --data Res_Pairs --epochs 30 --lr 1e-6 --init Models/gnn_model1.pt --checkpoint Models/gnn_model2.pt


# Predicate Names
#product defined identity_map domain codomain compose equivalent there_exists f1