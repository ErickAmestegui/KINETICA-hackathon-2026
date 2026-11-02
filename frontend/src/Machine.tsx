import { Suspense, Component, useEffect, useMemo, type ReactNode } from 'react';
import { Shape, Path } from 'three';
import { Canvas, useThree, type ThreeEvent } from '@react-three/fiber';
import { OrbitControls, Environment, Lightformer, ContactShadows, RoundedBox, Html, Line } from '@react-three/drei';
import { solve, type Parameters } from './engine';
import {modelPose} from './modelPose';

const steel='#b9c7cb', petrol='#115462', brass='#ba8b45';
type V3=[number,number,number];
function Metal({color=steel,rough=.24}:{color?:string;rough?:number}) {return <meshStandardMaterial color={color} metalness={.85} roughness={rough}/>;}
function Block({at,size,color=petrol,children}:{at:V3;size:V3;color?:string;children?:ReactNode}) {return <group position={at}><RoundedBox args={size} radius={.055} smoothness={3} castShadow receiveShadow><Metal color={color} rough={.32}/></RoundedBox>{children}</group>;}
function Axle({at,r=.14,length=.35,color=steel}:{at:V3;r?:number;length?:number;color?:string}) {return <mesh position={at} rotation={[Math.PI/2,0,0]} castShadow><cylinderGeometry args={[r,r,length,40]}/><Metal color={color}/></mesh>;}
function Ring({at,r,tube=.06,color=steel}:{at:V3;r:number;tube?:number;color?:string}) {return <mesh position={at} castShadow><torusGeometry args={[r,tube,16,80]}/><Metal color={color}/></mesh>;}
function FlywheelRim({r}:{r:number}){const shape=useMemo(()=>{const s=new Shape();s.absarc(0,0,r+.08,0,Math.PI*2,false);const hole=new Path();hole.absarc(0,0,r-.14,0,Math.PI*2,true);s.holes.push(hole);return s;},[r]);return <mesh position={[0,0,-.15]} castShadow><extrudeGeometry args={[shape,{depth:.3,bevelEnabled:true,bevelSegments:3,steps:1,bevelSize:.025,bevelThickness:.025,curveSegments:64}]}/><Metal color={steel} rough={.2}/></mesh>;}
function Bolt({at}:{at:V3}) {return <group position={at}><mesh rotation={[Math.PI/2,0,0]} castShadow><cylinderGeometry args={[.067,.067,.07,6]}/><Metal color={brass}/></mesh><Ring at={[0,0,-.04]} r={.075} tube={.012}/></group>;}
function Bearing({x,z,base}:{x:number;z:number;base:number}) {return <group><Block at={[x,base/2,z]} size={[.65,-base,.38]}/><Axle at={[x,0,z]} r={.33} length={.42} color={petrol}/><Ring at={[x,0,z+.23]} r={.21} tube={.07} color={brass}/><Block at={[x,base+.1,z]} size={[.95,.15,.7]}/>{[-.31,.31].map(b=><mesh key={b} position={[x+b,base+.22,z]}><cylinderGeometry args={[.06,.06,.12,6]}/><Metal color={brass}/></mesh>)}</group>;}
function Link({from,to,width=.22,depth=.16,color=steel}:{from:V3;to:V3;width?:number;depth?:number;color?:string}) {const dx=to[0]-from[0],dy=to[1]-from[1],len=Math.hypot(dx,dy);return <group position={[(from[0]+to[0])/2,(from[1]+to[1])/2,from[2]]} rotation={[0,0,Math.atan2(dy,dx)]}><Block at={[0,0,0]} size={[len,width,depth]} color={color}/><Block at={[0,0,depth/2+.008]} size={[len*.78,width*.35,.015]} color={petrol}/></group>;}
export const parts=[{id:'crank',n:'01',name:'Crank & flywheel',description:'Revolute joint · O → A. Converts angular motion into an orbit.',material:'Petrol enamel / brushed steel'}, {id:'rod',n:'02',name:'Connecting rod',description:'Rigid link · A → B. Both endpoints follow the constraint solver.',material:'Machined steel / brass bushings'}, {id:'slider',n:'03',name:'Slider / crosshead',description:'Prismatic joint · B. Translation along the calibrated guide axis.',material:'Satin steel / bronze bearings'}, {id:'frame',n:'04',name:'Ground & guides',description:'Fixed frame · O. Holds the shaft and constrains the slide axis.',material:'Cast metal / polished guide rails'}];
function Assembly({p,t,selected,onSelect,xray,labels}:{p:Parameters;t:number;selected:string;onSelect:(s:string)=>void;xray:boolean;labels:boolean}) {
 const {state:s,r,L,e,A,B,baseTop:base}=modelPose(p,t);
 const guideLeft=Math.sqrt((L-r)**2-e**2)-.7;
 const right=Math.sqrt((L+r)**2-e**2)+1.15, left=-r-1.15, wheel=r+.32;
 const pick=(id:string)=>(ev:ThreeEvent<MouseEvent>)=>{ev.stopPropagation();onSelect(id);};
 return <group position={[-(right+left)/2,0,0]}>
  <group onClick={pick('frame')}>
   <Block at={[(left+right)/2,base-.13,0]} size={[right-left,.25,2.4]}/>
   <Block at={[(left+right)/2,base-.29,0]} size={[right-left-.18,.08,2.22]} color={steel}/>
   {[left+.3,right-.3].map(x=>[-.85,.85].map(z=><group key={`${x},${z}`}><Block at={[x,base-.44,z]} size={[.65,.28,.55]} color="#2a3435"/><mesh position={[x,base+.05,z]}><cylinderGeometry args={[.09,.09,.1,6]}/><Metal color={brass}/></mesh></group>))}
   <Bearing x={0} z={-.58} base={base}/><Bearing x={0} z={.3} base={base}/>
   {[guideLeft,right-.35].map(x=><group key={x}><Block at={[x,base+.12,0]} size={[.5,.2,1.85]}/>{[-.66,.66].map(z=><group key={z}><Block at={[x,(e+base+.2)/2,z]} size={[.32,Math.max(.25,e-base-.2),.27]}/><mesh position={[x,e-.05,z]} rotation={[0,0,Math.PI/2]} castShadow><cylinderGeometry args={[.15,.15,.38,32]}/><Metal color={brass}/></mesh><mesh position={[x,e+.17,z]}><cylinderGeometry args={[.055,.055,.1,6]}/><Metal color={brass}/></mesh></group>)}</group>)}
   {[-.66,.66].map(z=><mesh key={z} position={[(guideLeft+right-.35)/2,e-.05,z]} rotation={[0,0,Math.PI/2]} castShadow><cylinderGeometry args={[.065,.065,right-guideLeft-.15,32]}/><Metal/></mesh>)}
   {[-.96,.96].map(z=><Block key={z} at={[(left+right)/2,base+.04,z]} size={[right-left-.8,.08,.12]} color={steel}/>)}
  </group>
  <group onClick={pick('crank')}>
   <Axle at={[0,0,-.22]} r={.15} length={1.9}/>
   <group rotation={[0,0,s.theta]} position={[0,0,-.88]}>
    <FlywheelRim r={wheel}/><Ring at={[0,0,.17]} r={wheel-.05} tube={.025}/><Ring at={[0,0,0]} r={wheel-.2} tube={.09} color={petrol}/>
    {Array.from({length:6},(_,i)=><group key={i} rotation={[0,0,i*Math.PI/3]}><Block at={[(wheel-.1)/2,0,0]} size={[wheel-.24,.18,.15]}/></group>)}
    <Axle at={[0,0,0]} r={.29} length={.44} color={brass}/><Ring at={[0,0,.24]} r={.18} tube={.04}/>
   </group>
   <group rotation={[0,0,s.theta]}><Block at={[r/2,0,.65]} size={[r+.28,.4,.24]}/><Axle at={[0,0,.59]} r={.29} length={.5} color={brass}/><Axle at={[r,0,.88]} r={.17} length={.5}/><Bolt at={[0,0,.87]}/></group>
  </group>
  <group onClick={pick('rod')}>
   <Link from={A} to={B} width={.22}/>
   {[A,B].map((pt,i)=><group key={i}><Axle at={pt} r={i===0?.25:.21} length={.23}/><Ring at={[pt[0],pt[1],pt[2]+.14]} r={i===0?.16:.13} tube={.047} color={brass}/><Bolt at={[pt[0],pt[1],pt[2]+.2]}/></group>)}
  </group>
  <group onClick={pick('slider')} position={[B[0],e,0]}>
   <Block at={[0,0,0]} size={[.7,.6,1.25]} color={steel}/><Block at={[0,.32,0]} size={[.83,.08,1.34]}/><Axle at={[0,0,.75]} r={.17} length={.8} color={brass}/>
   {[-.66,.66].map(z=><mesh key={z} position={[0,-.05,z]} rotation={[0,0,Math.PI/2]}><cylinderGeometry args={[.12,.12,.78,32]}/><Metal color={brass}/></mesh>)}
   {[-.25,.25].map(x=>[-.47,.47].map(z=><mesh key={`${x},${z}`} position={[x,.39,z]}><cylinderGeometry args={[.045,.045,.06,6]}/><Metal color={brass}/></mesh>))}
  </group>
  {xray&&<group><Line points={[[0,0,.98],[A[0],A[1],.98],[B[0],B[1],.98]]} color="#09b4ba" lineWidth={3}/>{[[0,0,1], [A[0],A[1],1],[B[0],B[1],1]].map((v,i)=><mesh key={i} position={v as V3}><sphereGeometry args={[.09,16,16]}/><meshBasicMaterial color="#f2ae50"/></mesh>)}</group>}
  {labels&&<>
   <Html position={[-.4,wheel+.6,-.8]} center><button className={`part-label ${selected==='crank'?'chosen':''}`} onClick={()=>onSelect('crank')}><b>01</b> Crankshaft<span>ROTARY INPUT</span></button></Html>
   <Html position={[(A[0]+B[0])/2,Math.max(A[1],B[1])+.95,.7]} center><button className={`part-label ${selected==='rod'?'chosen':''}`} onClick={()=>onSelect('rod')}><b>02</b> Connecting rod<span>RIGID CONSTRAINT</span></button></Html>
   <Html position={[L+r+.55,e+.85,.15]} center><button className={`part-label ${selected==='slider'?'chosen':''}`} onClick={()=>onSelect('slider')}><b>03</b> Crosshead<span>LINEAR OUTPUT</span></button></Html>
  </>}
 </group>;
}
class Boundary extends Component<{children:ReactNode},{failed:boolean}> {state={failed:false};static getDerivedStateFromError(){return {failed:true};}render(){return this.state.failed?<div className="empty"><h3>WebGL is unavailable</h3><p>Enable hardware acceleration to view the machine. The mathematical engine and analysis remain available.</p></div>:this.props.children;}}
function CameraReset({version}:{version:number}){const {camera,size}=useThree();useEffect(()=>{const factor=Math.max(1,1.35/(size.width/size.height));camera.position.set(7*factor,5.3*factor,9*factor);camera.lookAt(0,-.5,0);camera.updateProjectionMatrix();},[version,camera,size.width,size.height]);return null;}
export default function Machine(props:{p:Parameters;t:number;selected:string;onSelect:(s:string)=>void;xray:boolean;labels:boolean;cameraKey:number}) {
 return <Boundary><Canvas shadows dpr={[1,1.7]} camera={{position:[7,5.3,9],fov:36,near:.1,far:150}} gl={{antialias:true,preserveDrawingBuffer:true}}>
  <color attach="background" args={['#f4f3ee']}/><ambientLight intensity={.65}/><directionalLight position={[-3,7,5]} intensity={3.5} castShadow shadow-mapSize={[2048,2048]} shadow-camera-left={-10} shadow-camera-right={10} shadow-camera-top={10} shadow-camera-bottom={-10} shadow-bias={-.0005}/>
  <Suspense fallback={null}><Environment resolution={128}><Lightformer intensity={4} position={[0,5,-3]} rotation={[Math.PI/2,0,0]} scale={[12,8,1]}/><Lightformer intensity={3} position={[5,2,2]} rotation={[0,-Math.PI/2,0]} scale={[5,7,1]}/><Lightformer intensity={2} position={[-5,1,3]} rotation={[0,Math.PI/2,0]} scale={[4,6,1]}/></Environment></Suspense>
  <Assembly {...props}/>
  <ContactShadows position={[0,modelPose(props.p,props.t).floor,0]} opacity={.4} scale={22} blur={2.7} far={8} resolution={256}/>
  <gridHelper args={[24,48,'#dce1d9','#e9ebe4']} position={[0,modelPose(props.p,props.t).floor-.02,0]}/>
  <CameraReset version={props.cameraKey}/><OrbitControls key={props.cameraKey} makeDefault target={[0,-.5,0]} minDistance={5} maxDistance={30} maxPolarAngle={Math.PI*.48} enableDamping/>
 </Canvas></Boundary>;
}
