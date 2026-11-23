# CyberShield — Bandeja de revisión de planes por proyecto (fase 014)

## Alcance
El diagnóstico de ZIP/GitHub produce un plan documental; ahora existe una
bandeja independiente para revisarlo y conservar decisiones. **No concede
ejecución de defensas** ni modifica los controles históricos c1–c8.

### Archivos
- \`backend/migrations/014_project_plan_review_queue.sql\`: tablas nuevas
  \`cybershield_project_review_plans\`,
  \`cybershield_project_review_tasks\` y
  \`cybershield_project_review_history\`. Ningún ALTER de tablas existentes.
- \`backend/app/services/intelligence/project_plan_store.py\`:
  almacenamiento, validación, transiciones y bitácora transaccional.
- \`backend/app/api/project_plans.py\`: endpoints REST autenticados
  para roles \`admin\` y \`engineer\`.
- \`frontend/src/pages/ProjectPlanReviewPage.tsx\`:
  bandeja de planes con detalle, observaciones y decisiones.
- \`frontend/src/components/ProjectSecurityPlanDraft.tsx\`:
  opción adicional «Enviar a revisión» para tareas seleccionadas.
- Rutas UI \`/#/code-review\` y \`/#/project-plans\`.

## Flujo y seguridad
1. El usuario analiza su proyecto y selecciona tareas en el plan.
2. El servidor recibe solo \`project_name\` y una lista de IDs
   reconocidos. **No recibe ZIP ni fragmentos de código en este paso**.
3. El servidor vuelve a construir acciones y prioridades de un catálogo
   de reglas permitido. No acepta títulos o comandos del cliente.
4. Se guarda el plan con \`review_required\` para todas las tareas.
5. El ingeniero puede registrar:
   \`review_required -> under_review\` o \`rejected\`;
   \`under_review -> planned\` o \`rejected\`.
   Los estados terminales no se pueden revertir desde esta interfaz.
6. La auditoría guarda actor, estado anterior y nuevo, comentarios y
   fecha dentro de la misma transacción que la decisión.
7. \`planned\` significa **aceptada para planificación**: NO instalada,
   aprobada para ejecución, ni validada en el proyecto.
8. No existen endpoints para instalar, activar, adjuntar scripts, ejecutar
   comandos, cargar archivos de protección ni modificar controles.

## Atención: base compartida con el servicio principal
El backend de pruebas 8001 se ha iniciado con
\`--env-file /mnt/c/Users/Giovas128/downloads/CyberSHield/backend/.env\`.
Esto implica que **podría compartir PostgreSQL con el principal 8000**.
Por tanto **NO APLICAR LA MIGRACIÓN 014 TODAVÍA** hasta verificar y aislar
la base de pruebas. El backend no crea tablas automáticamente.

Si faltan las tablas, los endpoints de bandeja devuelven HTTP 503 con
un mensaje explícito; el escaneo, las propuestas documentales y la
exportación JSON permanecen disponibles.

### Validación del código sin tocar PostgreSQL
\`\`\`bash
cd /mnt/c/Users/Giovas128/downloads/CyberShield-ThreatCatalog
git pull --ff-only

PYTHONPATH=backend /mnt/c/Users/Giovas128/downloads/CyberSHield/backend/venv-wsl/bin/python \
  -m unittest discover -s backend/tests \
  -p 'test_project_plan_store.py' -v

PYTHONPATH=backend /mnt/c/Users/Giovas128/downloads/CyberSHield/backend/venv-wsl/bin/python \
  -m unittest discover -s backend/tests \
  -p 'test_project_security_plan.py' -v

cd frontend && npm run build
\`\`\`

Después de pruebas, reiniciar solo el proceso de backend 8001 identificado
y mantener intacto 8000. Abrir \`http://localhost:8001/#/project-plans\`.
Mientras la migración no se haya aplicado a una base **aislada**, aparecerá
un aviso de indisponibilidad: es intencional. No efectuar cambios SQL
hasta revisar aislamiento y respaldo.

## Fase posterior — paquetes de protecciones descargables
Por técnica MITRE o vulnerabilidad CISA podrá mostrarse la **disponibilidad**
de un paquete defensivo. El botón «Descargar protección» solo se habilitará
si el paquete ha sido revisado y aprobado para un entorno concreto.
Cada paquete deberá indicar tipo de defensa, plataforma, versión, dependencias,
hash SHA-256, revisión técnica, documentación, instrucciones de rollback,
prueba de laboratorio y vínculo de trazabilidad a técnica/CVE.
Cuando no exista una protección pertinente, mostrar «Sin protección validada»
y ofrecer acciones documentales. Las vulnerabilidades que requieren parche
de fabricante no deben simular tener scripts universales.
Ningún paquete debe autoejecutarse tras la descarga.
