"""Offline seal/evaluate workflow. Future labels are opened only by evaluate."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.independent_validation import seal,evaluate

def read(path):
    if path.stat().st_size>2_000_000:raise ValueError('Local evidence limit 2 MB')
    return json.loads(path.read_text('utf-8'))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['seal','evaluate']);p.add_argument('--protocol',type=Path);p.add_argument('--forecast',type=Path);p.add_argument('--seal',type=Path);p.add_argument('--annotations',type=Path);p.add_argument('--out',type=Path,required=True);args=p.parse_args()
    result=seal(read(args.protocol),read(args.forecast)) if args.mode=='seal' else evaluate(read(args.seal),read(args.annotations))
    with args.out.open('x',encoding='utf-8') as out:json.dump(result,out,indent=2,allow_nan=False)
    print('Saved local integrity artifact; independence remains unverified:',args.out)
if __name__=='__main__':main()
