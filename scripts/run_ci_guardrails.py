"""
CI regression guardrail suite for RAG quality.

Runs a short eval (Layer 1 + Layer 2), then enforces:
  - Context Recall >= 0.88
  - Faithfulness >= 0.85
  - Hallucinations < 15 (total count over evaluated questions)

Usage:
  python scripts/run_ci_guardrails.py --tenant-slug claw-demo --questions claw_manuals/eval_questions_300.json
  python scripts/run_ci_guardrails.py --tenant claw-demo --questions claw_manuals/eval_questions_300.json --sample 80

Exit code: 0 if all guardrails pass, 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Guardrail thresholds (production targets)
MIN_RECALL = 0.88
MIN_FAITHFULNESS = 0.85
MAX_HALLUCINATIONS = 14  # < 15 means total <= 14


def main() -> int:
    parser = argparse.ArgumentParser(description="CI regression guardrails for RAG")
    parser.add_argument("--tenant-slug", "--tenant", dest="tenant", required=True)
    parser.add_argument("--questions", type=Path, required=True)
    parser.add_argument("--sample", type=int, default=80, help="Number of questions to evaluate (default 80)")
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "results" / "ci_guardrails_results.json")
    parser.add_argument("--no-run", action="store_true", help="Only check existing output file")
    args = parser.parse_args()

    output_path = args.output if args.output.is_absolute() else PROJECT_ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not args.no_run:
        questions_path = args.questions if args.questions.is_absolute() else PROJECT_ROOT / args.questions
        cmd = [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "eval_comprehensive.py"),
            "--tenant-slug", args.tenant,
            "--questions", str(questions_path),
            "--layer", "all",
            "--sample", str(args.sample),
            "--output", str(output_path.with_suffix("")),
        ]
        print(f"Running eval: {' '.join(cmd)}")
        rc = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
        if rc.returncode != 0:
            print("Eval script failed.")
            return 1

    json_path = output_path if output_path.suffix == ".json" else output_path.with_suffix(".json")
    if not json_path.exists():
        print(f"Results file not found: {json_path}")
        return 1
    output_path = json_path

    with open(output_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    results = data.get("results", [])
    if not results:
        print("No results in output file.")
        return 1

    # Compute metrics from results
    n = len(results)
    recall_sum = 0.0
    faithfulness_sum = 0.0
    hallucination_total = 0

    for r in results:
        rm = r.get("retrieval_metrics") or {}
        am = r.get("answer_metrics") or {}
        recall_sum += rm.get("context_recall", 0.0)
        faithfulness_sum += am.get("faithfulness_score", 0.0)
        hallucination_total += am.get("hallucination_count", 0)

    avg_recall = recall_sum / n
    avg_faithfulness = faithfulness_sum / n

    # Guardrail checks
    recall_ok = avg_recall >= MIN_RECALL
    faith_ok = avg_faithfulness >= MIN_FAITHFULNESS
    halluc_ok = hallucination_total < 15  # < 15

    print()
    print("=" * 60)
    print("CI REGRESSION GUARDRAILS")
    print("=" * 60)
    print(f"  Context Recall:    {avg_recall:.3f}  (min {MIN_RECALL})  {'PASS' if recall_ok else 'FAIL'}")
    print(f"  Faithfulness:      {avg_faithfulness:.3f}  (min {MIN_FAITHFULNESS})  {'PASS' if faith_ok else 'FAIL'}")
    print(f"  Hallucinations:    {hallucination_total}  (max 14)  {'PASS' if halluc_ok else 'FAIL'}")
    print("=" * 60)

    if recall_ok and faith_ok and halluc_ok:
        print("All guardrails passed.")
        return 0

    print("One or more guardrails failed.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
