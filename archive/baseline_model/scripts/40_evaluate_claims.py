# -*- coding: utf-8 -*-
"""
CLI:
  python scripts/40_evaluate_claims.py \
      data/parsed/example.parsed.json \
      data/claims/example.claims.json \
      [out_dir] [model_name] [top_k]

Defaults:
  out_dir   = data/verdicts
  model     = sentence-transformers/all-mpnet-base-v2
  top_k     = 8
"""
import os, sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.truthfulness.evaluate import load_json, save_json, evaluate_claims

def main():
    if len(sys.argv) < 3:
        print("Usage: python scripts/40_evaluate_claims.py <parsed.json> <claims.json> [out_dir] [model_name] [top_k]")
        sys.exit(1)

    parsed_path = sys.argv[1]
    claims_path = sys.argv[2]
    out_dir     = sys.argv[3] if len(sys.argv) > 3 else "data/verdicts"
    model_name  = sys.argv[4] if len(sys.argv) > 4 else "sentence-transformers/all-mpnet-base-v2"
    top_k       = int(sys.argv[5]) if len(sys.argv) > 5 else 8

    for p in (parsed_path, claims_path):
        if not os.path.exists(p):
            print(f"[ERR] file not found: {os.path.abspath(p)}")
            sys.exit(1)

    parsed = load_json(parsed_path)
    claims = load_json(claims_path)

    out_obj = evaluate_claims(parsed, claims, model_name=model_name, top_k=top_k)
    out_path = os.path.join(out_dir, f"{out_obj['paper_id']}.verdicts.json")
    save_json(out_obj, out_path)

    print(f"[OK] wrote: {out_path}")
    print(f"  claims evaluated: {len(out_obj['verdicts'])}")
    # quick stats
    ps = [v['truthfulness']['p_support'] for v in out_obj['verdicts']]
    if ps:
        print(f"  p_support mean: {sum(ps)/len(ps):.3f}")

if __name__ == "__main__":
    main()
