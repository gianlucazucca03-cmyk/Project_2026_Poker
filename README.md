# Event Manager — Progetto Web Programming 2026

> 🇬🇧 **English version**: [README_EN.md](README_EN.md)

---

## Panoramica del progetto

È stato richiesto di progettare un sistema per la gestione di eventi.
La parte frontend è già sviluppata.
Il compito consiste nell'implementare il database e le API richieste.

Per poter superare l'esame, ogni studente, individualmente o in gruppo, dovrà:
- completare i progetti;
- creare una presentazione che mostri il processo di sviluppo (chi ha fatto cosa). Nella presentazione è richiesto che tutti i membri presentino qualcosa.

Si consiglia di formare gruppi (**massimo 4 persone per gruppo**) per velocizzare l’implementazione.

---

## Valutazione

Il progetto **vale fino a 10 punti** nella valutazione finale. Il punteggio rimanente è dato dal voto dello scritto (max 23 punti). Se lo studente ottiene \>30 punti, il voto includerà la lode.
- Si devono implementare almeno le API non opzionali. L’implementazione di **tutte** le API (obbligatorie + opzionali) darà il **punteggio massimo**.
- Il superamento della pipeline CI/CD è **obbligatorio** prima della consegna.

---

## Consegna

Tutti gli step devono essere completati **prima** di fissare l'appuntamento per l'esame orale.

Inviare una mail a:

- <maura.pintor@unica.it>

La mail deve contenere:

1. Il link al repository pubblico su GitHub che contiene il codice del progetto svolto.
   > ⚠️ **La pipeline CI/CD deve essere superata prima della consegna.** Se la pipeline fallisce, il progetto non può essere consegnato.
3. I nomi e le matricole di tutti i componenti del gruppo.
4. La presentazione in pptx o pdf.

In seguito, si fisserà una data per la presentazione (online o in presenza).

---

## Installazione e avvio

Il codice da cui partire si trova al seguente link:
<https://github.com/unica-web/project_2026/tree/main>

### 1. Clonare il repository

```bash
git clone https://github.com/asotgiu/progetto_pw_26.git
cd progetto_pw_26
```

### 2. Creare e attivare un ambiente virtuale

```bash
# con venv
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# oppure con conda
conda create -n pw26 python=3.12
conda activate pw26
```

### 3. Installare le dipendenze

```bash
pip install -r requirements.txt
```

### 4. Avviare il server

```bash
# modalità sviluppo con auto-reload
fastapi dev

# oppure esplicitamente
uvicorn app.main:app --reload
```

L'applicazione sarà disponibile su <http://127.0.0.1:8000>.
La documentazione interattiva delle API (Swagger UI) si trova su <http://127.0.0.1:8000/docs>.

---

## Database

Il sistema usa un database **SQLite** (file: `app/data/database.db`) gestito tramite **SQLModel** (basato su SQLAlchemy + Pydantic).

Sono presenti **3 tabelle**:

| Tabella | Chiave primaria | Descrizione |
|---|---|---|
| `event` | `id` (intero assegnato automaticamente) | Memorizza gli eventi |
| `user` | `username` (stringa, impostata alla creazione) | Memorizza gli utenti |
| `registration` | `(username, event_id)` composta | Collega utenti ed eventi |

### Implementare i modelli ORM

Bisogna implementare le classi ORM `User` ed `Event` rispettivamente in `app/models/user.py` e `app/models/event.py`.
**I nomi delle classi devono essere esattamente `User` ed `Event`**, altrimenti il frontend e il codice esistente smetteranno di funzionare.

Dopo aver definito le classi, importarle in `app/data/db.py` affinché `SQLModel.metadata.create_all(engine)` le rilevi e crei le tabelle al primo avvio.

```python
# app/data/db.py — assicurarsi che questi import siano presenti
from app.models.event import Event
from app.models.user import User
from app.models.registration import Registration
```

Per il campo `date` del modello `Event` usare il tipo `datetime` di Python:

```python
from datetime import datetime
```

La tabella `Registration` è già implementata — non modificarla.

---

## Linee guida per lo sviluppo

- **Documentare il codice** — ogni funzione/metodo deve avere un docstring che ne descriva il comportamento.

- **Validare i dati di input** — le API devono sempre effettuare correttamente la validazione dei dati ricevuti in input.

- **Usare il database** — i dati devono essere persistenti nel database SQLite tramite SQLModel.
  Non usare strutture dati Python in memoria (liste di dizionari, variabili globali, ecc.).

