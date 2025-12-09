#!/usr/bin/env python3
import json
import os
import datetime
from collections import defaultdict

LOG_FILE = "logs/metrics.jsonl"

def load_metrics():
    if not os.path.exists(LOG_FILE):
        print(f"No logs found at {LOG_FILE}")
        return []
    
    data = []
    with open(LOG_FILE, "r") as f:
        for line in f:
            if line.strip():
                try:
                    data.append(json.loads(line))
                except:
                    pass
    return data

def generate_report():
    metrics = load_metrics()
    if not metrics:
        return

    total_reqs = len(metrics)
    total_cost = sum(m.get("cost_est_usd", 0) for m in metrics)
    total_tokens = sum(m.get("tokens_total", 0) for m in metrics)
    
    # By Tier
    by_tier = defaultdict(int)
    cost_by_tier = defaultdict(float)
    
    for m in metrics:
        t = m.get("tier", "unknown")
        by_tier[t] += 1
        cost_by_tier[t] += m.get("cost_est_usd", 0)
        
    print(f"\n=== AI ROUTER COST REPORT ===")
    print(f"Generated: {datetime.datetime.now().isoformat()}")
    print("-" * 30)
    print(f"Total Requests : {total_reqs}")
    print(f"Total Tokens   : {total_tokens:,}")
    print(f"Total Cost     : ${total_cost:.6f}")
    print("-" * 30)
    print("Usage by Tier:")
    
    for tier, count in sorted(by_tier.items()):
        cost = cost_by_tier[tier]
        pct = (count / total_reqs) * 100
        print(f"  - {tier.upper():<10} : {count:>4} reqs ({pct:>5.1f}%) | ${cost:.6f}")
        
    print("-" * 30)
    
    # Validation
    local_tiers = ["local"] # Need to ensure generic local is mapped to 'local'? 
    # Actually in code: _get_tier_from_model returns 'standard' or whatever keys we logic out.
    # Wait, _get_tier_from_model defaults to 'standard' if not matched.
    # Llama/DeepSeek logic in cost_guard?
    # Let's check cost_guard logic again.
    
    pass

if __name__ == "__main__":
    generate_report()
