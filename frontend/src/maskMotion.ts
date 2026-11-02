import type {Parameters} from './engine';
export type MaskSample={frame:number;t:number;x:number;y:number;area_px2:number;source:string;object_id:string};
export type MaskCorrection={frame:number;x?:number;y?:number;excluded?:boolean};
export type MaskAssignment={frame:number;object_id:string};
export type MotionState={objectId:string;confirmedSlider:boolean;corrections:MaskCorrection[];assignments:MaskAssignment[];axisAngle:number|null;jitterPx:number;startFrame:number;endFrame:number|null;estimateTiming:boolean};
export const emptyMotionState=():MotionState=>({objectId:'',confirmedSlider:false,corrections:[],assignments:[],axisAngle:null,jitterPx:2,startFrame:0,endFrame:null,estimateTiming:false});
export type MaskObject={object_id:string;boxes:number;masks:number;valid_masks:number;samples:MaskSample[];missing_mask_frames:number[];motion:string;span_px:number|null;possible_id_jumps:number[];temporal_alerts?:{frame:number;deviation_px:number}[];temporal_threshold_px?:number|null;axis?:{direction:number[];origin:number[];linearity:number}|null};
export type MaskAudit={counts:{records:number;objects:number;boxes:number;masks:number;frames_with_geometry:number;source_frames:number};objects:MaskObject[];issues:{object_id?:string;frame?:number;reason:string}[];missing_geometry_frames:number[];evidence:{kind:string;diagnostic_id?:string;records_sha256:string;video_sha256?:string;video_id?:string};limitations:string[];centroid_method:string};
type Metric={n:number;rmse_px:number;baseline_rmse_px:number;cross_axis_rms_px:number};
export type MaskFit={object_id:string;rows:(MaskSample&{split:string;displacement_px:number;predicted_px:number;residual_px:number;cross_axis_px:number})[];axis:{direction:number[];origin:number[];linearity:number;estimated_from:string};projection:{gain_px_per_model_unit:number;offset_px:number;basis_at_zero:number};parameters_held_fixed:Partial<Parameters>;parameters_used:Parameters;timing_estimated:boolean;interval:{start_frame:number;end_frame:number;selection:string};split_frame:number;fit:Metric;validation:Metric;fit_frames:number[];validation_frames:number[];limitations:string[]};
export type MaskAnalysis={audit:MaskAudit;track:MaskSample[];motion:MaskFit|null};

export function correctedTrack(object:MaskObject|undefined,objects:MaskObject[],state:MotionState):MaskSample[]{
 const samples=new Map((object?.samples??[]).map(s=>[s.frame,{...s}]));
 for(const a of state.assignments){const s=objects.find(o=>o.object_id===a.object_id)?.samples.find(s=>s.frame===a.frame);if(s)samples.set(a.frame,{...s,source:'manual-ID-assignment'});}
 for(const c of state.corrections){const s=samples.get(c.frame);if(c.excluded)samples.delete(c.frame);else if(s&&c.x!==undefined&&c.y!==undefined)samples.set(c.frame,{...s,x:c.x,y:c.y,source:'manual-centroid'});}
 return [...samples.values()].sort((a,b)=>a.frame-b.frame);
}
