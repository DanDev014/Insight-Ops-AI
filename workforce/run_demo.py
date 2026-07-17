"""
run_demo.py
-----------
Run the full engine once and print + save the output as JSON — WITHOUT starting
the web server. Two uses:
  1. Sanity-check the engine end to end.
  2. Hand `workforce_output.json` to the frontend/LLM teammates so they can build
     against a real payload before the API is even deployed.

Usage:
    python run_demo.py            # uses DB if configured, else sample data
"""

import json

import database
from workforce_engine import build_workforce_intelligence


def main():
    tables = database.load_tables()
    result = build_workforce_intelligence(
        tables["team"], tables["projects"], tables["time_logs"]
    )

    print(f"Week ending: {result['generated_for_week_ending']}")
    print("\nSUMMARY:")
    print(json.dumps(result["summary"], indent=2))
    print(f"\n{len(result['employees'])} employees | "
          f"{len(result['recommendations'])} recommendations\n")
    print("TOP RECOMMENDATIONS:")
    for r in result["recommendations"][:5]:
        print(f"  • {r['alert_text']}")

    with open("workforce_output.json", "w") as f:
        json.dump(result, f, indent=2)
    print("\nSaved full payload -> workforce_output.json")


if __name__ == "__main__":
    main()
