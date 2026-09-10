# UE-Xchanges-OS — Acta de consciencia operativa

Seal: `2026-09-10T14:46:00+02:00`

> “Consciencia” aquí significa **estado explícito de conocimiento operativo**: qué sabemos, qué no sabemos, qué inferencias están prohibidas y qué debe comprobar un sucesor antes de actuar. No implica consciencia subjetiva ni convierte este documento en autoridad.

## 1. Lo que el sistema sabe con alta confianza al sellar

- El repositorio `rotprods/UE-Xchanges-OS` tiene como `main` observado `349f63f2109e40ab6cba960c7311456a5d7ae906`.
- Ese `main` incluye PR69: bounded health para writers normales basado en la sesión exacta actual + BootstrapGuard + leases realmente no expirados; la deuda histórica queda separada del critical path de autorización.
- PR67 endureció WriterAuthorizationReceipt/integridad; PR68 hizo visible el stale lifecycle de `ACTIVE_READ_ONLY` sin convertirlo en writer; PR69 separó higiene histórica de salud de autorización normal.
- El scheduler nativo de ChatGPT **sí puede despachar y completar** una tarea mínima sin tools. Eso no certifica RG2.2.
- El canario de control-plane V3 sí demostró lifecycle `receipt → lease ACTIVE → RELEASED → session completed` sin source/runtime/domain mutation.
- No existe evidencia observada en este sello de un `SCHEDULER_PRODUCTION_CANARY_PASS` completo.
- El dispatcher recurrente `UEX Runtime Dispatcher` está **deshabilitado**.
- Las sesiones PCV3, Stage-A y PCV4 fueron reconciliadas a `FAILED` por RPLs de control-plane; no se les atribuyó lease/source/projection success.
- CPR12 saneó la clase de leases huérfanos que rompía `lease_fencing_integrity`; los repair leases usados quedaron `RELEASED`.
- Los repair leases recientes CPR13/CPR14 también quedaron `RELEASED` por read-back exacto.
- En la ventana reciente inspeccionada no se observó ningún lease realmente vigente que autorizase un writer concurrente; un sucesor debe volver a consultar el inventario completo antes de escribir.

## 2. Lo que NO sabemos y no debemos fingir saber

- No se ha refrescado en este sello la totalidad del dominio `Opportunities/Applications/Human_Gates`; cualquier cifra antigua (176/164/etc.) es histórica hasta nueva lectura Drive.
- No se ha procesado en esta operación ninguna nueva fuente Gmail/Form/official; por tanto no sabemos si Human Frontier, receipts o deadlines cambiaron después del último RuntimeGraph materializado.
- No sabemos que el problema genérico “There was a problem with your scheduled task” tenga una única causa. Hemos aislado varios defectos reales de runtime/coordination, pero no tenemos un error interno completo del scheduler para todos los avisos históricos.
- No sabemos si existe un evento `SESSION_COMPLETED` posterior a `EVT-20260910T132147-CPR14-008` para CPR14. La fila `Agent_Sessions` sí aparece `COMPLETED`; si el evento no existe, hay una divergencia de coordinación que debe auditarse, no inventarse.
- No sabemos si un próximo canario productivo terminará dentro del presupuesto de una sola Scheduled Task; hay que medirlo, no asumirlo.
- No sabemos que Todoist runtime projection esté completamente vinculada por `runtime_action_id → task_id`; ausencia de binding exacto significa no-op, no fuzzy repair.

## 3. Invariantes que no se negocian

1. `Official/organiser/receipt evidence > Drive canonical operational truth > GitHub contracts > RuntimeGraph derived projections > UI/task projections > chat`.
2. `UNKNOWN` es deuda de verificación, nunca permiso.
3. `SubmissionAttempt != SubmissionReceipt`.
4. Gmail no se transforma directamente en receipt.
5. Fuzzy title matching, embeddings y similitud semántica sirven para recuperación/discovery, **nunca** para autorizar una mutación de estado.
6. `ACTIVE` textual no implica lease vivo; manda `expires_at` + owner + current policy + event evidence.
7. `ACTIVE_READ_ONLY` nunca se promociona a writer por conveniencia.
8. WriterAuthorizationReceipt es evidencia de coordinación, no domain authority ni external capability.
9. Después de persistir una autorización, el lease exacto debe adquirirse inmediatamente; no intercalar trabajo caro.
10. Toda mutación de fila de coordinación resuelve stable ID en el borde de escritura y hace read-back exacto.
11. RG2.2 percibe/reconcilia; RG2.3 ejecuta acciones reversibles. RG2.2 no ejecuta `Agent_Next`.
12. Pagos, login/MFA/CAPTCHA, secretos, OTP/cookies, external PREFILL y Submit irreversible permanecen fuera del flujo genérico.
13. Historial incierto nunca se convierte en `COMPLETED` para “limpiar”.
14. Un PASS de scheduler simple no es un PASS de RuntimeGraph.
15. Un PASS de un solo canario productivo no basta para producción recurrente estable.

## 4. Modelo mental actual

```text
                   EXTERNAL / CANONICAL AUTHORITY
Official / organiser / receipt / private Drive CRM + EventBus
                            |
                            v
                        CGEV2
        provenance + sessions + leases + events + recovery
                            |
          +-----------------+------------------+
          |                                    |
          v                                    v
   RuntimeGraph RG2.x                   COS / semantic graph
 exact-ID deterministic                 retrieval / topology
 execution projections                  20D / graphify / search
          |                                    |
          +-----------------+------------------+
                            |
                            v
                Human / Agent / System frontier
```

COS ayuda a encontrar, relacionar y navegar conocimiento. **No crea autoridad.** CGEV2 garantiza continuidad, procedencia y control de escritura. RuntimeGraph convierte evidencia explícita en ejecución determinista.

## 5. Riesgo dominante actual

El riesgo ya no es principalmente “un lease ACTIVE viejo bloquea todo”. Ese defecto fue aislado y saneado. El riesgo dominante es **liveness y presupuesto de activación del canario productivo**: conseguir que una Scheduled Task complete cold bootstrap, bounded health, WriterAuthorization, lease, un micro-batch, read-back y cierre fuerte dentro de una sola ejecución.

La solución correcta no es ampliar authority ni eliminar gates. Es reducir trabajo en critical path, medir timings y mantener micro-batches.

## 6. Regla de humildad operacional

Cuando dos superficies discrepen:

- preservar ambas observaciones;
- identificar cuál es autoritativa para ese hecho concreto;
- no “sincronizar” por estética;
- emitir finding/RPL cuando sea control-plane;
- no mutar dominio desde una proyección;
- no afirmar éxito hasta read-back.

## 7. Pregunta que debe poder contestar cualquier sucesor antes de escribir

> “¿Qué evidencia exacta, bajo qué autoridad, para qué stable ID, con qué sesión/lease, sobre qué `main` y qué watermark, autoriza ESTA transición y cómo demostraré el resultado y el cierre?”

Si no puede contestarla, el agente sigue read-only.
