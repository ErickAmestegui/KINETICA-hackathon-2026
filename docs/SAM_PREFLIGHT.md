# Experimento SAM 3.1: preparación final sin gasto

Fecha: 28 de octubre de 2026. Base revisada: `8643e90`, árbol limpio al comenzar. No se creó otro proyecto. Skills cargadas: `systematic-debugging`, `context-window-management`, `playwright` (nombre instalado). No se instalaron dependencias ni skills.

## Presupuesto final

| Campo | Valor comprobado |
|---|---|
| Archivo | `output/sam-local/eitech-50-cfr.mp4` |
| Modelo | `sam-3.1` |
| Prompt | `white foam block` |
| Regiones manuales | 0; una región sustituiría el prompt textual |
| Fotogramas | 50 de origen, 50 facturables |
| Resolución / duración | 960×540 /2.00 segundos /25 fps |
| Códec | H.264 High, avc1, yuv420p, MP4 |
| Solicitudes | Una; sin reintentos automáticos |
| Tarifa consultada | US$0.20 /1,000 fotogramas; mínimo 50 |
| Estimación | **US$0.0100**, sujeta a las condiciones vigentes de la cuenta |
| Autorización actual | **Bloqueada: `paid_enabled=false`** |

[Documentación de segmentación](https://dev.meta.ai/docs/sam/segmenting) y [tarifas oficiales](https://dev.meta.ai/docs/pricing-rate-limits), consultadas durante esta preparación. Un concepto nominal concreto es apropiado para SAM; una máscara identifica una región visible, no un centro de articulación. La subida documentada es síncrona y se referencia mediante `input_video.file_id`. Los resultados vacíos pueden ser respuestas completas válidas. Nada de esto constituye evidencia de una inferencia real exitosa de KINETICA.

## Verificación del video

- OpenCV y FFmpeg decodificaron los 50 fotogramas, sin errores. Chrome reprodujo el clip hasta `ended`, sin `video.error` ni errores de ejecución de la página.
- Los hashes SHA-256 del clip y del original coinciden con el manifiesto creado previamente. El original sigue teniendo 442 fotogramas y no se modificó.
- Se compararon **todos los fotogramas del clip** con los fotogramas 150–199 del original, reducidos a 960×540. PSNR medio 41.13 dB; son diferencias esperables de escalado y recompresión, no una métrica de seguimiento o de SAM. Se inspeccionó también un fotograma: corresponde al mecanismo Eitech y sus bloques de espuma.
- Evidencia privada: `output/sam-local/preflight-video.json`, `eitech-50-cfr.json`, `preflight-frame.jpg`. No se versionan videos ni esos resultados privados.

El clip fue importado **sólo al backend local de KINETICA** para verificar su recorrido. No se envió a Meta ni a ningún servicio externo.

## Correcciones y pruebas

**Presupuesto obsoleto reproducido:** una prueba de navegador mostró que el presupuesto de 442 fotogramas permanecía visible después de importar el clip de 50. Se invalida ahora al importar/restaurar un estudio. Además, un presupuesto sólo aparece y puede autorizarse si coincide con el ID del video seleccionado, el modelo y una solicitud. Se muestran nombre, número de fotogramas, resolución y duración.

El backend devuelve esa identidad junto al presupuesto y exige `video_id` en `/api/meta/run`. Un ID distinto al del token se rechaza con HTTP 409; los tokens vencidos o ya consumidos se rechazan con HTTP 403. Los tokens siguen caducando a los cinco minutos; el presupuesto de esta preparación deberá generarse de nuevo después de cualquier autorización futura.

**Bloqueo real local comprobado:** con el servidor reportando `paid_enabled=false`, se obtuvo un presupuesto local de US$0.0100 para 50 fotogramas. Un POST local a `/api/meta/run` con `approved=false` fue rechazado con HTTP 403 antes de crear transporte externo. En las pruebas aisladas, también se comprobó que `approved=true` no supera la bandera de pago falsa. No se modificó ninguna variable de autorización del operador.

**Capas del visor:** no se reprodujo la superposición reportada en Chrome durante esta sesión. Drei usa índices de capa muy altos; se confinó explícitamente el visor mediante `isolation:isolate`. La prueba verifica que la ventana cubre las etiquetas y que éstas siguen seleccionando piezas después de cerrar la ventana. No hubo rediseño.

**Mocks honestos:** los tres resultados `completed`, `incomplete` y `failed` muestran ahora `SIMULATED TEST — no real Meta inference` cuando proceden de la fixture. La etiqueta se conserva en el resultado guardado/exportado. Las rutas de inferencia del navegador están interceptadas y las pruebas Python bloquean transportes externos.

Resultados:

- **71 pruebas Python aprobadas**: motor, visión, parser, diagnósticos seguros, limpieza, presupuesto, bloqueo, discrepancia de clip, caducidad y uso único.
- **16 pruebas TypeScript aprobadas**, incluyendo identidad del presupuesto, gate falso y etiqueta de simulación.
- **10 escenarios Playwright aprobados**: los ocho anteriores y dos nuevos de capas/presupuesto/reproducción. Los estados SAM proceden exclusivamente de mocks. Tras ajustar el color de los avisos simulados, se recompiló y se repitieron los seis escenarios SAM/preflight: seis aprobados.
- **Build de producción correcto**. Persisten el aviso de tamaño del bundle y la deprecación Starlette/httpx del TestClient; no se actualizaron paquetes fuera del alcance.
- Capturas: `output/playwright/sam-final-budget.png`, `sam-modal-layering.png`, `sam-mock-completed.png`, `sam-mock-incomplete.png`, `sam-mock-failed.png`.
- Evidencia del presupuesto local, sin token: `output/sam-local/final-budget.json`.

## Estado y pendientes

Se hicieron **cero solicitudes a la API de Meta**: ninguna subida, inferencia, consulta de catálogo o eliminación remota. Las únicas lecturas externas fueron páginas públicas de documentación. No se consumieron créditos ni se configuraron pagos. La clave no se mostró ni se incorporó a pruebas.

La causa del HTTP 502 anterior sigue desconocida. Siguen pendientes el comportamiento real del proveedor, consumo contabilizado, formato de una respuesta auténtica, decodificación completa en ese caso y eliminación efectiva del archivo remoto. El estado del archivo de la solicitud anterior tampoco se comprobó. Una desconexión después de enviar la inferencia puede implicar gasto aunque el resultado local falle; no reintentar automáticamente. Véase [SAM_REPAIR.md](SAM_REPAIR.md).

## Procedimiento futuro: únicamente después de autorización explícita nueva

1. Obtener aprobación específica para **una** solicitud de `sam-3.1`, este clip de 50 fotogramas, prompt `white foam block`, sin regiones, y el importe estimado. Confirmar la tarifa/condiciones de cuenta vigentes y el permiso para transferir el clip. Esta preparación no concede ese permiso.
2. Conservar `MODEL_API_KEY` exclusivamente en el entorno backend o `.env` privado existente. No copiarlo al chat, frontend, comandos ni logs. Sólo después de la aprobación, el operador puede habilitar temporalmente `META_ALLOW_PAID=true` en ese archivo privado. Verificar que ninguna variable de entorno de mayor prioridad lo contradice.
3. Reiniciar el proceso KINETICA para cargar el cambio. `Start-Kinetica.ps1` **no reinicia** un servidor ya activo. Desde la raíz, detener únicamente el proceso comprobado de KINETICA y volver a iniciar:

   ```powershell
   $listeners=Get-NetTCPConnection -State Listen -LocalPort 8000 -ErrorAction SilentlyContinue
   foreach($listener in $listeners){
     $proc=Get-CimInstance Win32_Process -Filter "ProcessId = $($listener.OwningProcess)"
     if($proc.CommandLine -notlike '*uvicorn*backend.main:app*'){throw 'Proceso inesperado; no detener'}
     Stop-Process -Id $listener.OwningProcess
   }
   .\scripts\Start-Kinetica.ps1
   ```

4. Recargar `http://127.0.0.1:8000/`. Importar exactamente `<USER_HOME>\Documents\KINETICA\output\sam-local\eitech-50-cfr.mp4`. Abrir **Model connections**, seleccionar **SAM 3.1**, escribir **white foam block** y comprobar **0 selected regions**. Preparar un presupuesto nuevo.
5. Antes de pulsar nada, comprobar en la tarjeta: **eitech-50-cfr.mp4**, **50 source frames**, **960×540**, **2.00 s**, **1 request**, **US$0.0100** si la tarifa sigue igual. Cualquier diferencia obliga a detenerse y revisar; no reutilizar una tarjeta de 442 fotogramas.
6. Pulsar **Authorize this paid request** una sola vez. Esperar el desenlace sin recargar, repetir ni preparar otra solicitud. El token se consume una vez. Conservar el estado final, número de registros, diagnósticos, `usage.video_frames_processed` cuando esté disponible y resultado de limpieza. No interpretar `completed` como reconstrucción verificada.
7. Después del único intento —éxito, parcial o fallo—, volver a `META_ALLOW_PAID=false` y reiniciar con el mismo procedimiento. Confirmar que el estado local vuelve a falso. Exportar el reporte y guardar evidencias privadamente. Si la limpieza falla o el estado de la subida es desconocido, revisar la retención remota mediante una operación expresamente autorizada; no repetir la inferencia.

**No ejecutar estos pasos de habilitación durante la preparación actual.**
