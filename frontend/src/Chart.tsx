import {solve,type Parameters,type Observation,type Calibration,project} from './engine';
export default function Chart({p,t,observations=[],calibration,large=false}:{p:Parameters;t:number;observations?:Observation[];calibration?:Calibration;large?:boolean}) {
 const duration=Math.abs(p.rpm)>0?60/Math.abs(p.rpm):2;
 const n=150, series=Array.from({length:n+1},(_,i)=>({t:i/n*duration,x:solve(p,i/n*duration).B[0]}));
 const min=p.L-p.r-Math.abs(p.e)-4,max=p.L+p.r+4;
 const px=(x:number)=>36+x/duration*300,py=(y:number)=>136-(y-min)/(max-min)*110;
 const path=series.map((d,i)=>`${i?'L':'M'}${px(d.t)},${py(d.x)}`).join(' ');
 return <div className={`chart ${large?'large':''}`}><div className="chart-title"><b>Slider displacement</b><span><i/>Calculated</span></div><svg viewBox="0 0 360 168" role="img" aria-label="Calculated slider displacement over one revolution">
  {[0,.25,.5,.75,1].map(f=><g key={f}><line x1={36+300*f} x2={36+300*f} y1="20" y2="136" stroke="#dfe5e3"/><text x={36+300*f} y="155" textAnchor="middle">{(f*duration).toFixed(2)}</text></g>)}
  {[min,(max+min)/2,max].map(y=><g key={y}><line x1="36" x2="336" y1={py(y)} y2={py(y)} stroke="#dfe5e3"/><text x="30" y={py(y)+3} textAnchor="end">{y.toFixed(0)}</text></g>)}
  <path d={`${path} L336,136 L36,136 Z`} fill="url(#area)"/><path d={path} fill="none" stroke="#147a86" strokeWidth="2.3"/>
  {observations.filter(o=>o.joint==='slider').map((o,i)=>{if(!calibration)return null;const origin=project([0,p.e],calibration);const x=((o.x-origin[0])*Math.cos(calibration.angle)+(o.y-origin[1])*Math.sin(calibration.angle))/calibration.scale;return <circle key={i} cx={px(o.t%duration)} cy={py(x)} r="2.8" fill={o.split==='fit'?'#c38b42':'#785caa'}/>;})}
  <line x1={px(t%duration)} x2={px(t%duration)} y1="16" y2="136" stroke="#c28c48" strokeDasharray="3 3"/><circle cx={px(t%duration)} cy={py(solve(p,t).B[0])} r="4" fill="#147a86" stroke="white" strokeWidth="2"/>
  <defs><linearGradient id="area" x1="0" y1="0" x2="0" y2="1"><stop stopColor="#399eaa" stopOpacity=".15"/><stop offset="1" stopColor="#399eaa" stopOpacity="0"/></linearGradient></defs>
 </svg><div className="chart-axis"><span>Model units</span><span>Time (s) · one revolution</span></div></div>;
}
