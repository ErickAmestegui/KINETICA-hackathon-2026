"""Local backend controller. quote is offline; run needs a fresh approved estimate."""
import argparse
import json
import urllib.request
from pathlib import Path

def post(route,body):
    request=urllib.request.Request('http://127.0.0.1:8000/api/lab/muse/'+route,data=json.dumps(body).encode(),headers={'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(request,timeout=60) as response:return json.load(response)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mode',choices=['quote','run']);parser.add_argument('--quote',type=Path);parser.add_argument('--approve-one',action='store_true');args=parser.parse_args()
    if args.mode=='quote':
        result=post('quote',{'text':'Duplica la velocidad angular del mecanismo','parameters':{'r':32,'L':128,'rpm':40,'e':0,'phase':0}})
        folder=Path(__file__).resolve().parents[1]/'output'/'muse-trial';folder.mkdir(exist_ok=True)
        destination=folder/(result['token']+'.json')
        with destination.open('x',encoding='utf-8') as out:json.dump(result,out,indent=2)
        print('Estimate saved privately:',destination)
        print('Input allowance:',result['input_token_allowance'],'Output cap:',result['output_token_limit'],'Estimated USD:',result['estimated_usd'],'paid_enabled:',result['status']['paid_enabled'])
    else:
        if not args.approve_one or not args.quote:parser.error('run requires --quote and --approve-one after explicit human authorization')
        quote=json.loads(args.quote.read_text('utf-8'))
        if not quote['status']['paid_enabled']:raise ValueError('This estimate was prepared disabled; a NEW authorized enabled quote is required')
        result=post('run',{'token':quote['token'],'approved':True})
        print('One request completed. Diagnostic:',result['diagnostic_id'],'Usage:',result['usage'],'Applied:',result['applied'])
        print('Review the saved tool proposal before changing the alternate model. No second model request is made.')
if __name__=='__main__':main()
