"""Export cleaned climbing data to static JSON files in static_cleaner/."""
import json
import os

from api import SCORING_METHODS, build_clean_dataframe, calculate_score

OUTPUT_DIR = "static_cleaner"


def export_static():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    df, present_grades = build_clean_dataframe()

    grade_cols = [f"{g}_{suffix}" for g in present_grades for suffix in ("completed", "tried")]
    output_cols = ["Location", "Dates", "daily_score"] + grade_cols
    if "Comments" in df.columns:
        output_cols.append("Comments")

    all_methods = {}

    for method_key, weights in SCORING_METHODS.items():
        df["daily_score"] = df.apply(
            lambda r: calculate_score(r, weights, present_grades), axis=1
        )

        result_df = df[output_cols].copy()
        result_df = result_df.assign(Dates=result_df["Dates"].dt.strftime("%Y-%m-%d"))
        result_df = result_df.fillna(0)

        sessions = result_df.to_dict(orient="records")

        payload = {
            "scoring_method": method_key,
            "weights": weights,
            "total_sessions": len(sessions),
            "sessions": sessions,
        }

        out_path = os.path.join(OUTPUT_DIR, f"{method_key}.json")
        with open(out_path, "w") as f:
            json.dump(payload, f, indent=2)
        print(f"Wrote {out_path}")

        all_methods[method_key] = {"scoring_method": method_key, "weights": weights, "total_sessions": len(sessions)}

    combined_path = os.path.join(OUTPUT_DIR, "all.json")
    with open(combined_path, "w") as f:
        json.dump(all_methods, f, indent=2)
    print(f"Wrote {combined_path}")


if __name__ == "__main__":
    export_static()
