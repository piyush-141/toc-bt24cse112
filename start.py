"""
Workflow Sentinel - Unified Backend Start Script.

Consolidates all server initialization, dataset generation, model calibration,
and service startup into a single command:
    python start.py
"""

import sys
import os

# Safely handle Windows console encodings
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def main():
    print("=" * 65)
    print("   Workflow Sentinel: Process Anomaly Detection System")
    print("   Automata (DFA) & Machine Learning Dual-Engine")
    print("=" * 65)

    # 1. Verify Core Packages
    try:
        import fastapi
        import sklearn
        import pandas
        import numpy
        import uvicorn
        print("[OK] Core dependencies verified (FastAPI, scikit-learn, pandas, numpy).")
    except ImportError as e:
        print(f"[!] Missing dependency: {e.name}")
        print("    Run: pip install -r requirements.txt")
        sys.exit(1)

    # 2. Verify Sample Dataset
    sample_csv = os.path.join("data", "sample_event_log.csv")
    if not os.path.exists(sample_csv):
        print("[*] Generating baseline sample dataset (1,000 cases)...")
        from data.generator import SyntheticLogGenerator
        os.makedirs("data", exist_ok=True)
        gen = SyntheticLogGenerator(seed=42)
        df = gen.generate_dataset(num_cases=1000)
        df.to_csv(sample_csv, index=False)
        print(f"[OK] Created {sample_csv} ({len(df)} events).")
    else:
        print(f"[OK] Baseline dataset ready: {sample_csv}")

    # 3. Launch Server
    port = int(os.environ.get("PORT", 8000))
    print(f"\n[SERVER] Starting Workflow Sentinel Server on http://localhost:{port}")
    print(f"         Unified Web Dashboard & API: http://localhost:{port}")
    print("         (Optional) Hot-reload dev server: cd frontend && npm run dev\n")

    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)

if __name__ == "__main__":
    main()
