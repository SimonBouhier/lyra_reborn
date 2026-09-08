"""CLI explicite du diagnostic exploratoire P6 ; aucune commande implicite live."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from experiments.p6_recall.study import prepare, qualify, run, analyse

parser = argparse.ArgumentParser(description=__doc__)
commands = parser.add_subparsers(dest='command', required=True)
p = commands.add_parser('prepare'); p.add_argument('--protocol', type=Path, required=True); p.add_argument('--destination', type=Path, required=True)
p = commands.add_parser('qualify'); p.add_argument('--study', type=Path, required=True)
p = commands.add_parser('run'); p.add_argument('--study', type=Path, required=True); p.add_argument('--max-calls', type=int)
p = commands.add_parser('analyse'); p.add_argument('--study', type=Path, required=True); p.add_argument('--destination', type=Path, required=True)
args = parser.parse_args()
if args.command == 'prepare': result = prepare(args.protocol, args.destination)
elif args.command == 'qualify': result = qualify(args.study)
elif args.command == 'run':
    if args.max_calls is not None and args.max_calls <= 0: parser.error('--max-calls doit être positif')
    result = run(args.study, args.max_calls)
else: result = analyse(args.study, args.destination)
print(json.dumps({k:v for k,v in result.items() if k not in ('scores', 'sources', 'files', 'engines')}, ensure_ascii=False, indent=2))
if args.command == 'qualify' and not result['passed']:
    sys.exit(2)
