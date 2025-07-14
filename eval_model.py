import argparse, glob, json, os, re, collections, torch
from torch_geometric.loader import DataLoader
from train_model_GNN import (
    ClauseResolutionDataset,
    EdgeClassifierGNN,
    build_graph_from_example,      # only needed if we changed the import path
)

# ---------- metrics helpers ---------------------------------
def edge_accuracy(model, loader, device):
    model.eval()
    hit, total = 0, 0
    with torch.no_grad():
        for data in loader:
            data = data.to(device)
            if data.y.numel() == 0:
                continue
            pred = model(data.x, data.edge_index).argmax(dim=1)
            hit  += (pred == data.y).sum().item()
            total += data.y.size(0)
    return hit / total if total else 0.0


def hits_at_1(model, dataset, device):
    """Return the fraction of graphs whose top-scored edge is a gold edge.
       Works even if there are multiple gold edges (e.g. forward + backward)."""
    loader = DataLoader(dataset, batch_size=1, shuffle=False)
    good = 0
    with torch.no_grad():
        for data in loader:
            data = data.to(device)
            # class-1 logit for every edge
            scores = model(data.x, data.edge_index)[:, 1]
            top_edge = scores.argmax().item()
            gold_edges = (data.y == 1).nonzero(as_tuple=True)[0]   # may be >1
            good += int(top_edge in gold_edges)
    return good / len(dataset)



def prf1(model, loader, device):
    from sklearn.metrics import precision_recall_fscore_support
    y_true, y_pred = [], []
    with torch.no_grad():
        for data in loader:
            data = data.to(device)
            if data.y.numel() == 0:
                continue
            logits = model(data.x, data.edge_index).argmax(dim=1)
            y_true.extend(data.y.cpu().numpy())
            y_pred.extend(logits.cpu().numpy())
    p, r, f, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=[1], average="binary", zero_division=0
    )
    return p, r, f


# ---------- main --------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, nargs="+",
                    help="folder(s) or file(s) with *.jsonl test data")
    ap.add_argument("--checkpoint", required=True,
                    help="model .pt file to load")
    ap.add_argument("--predicates", nargs="+", required=True,
                    help="same predicate list used at train time")
    args = ap.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Build dataset (uses the same class from train_,model.py)
    dataset = ClauseResolutionDataset(
        paths=args.data,
        predicate_list=args.predicates,
        max_args=8,
    )
    loader = DataLoader(dataset, batch_size=8, shuffle=False)

    # Restore model with the same input/output dims
    #model = EdgeClassifierGNN(in_dim=5, hidden_dim=64).to(device)
    # Restore model
    model = EdgeClassifierGNN(
        num_predicates=len(args.predicates),
        max_args=8,
        hidden_dim=64
    ).to(device)
    model.load_state_dict(torch.load(args.checkpoint, map_location=device))
    model.eval()

    # Metrics
    acc  = edge_accuracy(model, loader, device)
    hit1 = hits_at_1(model, dataset, device)
    p, r, f = prf1(model, loader, device)

    print(f"Edge accuracy : {acc:.3%}")
    print(f"Hits@1        : {hit1:.3%}")
    print(f"Positive edge – precision {p:.3%} | recall {r:.3%} | F1 {f:.3%}")


if __name__ == "__main__":
    main()

#python eval_model.py --data Dataset/Test_Res_Pairs_3 --checkpoint Models/gnn_model.pt --predicates convergent_lines unorthogonal_lines

#python eval_model.py --data Dataset/Test_Res_Pairs_4 --checkpoint Models/gnn_model3.pt --predicates pred1, pred2, pred3, pred4, pred5