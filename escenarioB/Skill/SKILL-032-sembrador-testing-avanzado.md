# SKILL-032 — Sembrador testing avanzado

**Spec:** SPEC-033  
**Cuándo usar:** Regenerar BD MySQL (`laboratorioB`) con dataset coherente para demos y testing avanzado.

---

## Pasos

1. Confirmar `App/.env` → `DATABASE_URL=.../laboratorioB`.
2. Actualizar `seed_coherent.py` según SPEC-033 (2 periodos, 20 docentes, 400 estudiantes, staff).
3. Cambiar `setup_mysql.py` para invocar `seed_coherent` (no `seed_massive`).
4. Desde `App/backend` con venv:
   ```powershell
   .\.venv\Scripts\python.exe setup_mysql.py
   ```
5. Verificar conteos: careers=3, terms=2, teachers=20, students=400, staff users presentes.
6. Smoke: login `docente01`, `est0001`, `rector`, `coord01`, `secretaria`, `tutor1`, `soporte`.

---

## Checklist

- [x] SPEC-033 creado
- [x] `seed_coherent.py` con volúmenes y coherencia
- [x] `setup_mysql.py` usa seed coherente
- [x] BD regenerada sin errores
- [x] Credenciales impresas al final del seed
