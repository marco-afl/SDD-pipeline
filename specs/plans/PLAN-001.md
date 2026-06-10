## Plan: US-001 — Transferencia de dinero entre cuentas NovaPay

**Story de referencia:** `specs/stories/US-001.md`

---

### Archivos involucrados

| Archivo | Acción | Entorno | Notas |
|---------|--------|---------|-------|
| `src/api/routes/transfers.py` | crear | dev | Endpoint `POST /v1/transfers` |
| `src/api/schemas/transfer_schema.py` | crear | dev | Validación y serialización de request/response |
| `src/services/transfer_service.py` | crear | dev | Lógica de negocio: atomicidad, idempotencia |
| `src/services/audit_service.py` | crear | dev | Emisión de eventos al log de auditoría |
| `src/repositories/account_repository.py` | crear | dev | Consulta de saldo y bloqueo de fondos |
| `src/repositories/transfer_repository.py` | crear | dev | Persistencia de transferencias e idempotency keys |
| `src/models/transfer.py` | crear | dev | Modelo de datos Transfer |
| `src/models/audit_log.py` | crear | dev | Modelo de datos AuditLog |
| `src/errors/transfer_errors.py` | crear | dev | Excepciones de dominio (InsufficientFunds, etc.) |
| `tests/test_transfers.py` | crear | dev | Tests unitarios e integración del endpoint |

> ⚠️ Ningún archivo de producción existente será modificado en esta story.

---

### Tareas técnicas

**T-1: Modelos de datos**
- Definir `Transfer`: `transfer_id`, `origin_account`, `destination_account`, `amount`, `currency`, `description`, `status`, `idempotency_key`, `created_at`.
- Definir `AuditLog`: `event_id`, `transfer_id`, `origin_account`, `destination_account`, `amount`, `initiated_by`, `ip_address`, `timestamp`.

**T-2: Validación de request (`transfer_schema.py`)**
- Validar presencia y tipo de campos obligatorios.
- Validar `amount > 0` y máximo 2 decimales (rechazar con `INVALID_AMOUNT` si falla).
- Validar que `origin_account != destination_account`.
- Marcar `description` como opcional (string, max 255 chars).
- Validar formato de `idempotency_key` (UUID v4).

**T-3: Repositorios**
- `AccountRepository.get_balance(account_id)` — consulta saldo disponible.
- `AccountRepository.lock_funds(account_id, amount)` — bloqueo pesimista o transaccional.
- `TransferRepository.find_by_idempotency_key(key)` — busca transferencia previa.
- `TransferRepository.save(transfer)` — persiste nueva transferencia.

**T-4: Servicio de transferencia (`transfer_service.py`)**
1. Verificar `idempotency_key`:
   - Si existe con mismos parámetros → devolver respuesta guardada (no procesar).
   - Si existe con parámetros distintos → lanzar `IdempotencyConflict`.
2. Verificar existencia de cuenta origen (pertenece al cliente autenticado).
3. Verificar existencia de cuenta destino.
4. Verificar saldo suficiente.
5. Ejecutar débito + crédito dentro de una transacción de base de datos.
6. Persistir `Transfer` con `status: completed`.
7. Emitir evento a `AuditService`.

**T-5: Servicio de auditoría (`audit_service.py`)**
- Registrar `AuditLog` con todos los campos requeridos por CA-4.
- El registro de auditoría debe ser independiente de la transacción principal (no debe hacer rollback si el log falla; solo alertar).

**T-6: Errores de dominio (`transfer_errors.py`)**
- `InsufficientFundsError` → `422 INSUFFICIENT_FUNDS`
- `OriginAccountNotFoundError` → `404 ORIGIN_ACCOUNT_NOT_FOUND`
- `DestinationAccountNotFoundError` → `404 DESTINATION_ACCOUNT_NOT_FOUND`
- `InvalidAmountError` → `400 INVALID_AMOUNT`
- `SameAccountTransferError` → `400 SAME_ACCOUNT_TRANSFER`
- `IdempotencyConflictError` → `409 IDEMPOTENCY_CONFLICT`

**T-7: Endpoint (`transfers.py`)**
- Registrar ruta `POST /v1/transfers`.
- Extraer `ip_address` del request para auditoría.
- Mapear excepciones de dominio → respuestas HTTP con cuerpo estándar.
- Devolver `201 Created` en éxito.

**T-8: Tests (`test_transfers.py`)**
- Happy path: transferencia exitosa, verifica débito/crédito y log de auditoría.
- Idempotencia: mismo request dos veces → segunda llamada devuelve la misma respuesta, sin doble débito.
- Idempotencia con conflicto: misma key, distinto monto → `409`.
- Saldo insuficiente → `422`.
- Cuenta origen inexistente → `404`.
- Cuenta destino inexistente → `404`.
- Monto negativo → `400`.
- Monto con 3 decimales → `400`.
- Misma cuenta → `400`.

---

### Decisiones de diseño pendientes de aprobación

| # | Opción A | Opción B | Impacto |
|---|----------|----------|---------|
| D-1: **Lenguaje/framework** | ✅ Python + FastAPI | Python + Flask | FastAPI: validación automática con Pydantic, async nativo. |
| D-2: **Base de datos** | ✅ SQLite (prototipo) | PostgreSQL | SQLite: zero infra. Migración a Postgres: solo cambiar DATABASE_URL. |
| D-3: **Mecanismo de idempotencia** | ✅ Tabla en DB | Cache Redis con TTL | Durable y consistente, sin dependencias adicionales. |
| D-4: **Auditoría** | ✅ Tabla `audit_logs` | Archivo JSON | Consultable y relacional, mismo motor que el resto. |

---

### Riesgos

- **Concurrencia:** sin bloqueo pesimista, dos transferencias simultáneas desde la misma cuenta pueden provocar sobregiro. Mitigación: usar `SELECT FOR UPDATE` o transacción serializable.
- **Fallo entre débito y crédito:** si el proceso muere entre ambas operaciones, el cliente queda en estado inconsistente. Mitigación: operación dentro de una única transacción de DB.
- **Auditoría bloqueante:** si el insert de auditoría falla y está dentro de la transacción principal, puede hacer rollback de una transferencia ya realizada. Mitigación: auditoría fuera de la transacción (T-5).

---

### Estado

- [ ] Borrador &nbsp;&nbsp;[x] Aprobado
