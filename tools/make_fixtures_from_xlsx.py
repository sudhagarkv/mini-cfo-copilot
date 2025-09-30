import argparse
from pathlib import Path
import pandas as pd

def main(xlsx_path: Path, fixtures_dir: Path):
    fixtures_dir.mkdir(parents=True, exist_ok=True)
    xl = pd.ExcelFile(xlsx_path)
    needed = ["actuals", "budget", "cash", "fx"]
    for name in needed:
        if name not in xl.sheet_names:
            raise ValueError(f"Sheet '{name}' missing in {xlsx_path}")
        df = xl.parse(name)
        (fixtures_dir / f"{name}.csv").write_text(df.to_csv(index=False))
    print(f"Exported to {fixtures_dir}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--xlsx", required=True, help="Path to provided data.xlsx")
    p.add_argument("--outdir", default="fixtures", help="Output fixtures folder")
    args = p.parse_args()
    main(Path(args.xlsx), Path(args.outdir))
