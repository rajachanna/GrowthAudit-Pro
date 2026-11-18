"""Run public website scans from a terminal."""
from argparse import ArgumentParser
from pathlib import Path
from .engine import run_audit, report_json, report_markdown


def main(argv=None):
    p=ArgumentParser(description="Public website HTML technical audit (not a ranking predictor)")
    p.add_argument("url")
    p.add_argument("--format",choices=("json","markdown"),default="json")
    p.add_argument("--output",type=Path)
    a=p.parse_args(argv)
    from .fetch import FetchError
    from .security import UnsafeTarget
    try:
        report=run_audit(a.url)
    except (FetchError,UnsafeTarget,PermissionError) as exc:
        p.exit(2,str(exc)+"\n")
    out=report_json(report) if a.format=="json" else report_markdown(report)
    if a.output:a.output.write_text(out+"\n",encoding="utf-8")
    else:print(out)
    return 0


if __name__=="__main__":
    raise SystemExit(main())
