"""Prepare narration and finalize an authentic Playwright recording; no model I/O.

Three steps: --prepare (offline Windows speech), capture_demo_video.cjs, --render.
The video remains private until the entrant approves media terms and publication.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import wave

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/submission-video'

SCENES = [
 ('intro', 'From footage to a testable machine',
  'A moving machine is easy to watch, but harder to explain. KINETICA connects authentic visual observations to an inspectable mechanical hypothesis. This is the working Reality Lab, recorded locally. No new model inference was used to produce this demonstration.',
  'Una máquina en movimiento es fácil de observar y más difícil de explicar. KINETICA conecta observaciones visuales auténticas con una hipótesis mecánica inspeccionable. Esta es la aplicación real, grabada localmente, sin inferencias nuevas.'),
 ('observe', 'Observe · saved real Meta SAM 3.1 evidence',
  'Observe the real Eitech mechanism and preserved Meta SAM three point one component masks. The response contains one hundred fifty boxes and one hundred fifty contours: three object identities across fifty frames. I explicitly confirm the slider identity. Segmentation does not identify its joint center.',
  'Observa el mecanismo Eitech real y sus máscaras Meta SAM 3.1 conservadas. Son 150 cajas y 150 contornos: tres IDs en 50 fotogramas. Confirmo explícitamente la identidad de la corredera; la segmentación no identifica su articulación.'),
 ('predict', 'Predict · seal before reveal',
  'At frame twenty nine, freeze fits only earlier local observations and seals an eight frame forecast. The gold path is a calculated hypothesis. Geometry remains declared. Because the original SAM request processed the full clip, this retrospective replay does not establish causal online prediction.',
  'En el fotograma 29, Freeze ajusta solo observaciones locales anteriores y sella ocho fotogramas futuros. El trazado dorado es una hipótesis calculada. La geometría es declarada y SAM procesó el clip completo: este replay retrospectivo no demuestra predicción causal en línea.'),
 ('reveal', 'Reveal · compare the same observations',
  'Reveal compares all methods on the same eight saved observations. Model error is nine point one zero pixels, versus twenty three point nine three for the constant baseline and seventy five point five nine for linear extrapolation. These are image coordinate errors, not physical reconstruction accuracy.',
  'Reveal compara los tres métodos con las mismas ocho observaciones guardadas. RMSE: modelo 9,10 píxeles; referencia constante 23,93; extrapolación lineal 75,59. Son errores en coordenadas de imagen, no precisión de reconstrucción física.'),
 ('cut', 'Reveal · an invalid experiment stays invalid',
  'A longer horizon crosses the known source change at frames thirty seven to thirty eight. KINETICA withholds every score. We preserve failures instead of replacing missing evidence with a confident number. Independent continuous footage and untouched labels remain the next validation step.',
  'Un horizonte más largo cruza el cambio conocido de fuente entre los fotogramas 37 y 38. KINETICA invalida todas las métricas. Conservamos los fallos. La validación independiente con vídeo continuo y etiquetas sin inspeccionar sigue pendiente.'),
 ('break', 'Break Reality · solver driven alternatives',
  'Now change the mechanism. Original and alternate share one clock, and every rendered pose comes from the constraint solver. An impossible stroke is rejected. A feasible change produces a different calculated motion. This is a counterfactual simulation; forces, materials and mechanical buildability are not evaluated.',
  'Ahora modificamos el mecanismo. Original y alternativa comparten reloj; el solver calcula cada pose. Un recorrido imposible se rechaza y uno viable cambia el movimiento. Es simulación contrafactual: no se evalúan fuerzas, materiales ni fabricabilidad.'),
 ('ask', 'Ask the Machine · explicitly labeled local mock',
  'Ask the Machine is clearly labeled as a deterministic mock. It proposes a bounded tool request, KINETICA validates the geometry, and the user confirms before the alternate changes. The real Muse trial failed and remains unverified. This local demonstration does not pretend otherwise.',
  'Ask the Machine está claramente etiquetado como mock determinista. Propone una herramienta acotada, KINETICA valida la geometría y el usuario confirma antes de cambiar la alternativa. El ensayo Muse real falló y sigue sin verificarse; esta demostración no lo presenta como éxito.'),
 ('outro', 'An inspectable loop from observations to hypotheses',
  'Authentic saved Meta segmentation, explicit human interpretation, sealed hypotheses and solver driven alternatives, in one reproducible studio. Source footage: Rhetos, Schubkurbelgetriebe Eitech, Wikimedia Commons, Creative Commons Attribution Share Alike four point zero. The proposed audiovisual release follows that license. Application code remains MIT.',
  'Segmentación Meta auténtica guardada, interpretación humana explícita, hipótesis selladas y alternativas calculadas en un estudio reproducible. Metraje: Rhetos, Schubkurbelgetriebe Eitech, Wikimedia Commons, CC BY-SA 4.0. La publicación audiovisual propuesta respeta esa licencia. Código de la aplicación MIT.'),
]

ORIGINAL_SCENES = [
 ('intro', 'Original material only',
  'A moving machine is easy to watch, but harder to explain. KINETICA connects visual observations to an inspectable mechanical hypothesis. This version of the demonstration uses only material we created. The footage is an original synthetic clip rendered by KINETICA code. It is not a real recording, and no new model inference was used.',
  'Una máquina en movimiento es fácil de observar y más difícil de explicar. KINETICA conecta observaciones visuales con una hipótesis mecánica inspeccionable. Esta versión usa solo material propio: un clip sintético original generado con el código de KINETICA. No es una grabación real y no se usaron inferencias nuevas.'),
 ('observe', 'Observe · synthetic geometry, labeled as such',
  'Observe the clip and its saved geometry: two objects across one hundred twenty five frames. This geometry is not Meta SAM output. It is derived from the clip\'s known motion plus measurement noise, and the interface labels it as a simulated test. I explicitly confirm the slider identity.',
  'Observa el clip y su geometría guardada: dos objetos en 125 fotogramas. Esta geometría no es salida de Meta SAM: se deriva del movimiento conocido del clip más ruido de medición, y la interfaz la etiqueta como prueba simulada. Confirmo explícitamente la identidad de la corredera.'),
 ('predict', 'Predict · seal before reveal',
  'At frame seventy four, freeze fits only earlier observations and seals a twenty frame forecast. The model assumes a constant motor speed. The hidden truth contains a speed ripple that the model was never told about. The gold path is a calculated hypothesis, and geometry remains declared.',
  'En el fotograma 74, Freeze ajusta solo observaciones anteriores y sella 20 fotogramas futuros. El modelo supone velocidad constante del motor; la verdad oculta contiene una oscilación de velocidad que el modelo desconoce. El trazado dorado es una hipótesis calculada y la geometría es declarada.'),
 ('reveal', 'Reveal · compare the same observations',
  'Reveal compares all methods on the same twenty saved observations. Model error is seven point six seven pixels, versus fifty two point zero five for the constant baseline and one hundred twenty nine point eight two for linear extrapolation. On synthetic data this checks the pipeline. It is not evidence about real footage.',
  'Reveal compara los tres métodos con las mismas 20 observaciones guardadas. RMSE: modelo 7,67 píxeles; referencia constante 52,05; extrapolación lineal 129,82. Con datos sintéticos esto verifica el proceso; no es evidencia sobre vídeo real.'),
 ('guard', 'Reveal · insufficient evidence is refused',
  'With too little history, freezing at frame forty nine, KINETICA refuses to predict. Timing is not identifiable from less than one and a quarter observed cycles. Insufficient evidence produces an explanation, never a confident number.',
  'Con muy poco historial, congelando en el fotograma 49, KINETICA se niega a predecir: la sincronización no es identificable con menos de 1,25 ciclos observados. La evidencia insuficiente produce una explicación, nunca un número confiado.'),
 ('break', 'Break Reality · solver driven alternatives',
  'Now change the mechanism. Original and alternate share one clock, and every rendered pose comes from the constraint solver. An impossible stroke is rejected. A feasible change produces a different calculated motion. This is a counterfactual simulation; forces, materials and mechanical buildability are not evaluated.',
  'Ahora modificamos el mecanismo. Original y alternativa comparten reloj; el solver calcula cada pose. Un recorrido imposible se rechaza y uno viable cambia el movimiento. Es simulación contrafactual: no se evalúan fuerzas, materiales ni fabricabilidad.'),
 ('ask', 'Ask the Machine · explicitly labeled local mock',
  'Ask the Machine is clearly labeled as a deterministic mock. It proposes a bounded tool request, KINETICA validates the geometry, and the user confirms before the alternate changes. The real Muse trial failed and remains unverified. This local demonstration does not pretend otherwise.',
  'Ask the Machine está claramente etiquetado como mock determinista. Propone una herramienta acotada, KINETICA valida la geometría y el usuario confirma antes de cambiar la alternativa. El ensayo Muse real falló y sigue sin verificarse; esta demostración no lo presenta como éxito.'),
 ('outro', 'Meta integration · where the real evidence lives',
  'Here is the Meta Model API integration: SAM three point one for segmentation and a guarded Muse Spark adapter. Every request needs a cost estimate and explicit approval; paid inference is blocked by default. KINETICA\'s real SAM run produced three hundred geometry records on a separate third party clip, documented in the repository and not shown here. Real Muse Spark remains unverified.',
  'Esta es la integración con la Meta Model API: SAM 3.1 para segmentación y un adaptador Muse Spark protegido. Cada solicitud exige un presupuesto y aprobación explícita; la inferencia de pago está bloqueada por defecto. La ejecución real de SAM produjo 300 registros de geometría sobre un clip de terceros distinto, documentada en el repositorio y no mostrada aquí. Muse Spark real sigue sin verificarse.'),
]

VARIANT = 'licensed'

def run(command, **kwargs):
    subprocess.run([str(value) for value in command], check=True, **kwargs)

def hash_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def timestamp(value, separator=','):
    ms = int(round(value * 1000)); hours, ms = divmod(ms, 3600000)
    minutes, ms = divmod(ms, 60000); seconds, ms = divmod(ms, 1000)
    return f'{hours:02}:{minutes:02}:{seconds:02}{separator}{ms:03}'

def chunks(text, max_chars=112):
    # Balanced lengths avoid one-word tail cues that flash too briefly to read.
    words = text.split(); count = max(1, -(-len(text) // max_chars))
    while True:
        target = len(text) / count; result=[]; row=[]
        for word in words:
            if row and len(' '.join(row + [word])) > target and len(result) < count - 1:
                result.append(' '.join(row)); row=[]
            row.append(word)
        result.append(' '.join(row))
        if max(len(r) for r in result) <= max_chars: return result
        count += 1

def two_lines(text, limit=56):
    if len(text) <= limit: return text
    words = text.split()
    split = min(range(1, len(words)), key=lambda i: abs(len(' '.join(words[:i])) - len(' '.join(words[i:]))))
    return ' '.join(words[:split]) + '\n' + ' '.join(words[split:])

def prepare():
    OUT.mkdir(parents=True, exist_ok=True)
    entries = [dict(id=identity, title=title, en=en, es=es,
                    audio=str(OUT / f'{index:02}-{identity}.wav'))
               for index, (identity,title,en,es) in enumerate(SCENES)]
    path = OUT / 'narration.json'
    path.write_text(json.dumps(entries, indent=2, ensure_ascii=False), 'utf-8')
    run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',
         ROOT/'scripts/render_demo_narration.ps1','-Manifest',path])
    for entry in entries:
        with wave.open(entry['audio']) as audio:
            entry['audio_duration'] = audio.getnframes() / audio.getframerate()
        entry['minimum_scene_seconds'] = entry['audio_duration'] + 1.0
    path.write_text(json.dumps(entries, indent=2, ensure_ascii=False), 'utf-8')
    print(json.dumps({'chapters':len(entries),'narration_seconds':sum(e['audio_duration'] for e in entries),
                      'scene_minimum_seconds':sum(e['minimum_scene_seconds'] for e in entries)}, indent=2))

def captions(entries, language):
    cues=[]
    for entry in entries:
        phrases=chunks(entry[language]); total=sum(len(s.split()) for s in phrases)
        at=entry['start']+.25
        for phrase in phrases:
            duration=entry['audio_duration']*len(phrase.split())/total
            cues.append((at,min(entry['end']-.15,at+duration),phrase)); at+=duration
    srt='\n\n'.join(f'{i+1}\n{timestamp(start)} --> {timestamp(end)}\n{two_lines(text)}' for i,(start,end,text) in enumerate(cues))+'\n'
    vtt='WEBVTT\n\n'+'\n\n'.join(f'{timestamp(start,".")} --> {timestamp(end,".")}\n{two_lines(text)}' for start,end,text in cues)+'\n'
    (OUT/f'kinetica-demo.{language}.srt').write_text(srt,'utf-8')
    (OUT/f'kinetica-demo.{language}.vtt').write_text(vtt,'utf-8')
    if language=='en':
        header='''[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,Arial,29,&H00FFFFFF,&H00FFFFFF,&H00123F49,&H00123F49,0,0,0,0,100,100,0,0,1,1,0,2,100,100,15,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
        def ass_time(seconds):
            return timestamp(seconds,'.')[1:-1]
        events=[]
        for start,end,text in cues:
            # At most two balanced readable lines in the reserved lower band.
            words=text.split(); middle=len(words)//2
            if len(text)>78:text=' '.join(words[:middle])+r'\N'+' '.join(words[middle:])
            events.append(f'Dialogue: 0,{ass_time(start)},{ass_time(end)},Caption,,0,0,0,,{text}')
        (OUT/'kinetica-demo.en.ass').write_text(header+'\n'.join(events)+'\n','utf-8')

def render():
    import cv2
    import imageio_ffmpeg
    capture=json.loads((OUT/'capture.json').read_text('utf-8'))
    entries=json.loads((OUT/'narration.json').read_text('utf-8'))
    by_id={e['id']:e for e in capture['scenes']}
    # The locked recorder rounds repeats per screencast frame; its media clock can
    # differ from action wall time. Map chapter positions to the recorded clock,
    # preserving every recorded frame at its actual encoded rate. No setpts/speed
    # change or synthetic frames are applied. Chapter samples are visually checked.
    raw_video=cv2.VideoCapture(capture['recording'])
    raw_duration=raw_video.get(cv2.CAP_PROP_FRAME_COUNT)/raw_video.get(cv2.CAP_PROP_FPS)
    raw_video.release()
    clock_scale=raw_duration/capture['capture_stop_wall_seconds']
    opening=capture['opening_trim_seconds']
    trim=opening*clock_scale
    for entry in entries:
        entry.update(by_id[entry['id']])
        entry['start']=(entry['start']-opening)*clock_scale
        entry['end']=(entry['end']-opening)*clock_scale
    total=entries[-1]['end']
    if total>180: raise ValueError(f'Master exceeds confirmed 3-minute limit: {total:.3f}s')
    for language in ('en','es'): captions(entries,language)
    ffmpeg=Path(imageio_ffmpeg.get_ffmpeg_exe())
    # Assemble speech with exact silence between chapter starts. Screen timing
    # remains real time; no altered values, synthetic UI or generated imagery.
    with wave.open(entries[0]['audio']) as first:
        params=first.getparams(); rate=first.getframerate(); sample_width=first.getsampwidth(); channels=first.getnchannels()
    with wave.open(str(OUT/'narration.wav'),'wb') as out:
        out.setparams(params); cursor=0
        for entry in entries:
            target=round((entry['start']+.25)*rate)
            if target<cursor: raise ValueError('Narration chapters overlap')
            out.writeframes(b'\0'*(target-cursor)*sample_width*channels)
            with wave.open(entry['audio']) as sound:
                assert sound.getframerate()==rate and sound.getsampwidth()==sample_width and sound.getnchannels()==channels
                out.writeframes(sound.readframes(sound.getnframes())); cursor=target+sound.getnframes()
        out.writeframes(b'\0'*max(0,round(total*rate)-cursor)*sample_width*channels)
    subtitle='kinetica-demo.en.ass'
    # Burn subtitles in the editorial lower band, retaining the complete captured
    # viewport above. This is video editing, not modification of the application.
    vf=("scale=1920:960:flags=lanczos,pad=1920:1080:0:0:color=0x123f49,"
        f"ass={subtitle},"
        "drawtext=fontfile='C\\:/Windows/Fonts/arial.ttf':text='KINETICA / REALITY LAB  |  AUTHENTIC SCREEN RECORDING"
        f"{'  |  ORIGINAL SYNTHETIC FOOTAGE, NOT A REAL RECORDING' if VARIANT=='original' else ''}':"
        "fontsize=15:fontcolor=0xbcd3ca:x=32:y=978")
    credits=[
        'KINETICA REALITY LAB',
        'MEDIA / ORIGINAL MATERIAL ONLY',
        'Footage: original synthetic clip rendered by scripts/make_original_demo_clip.py',
        'Geometry: derived from known synthetic motion plus noise. Not Meta SAM output.',
        'No third-party footage, music or images. Application code: MIT.',
        'Real Meta SAM 3.1 evidence (300 records) belongs to a separate third-party clip;',
        'documented in the repository, not shown or applied in this video.',
        'Narration synthesized offline. No new inference. Muse live remains unverified.',
    ] if VARIANT=='original' else [
        'KINETICA REALITY LAB',
        'SOURCE FOOTAGE / AUDIOVISUAL LICENSE',
        'Schubkurbelgetriebe (Eitech) - Rhetos - Wikimedia Commons',
        'https://commons.wikimedia.org/wiki/File:Schubkurbelgetriebe_(Eitech).webm',
        'CC BY-SA 4.0 - https://creativecommons.org/licenses/by-sa/4.0/',
        'Changes: excerpt, resize, re-encode, SAM annotations and recorded interface.',
        'Audiovisual adaptation: CC BY-SA 4.0. Application code: MIT.',
        'Narration synthesized offline. No new inference. Muse live remains unverified.',
    ]
    (OUT/'CREDITS.txt').write_text('\n'.join(credits)+'\n','utf-8')
    description='''KINETICA Reality Lab — from footage to testable mechanical hypotheses.

This is a genuine recording of the local working application: Observe authentic
saved Meta SAM 3.1 segmentation; seal a local forecast before Reveal; compare the
same observed frames with constant and linear baselines; change the solver-driven
3D mechanism; review and confirm a clearly labeled deterministic mock tool call.

The preserved SAM result contains 150 boxes and 150 contours: three IDs across
50 frames. Slider identity is human-confirmed; masks do not locate joint centers.
The inspected-data replay (freeze29/horizon8) gives model RMSE9.1046px,
constant23.9297px and linear75.5859px on the same eight observations.
Horizon20 crosses the known source change and all scores are withheld.
These are image-space retrospective results, not physical reconstruction accuracy
or independent prospective validation. Original SAM saw the full clip.
Break Reality is a counterfactual simulation. Forces, materials and buildability
are not evaluated. Ask the Machine is a deterministic mock; real Muse remains
unverified after a failed trial, with original cause and usage undetermined.

SOURCE / RIGHTS
Schubkurbelgetriebe (Eitech) — Rhetos — Wikimedia Commons — CC BY-SA4.0.
https://commons.wikimedia.org/wiki/File:Schubkurbelgetriebe_(Eitech).webm
https://creativecommons.org/licenses/by-sa/4.0/
Changes: excerpt, resize, re-encode, saved SAM annotations and recorded interface.
Proposed audiovisual release: CC BY-SA4.0. Original application code: MIT.
English narration was synthesized entirely offline using Microsoft Zira Desktop.
No music, generated measurement imagery or new model inference was added.

REVIEW STATUS
Prepared locally for entrant review. No upload or publication has been authorized.
Repository/demo links must be added only after separate approval and verification.
'''
    if VARIANT=='original':
        description='''KINETICA Reality Lab — from footage to testable mechanical hypotheses.

This is a genuine recording of the local working application, run on ORIGINAL
SYNTHETIC footage rendered by KINETICA's own code. It is not a real recording.
Observe labeled synthetic geometry; seal a local forecast before Reveal; compare the
same observed frames with constant and linear baselines; see an under-determined
freeze refused; change the solver-driven 3D mechanism; review and confirm a clearly
labeled deterministic mock tool call.

The geometry is derived from the clip's known motion plus measurement noise. It is
not Meta SAM output. The true motion contains a motor speed ripple the model is not
told about. Freeze74/horizon20 gives model RMSE7.67px, constant52.05px and
linear129.82px on the same twenty observations. This checks the pipeline; it is not
evidence about real mechanisms. Break Reality is a counterfactual simulation. Ask the
Machine is a deterministic mock; real Muse remains unverified after a failed trial.

META SAM 3.1 EVIDENCE
KINETICA's real Meta SAM 3.1 run (diagnostic e14d21bb8f3c: 150 boxes + 150 contours,
three IDs over 50 frames) was made on a separate third-party clip. Those detections
belong to that source, are documented in the repository and are not shown here.

MEDIA
All footage, geometry, captions and graphics: original work of the KINETICA entrant.
English narration synthesized entirely offline using Microsoft Zira Desktop.
No music, third-party footage or new model inference. Application code: MIT.

REVIEW STATUS
Prepared locally for entrant review. No upload or publication has been authorized.
'''
    (OUT/'YOUTUBE_DESCRIPTION.txt').write_text(description,'utf-8')
    # The original-media outro shows the Meta connection panel; credits follow it.
    credit_start=entries[-1]['end']-6.5 if VARIANT=='original' else entries[-1]['start']+3
    vf+=f",drawbox=x=0:y=0:w=iw:h=960:color=0x123f49:t=fill:enable='gte(t,{credit_start:.3f})'"
    for i,line in enumerate(credits):
        name=f'credit-{i}.txt';(OUT/name).write_text(line,'utf-8')
        vf+=(f",drawtext=fontfile='C\\:/Windows/Fonts/arial.ttf':textfile='{name}':"
             f"fontsize={50 if i==0 else 25}:fontcolor={'0xf3f2e6' if i==0 else '0xbcd3ca'}:"
             f"x=100:y={160+i*75}:enable='gte(t,{credit_start:.3f})'")
    output=OUT/'KINETICA-Reality-Lab-demo-1080p.mp4'
    run([ffmpeg,'-y','-filter_threads','2','-ss',f'{trim:.3f}','-i',capture['recording'],'-i',OUT/'narration.wav','-vf',vf,
         '-t',f'{total:.3f}','-r','25','-c:v','libx264','-threads','2','-preset','medium','-crf','20',
         '-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-movflags','+faststart',
         '-metadata','title=KINETICA Reality Lab - authentic local demonstration',
         '-metadata','comment='+('Real screen recording of original synthetic footage; no third-party media; offline synthesized narration; publication approval pending' if VARIANT=='original' else 'Real screen recording; offline synthesized narration; Eitech Rhetos CC BY-SA 4.0; audiovisual adaptation CC BY-SA 4.0; publication approval pending'),output],
        cwd=OUT, stdout=subprocess.DEVNULL,stderr=(OUT/'encode.log').open('w',encoding='utf-8'))
    video=cv2.VideoCapture(str(output)); frames=int(video.get(cv2.CAP_PROP_FRAME_COUNT)); fps=video.get(cv2.CAP_PROP_FPS)
    width=int(video.get(cv2.CAP_PROP_FRAME_WIDTH));height=int(video.get(cv2.CAP_PROP_FRAME_HEIGHT));video.release()
    assert width==1920 and height==1080 and 0<frames/fps<=180.05
    for entry in entries:
        position=(entry['start']+entry['end'])/2
        video=cv2.VideoCapture(str(output));video.set(cv2.CAP_PROP_POS_MSEC,position*1000);ok,frame=video.read();video.release()
        if not ok:raise ValueError('Could not decode chapter QA frame')
        cv2.imwrite(str(OUT/f"qa-{entry['id']}.jpg"),frame)
    info=dict(schema='kinetica-demo-video/1',file=output.name,sha256=hash_file(output),
              bytes=output.stat().st_size,duration_seconds=frames/fps,width=width,height=height,fps=fps,
              video_codec='H.264',pixel_format='yuv420p',audio_codec='AAC',
              narration='Offline synthesized Microsoft Zira Desktop, English',
              captions=['English burned-in','English SRT/VTT','Spanish SRT/VTT'],
              footage='Authentic Playwright screen recording, no values/UI altered'+('; on-screen clip is original synthetic media' if VARIANT=='original' else ''),
              variant=VARIANT,
              source_sha256=capture['source_sha256'],source_export_sha256=capture['source_export_sha256'],
              raw_recording_sha256=hash_file(Path(capture['recording'])),
              new_inference=False,paid_requests=0,muse='deterministic mock; live unverified',
              publication_authorized=False,audiovisual_license='original work; licence chosen by entrant at upload' if VARIANT=='original' else 'CC BY-SA 4.0',
              raw_recording_duration=raw_duration,opening_trim_seconds=trim,recorded_clock_scale=clock_scale,
              chapters=[{key:entry[key] for key in ('id','title','start','end','en','es','audio_duration')} for entry in entries])
    (OUT/'video-manifest.json').write_text(json.dumps(info,indent=2,ensure_ascii=False),'utf-8')
    for language in ('en','es'):
        transcript='\n\n'.join(f"{timestamp(e['start'],'.')} — {e['title']}\n{e[language]}" for e in entries)
        (OUT/f'transcript.{language}.txt').write_text(transcript+'\n','utf-8')
    print(json.dumps({k:v for k,v in info.items() if k!='chapters'},indent=2))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    action=parser.add_mutually_exclusive_group(required=True);action.add_argument('--prepare',action='store_true');action.add_argument('--render',action='store_true')
    parser.add_argument('--variant',choices=('licensed','original'),default='licensed',help='original: narration/credits for the original synthetic media capture')
    args=parser.parse_args()
    global OUT,SCENES,VARIANT
    if args.variant=='original':
        OUT=ROOT/'output/submission-video-original';SCENES=ORIGINAL_SCENES;VARIANT='original'
    prepare() if args.prepare else render()

if __name__=='__main__':main()
