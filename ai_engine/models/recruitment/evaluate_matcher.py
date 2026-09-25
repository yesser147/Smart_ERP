"""
Measures the CV matcher on a public labelled data set:
huggingface.co/datasets/cnamuangtoun/resume-job-description-fit
(resume / job description pairs labelled No Fit, Potential Fit, Good Fit).

    python -m models.recruitment.evaluate_matcher                  # embedding signal, 300 pairs
    python -m models.recruitment.evaluate_matcher --pairs 600
    python -m models.recruitment.evaluate_matcher --llm 30         # + LLM judgment on 30 pairs (slow)

Reported: ROC-AUC "Good Fit vs No Fit" and Spearman correlation with the
ordinal label (0 / 1 / 2) for each signal, plus the similarity range to use
for EMB_LOW / EMB_HIGH in matcher.py. Nothing is written to the database.
"""

import argparse
import json

import numpy as np
import requests
from sklearn.metrics import roc_auc_score
from scipy.stats import spearmanr

from embeddings import get_model
from models.recruitment.llm_client import generate_json

DATASET = "cnamuangtoun/resume-job-description-fit"
ROWS_API = "https://datasets-server.huggingface.co/rows"
LABELS = {"No Fit": 0, "Potential Fit": 1, "Good Fit": 2}


def download(split: str, n: int, seed: int) -> list[dict]:
    """Fetches n rows spread over the split (the API serves 100 rows per call)."""
    info = requests.get(ROWS_API, params={"dataset": DATASET, "config": "default", "split": split,
                                          "offset": 0, "length": 1}, timeout=60).json()
    total = info["num_rows_total"]
    rng = np.random.default_rng(seed)
    offsets = sorted(set(rng.integers(0, max(1, total - 100), size=max(1, n // 50)).tolist()))
    rows = []
    for off in offsets:
        page = requests.get(ROWS_API, params={"dataset": DATASET, "config": "default", "split": split,
                                              "offset": int(off), "length": 100}, timeout=60).json()
        rows.extend(r["row"] for r in page.get("rows", []))
        if len(rows) >= n * 2:
            break
    rng.shuffle(rows)
    return [r for r in rows if r.get("label") in LABELS][:n]


def embedding_similarity(pairs: list[dict]) -> np.ndarray:
    model = get_model()
    resumes = model.encode([p["resume_text"][:1500] for p in pairs], normalize_embeddings=True, batch_size=32)
    jobs = model.encode([p["job_description_text"][:1500] for p in pairs], normalize_embeddings=True, batch_size=32)
    return np.sum(resumes * jobs, axis=1) * 100


def llm_judgment(pair: dict) -> float | None:
    prompt = f"""Score from 0 to 100 how well this candidate fits this job. A career in an unrelated field
must score below 25. Return ONLY a JSON object: {{"score": 0}}

JOB DESCRIPTION:
{pair['job_description_text'][:2500]}

RESUME:
{pair['resume_text'][:3000]}"""
    try:
        return float(generate_json(prompt, temperature=0.0, timeout=120).get("score"))
    except Exception as e:
        print(f"  LLM failed on one pair: {e}")
        return None


def report(name: str, scores: np.ndarray, labels: np.ndarray):
    mask = ~np.isnan(scores)
    s, y = scores[mask], labels[mask]
    binary = (y == 0) | (y == 2)
    auc = roc_auc_score(y[binary] == 2, s[binary]) if len(set(y[binary])) == 2 else float("nan")
    rho = spearmanr(s, y).statistic
    print(f"{name:28s} pairs={mask.sum():4d}  AUC(Good vs No)={auc:.3f}  Spearman={rho:.3f}")
    return {"signal": name, "pairs": int(mask.sum()), "auc_good_vs_no": round(float(auc), 3),
            "spearman": round(float(rho), 3)}


def main():
    parser = argparse.ArgumentParser(description="Evaluate the CV matcher on labelled resume/job pairs")
    parser.add_argument("--pairs", type=int, default=300)
    parser.add_argument("--llm", type=int, default=0, help="also score N pairs with the LLM (slow)")
    parser.add_argument("--split", default="test")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    print(f"Downloading {args.pairs} pairs from {DATASET} ({args.split})...")
    pairs = download(args.split, args.pairs, args.seed)
    labels = np.array([LABELS[p["label"]] for p in pairs])
    print("labels:", {k: int((labels == v).sum()) for k, v in LABELS.items()})

    sims = embedding_similarity(pairs)
    results = [report("embedding similarity", sims, labels)]

    good, bad = sims[labels == 2], sims[labels == 0]
    print(f"similarity %: No Fit median {np.median(bad):.1f}, Good Fit median {np.median(good):.1f} "
          f"(10th-90th pct of all: {np.percentile(sims, 10):.1f} - {np.percentile(sims, 90):.1f})")
    print("-> matcher.py EMB_LOW / EMB_HIGH should roughly span that range.")

    if args.llm:
        sub = list(range(min(args.llm, len(pairs))))
        print(f"LLM judgment on {len(sub)} pairs...")
        llm = np.full(len(pairs), np.nan)
        for i in sub:
            score = llm_judgment(pairs[i])
            llm[i] = np.nan if score is None else score
        results.append(report("LLM judgment", llm, labels))
        both = ~np.isnan(llm)
        blend = np.where(both, 0.8 * llm + 0.2 * np.clip((sims - 15) / 45 * 100, 0, 100), np.nan)
        results.append(report("LLM 80% + embedding 20%", blend, labels))

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