- **Nessuna regressione** — le API sono *aggiunte* di funzionalità. Il server deve continuare a funzionare correttamente con il frontend già fornito.

---

## API reference

Tutte le API devono essere implementate sotto i percorsi indicati.
Le API contrassegnate con **(opzionale)** danno punti aggiuntivi ma non sono strettamente necessarie.

---

### /events

#### `GET /events`

Restituisce la lista di tutti gli eventi esistenti.

**Risposta** `200 OK`:
```json
[
  {
    "title": "string",
    "description": "string",
    "date": "2026-05-22T16:46:29.137Z",
    "location": "string",
    "id": 0
  }
]
```

---

#### `POST /events`

Crea un nuovo evento.

**Corpo della richiesta**:
```json
{
  "title": "string",
  "description": "string",
  "date": "2026-05-22T16:55:14.958Z",
  "location": "string"
}
```

**Risposta** `200 OK` o `201 Created`.

---

#### `GET /events/{id}`

Restituisce l'evento con l'`id` indicato.

**Risposta** `200 OK`:
```json
{
  "title": "string",
  "description": "string",
  "date": "2026-05-22T16:56:30.590Z",
  "location": "string",
  "id": 0
}
```

**Risposta** `404 Not Found` se l'evento non esiste.

---

#### `PUT /events/{id}`

Aggiorna un evento esistente.

**Corpo della richiesta**:
```json
{
  "title": "string",
  "description": "string",
  "date": "2026-05-22T16:57:12.873Z",
  "location": "string"
}
```

**Risposta** `200 OK`.  
**Risposta** `404 Not Found` se l'evento non esiste.

---

#### `POST /events/{id}/register`

Registra un utente all'evento con l'`id` indicato.
Se l'utente non esiste ancora nella tabella `user`, viene creato automaticamente.

**Corpo della richiesta**:
```json
{
  "username": "string",
  "name": "string",
  "email": "string"
}
```

**Risposta** `200 OK` o `201 Created`.  
**Risposta** `404 Not Found` se l'evento non esiste.

---

#### *(opzionale)* `DELETE /events`

Elimina **tutti** gli eventi.

**Risposta** `200 OK`.

---

#### *(opzionale)* `DELETE /events/{id}`

Elimina l'evento con l'`id` indicato.
Deve eliminare anche tutte le registrazioni associate all'evento (cascade).

**Risposta** `200 OK`.  
**Risposta** `404 Not Found` se l'evento non esiste.

---

### /users

#### `GET /users`

Restituisce la lista di tutti gli utenti esistenti.

**Risposta** `200 OK`:
```json
[
  {
    "username": "string",
    "name": "string",
    "email": "string"
  }
]
```

---

#### `POST /users`

Crea un nuovo utente.

**Corpo della richiesta**:
```json
{
  "username": "string",
  "name": "string",
  "email": "string"
}
```

**Risposta** `200 OK` o `201 Created`.  
**Risposta** `4xx` se esiste già un utente con lo stesso username.

---

#### `GET /users/{username}`

Restituisce l'utente con lo `username` indicato.

**Risposta** `200 OK`:
```json
{
  "username": "string",
  "name": "string",
  "email": "string"
}
```

**Risposta** `404 Not Found` se l'utente non esiste.

---

#### *(opzionale)* `DELETE /users`

Elimina **tutti** gli utenti.

**Risposta** `200 OK`.

---

#### *(opzionale)* `DELETE /users/{username}`

Elimina l'utente con lo `username` indicato.
Deve eliminare anche tutte le registrazioni associate all'utente (cascade).

**Risposta** `200 OK`.  
**Risposta** `404 Not Found` se l'utente non esiste.

---

### /registrations

#### `GET /registrations`

Restituisce la lista di tutte le registrazioni esistenti.

**Risposta** `200 OK`:
```json
[
  {
    "username": "string",
    "event_id": 0
  }
]
```

---

#### *(opzionale)* `DELETE /registrations`

Elimina una singola registrazione, identificata tramite query parameter.

**Query parameter**:

| Parametro | Tipo | Descrizione |
|---|---|---|
| `username` | string | Username dell'utente registrato |
| `event_id` | integer | ID dell'evento |

**Esempio**: `DELETE /registrations?username=alice&event_id=3`

**Risposta** `200 OK`.  
**Risposta** `404 Not Found` se l'evento, l'utente o la registrazione non esistono.

