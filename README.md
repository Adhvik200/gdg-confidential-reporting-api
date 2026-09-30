# GDG SRMIST KTR — Confidential Reporting System

A backend REST API for submitting and tracking confidential reports anonymously. This project was developed as a recruitment-task implementation for the **Google Developer Groups (GDG) SRMIST KTR**.

A reporter can submit a report without creating an account or providing identifying information. The system returns a cryptographically random case code that can be used to check the report status later.

## Features

- Anonymous report submission without an account
- Categories: Security, Harassment, Corruption, Technical, and Other
- Optional evidence or reference URL
- Cryptographically secure random case codes
- SHA-256 hashing of case codes before database storage
- Anonymous case tracking
- Moderator authentication using JWT
- Protected moderator endpoints for viewing and managing reports
- Report listing, filtering, and status/update history
- Controlled status workflow and input validation
- Swagger/OpenAPI documentation
- Automated tests
- SQLite development database and PostgreSQL-compatible configuration
- Gunicorn and Render deployment support

## Architecture

The application uses Python, Flask, SQLAlchemy, Flask-Migrate, Flask-JWT-Extended, Flasgger/Swagger, SQLite or PostgreSQL, Pytest, and Gunicorn. Flask provides the REST API, SQLAlchemy handles persistence, JWT protects moderator routes, and the database stores reports, hashed case codes, and status history.

## Privacy model

The API does not ask for or store the reporter's name, email address, account ID, phone number, or other reporter identity fields. Reports contain their content, category, status, timestamps, optional reference URL, and a SHA-256 hash of the case code.

### Case-code security

A case code is generated with Python's `secrets` module and is not derived from the database primary key. The original code is returned only in the submission response; only its SHA-256 hash is stored. The reporter must save the code securely because it is needed for anonymous tracking. Anyone who obtains the code may be able to view that report's status, so it should be treated as a secret.

### Moderator privacy

Moderator access is authenticated with JWT. Moderator credentials and tokens are for staff access and are not linked to reporter identity. Keep moderator credentials and signing secrets out of source control, restrict moderator access, and use HTTPS in deployment.

### Infrastructure privacy limitation

The application itself does not store reporter IP addresses. Hosting providers, reverse proxies, load balancers, web servers, analytics systems, and firewalls may independently retain network logs. Review and configure infrastructure logging, access, and retention policies before handling real confidential reports.

## Status workflow

```text
SUBMITTED -> UNDER_REVIEW -> RESOLVED
                         \\-> DISMISSED
```

Invalid transitions are rejected. A report must first move from `SUBMITTED` to `UNDER_REVIEW`; it can then be marked `RESOLVED` or `DISMISSED`.

## Project structure

A typical project layout is:

```text
.
├── app/                    # Flask application, routes, models, and services
├── migrations/             # Database migration files, if enabled
├── tests/                  # Automated tests
├── .env.example            # Example environment configuration (safe to commit)
├── .gitignore              # Excludes secrets, local databases, and environments
├── config.py               # Application configuration
├── requirements.txt        # Python dependencies
├── run.py                  # Local application entry point
└── README.md
```

Names may vary slightly depending on the implementation; use the files in the repository as the source of truth.

## Setup

### 1. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Windows Command Prompt:

```bat
python -m venv .venv
.venv\Scripts\activate
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 3. Configure environment variables

Copy `.env.example` to `.env`, then replace the placeholder secrets with long, unique random values. Never commit `.env` or production secrets.

Example `.env.example`:

```env
SECRET_KEY=replace-with-a-long-random-secret
JWT_SECRET_KEY=replace-with-a-long-random-jwt-secret
DATABASE_URL=sqlite:///app.db
FLASK_DEBUG=0
```

For PostgreSQL, set `DATABASE_URL` to the provider's connection URL and ensure the database driver listed in `requirements.txt` is installed. Do not place production credentials in `.env.example`.

### 4. Initialize the database

Initialize or create the schema using the repository's configured database command. For a Flask-Migrate setup, a typical first-time sequence is:

```bash
flask db upgrade
```

If the project instead creates tables when the application starts, run the initialization command documented by its entry point. Back up persistent production data before applying schema changes.

### 5. Create a moderator

Use the project's moderator-creation CLI or setup procedure. Set a strong, unique password and keep it private. Do not commit credentials or create a default production moderator with a known password. If the repository provides no CLI, create the moderator through its documented model/bootstrap process before using protected endpoints.

### 6. Run the application

Use the project entry point, for example:

```bash
python run.py
```

The local server is commonly available at `http://127.0.0.1:5000`. Confirm the actual host and port from the startup output or configuration. Do not expose Flask's development server or debug mode in production.

## API reference

The examples below use `http://127.0.0.1:5000` as the base URL. The seven endpoint paths shown are a conventional reference; align them with the route definitions in the application if their names differ. JSON field names shown are illustrative and should match the implementation's schemas.

### Public endpoints

#### 1. Submit a report

`POST /api/reports`

No account or authentication is required.

Request:

```json
{
  "category": "Security",
  "description": "Please review the issue described here.",
  "evidence_url": "https://example.org/reference"
}
```

`evidence_url` is optional. On success, the response includes the newly generated case code. Save it securely.

Example response:

```json
{
  "message": "Report submitted successfully",
  "case_code": "CASE-REPLACE-WITH-ISSUED-CODE",
  "status": "SUBMITTED"
}
```

#### 2. Track a report anonymously

`POST /api/reports/track`

Request:

```json
{
  "case_code": "CASE-REPLACE-WITH-ISSUED-CODE"
}
```

Example response:

```json
{
  "status": "UNDER_REVIEW",
  "created_at": "2026-01-01T12:00:00Z",
  "updated_at": "2026-01-02T09:30:00Z"
}
```

The public tracking response should expose only information intended for the reporter; it should not disclose moderator-only notes or other reports.

### Moderator endpoints

Moderator routes require a valid JWT in the `Authorization` header: `Bearer <access_token>`.

#### 3. Moderator login

`POST /api/moderator/login`

Request:

```json
{
  "username": "moderator",
  "password": "your-moderator-password"
}
```

Example response:

```json
{
  "access_token": "<jwt-access-token>"
}
```

#### 4. List and filter reports

`GET /api/moderator/reports`

Optional query filters may include `status` and `category`, depending on the implementation. Example:

```http
GET /api/moderator/reports?status=SUBMITTED&category=Security
Authorization: Bearer <jwt-access-token>
```

#### 5. Get a report

`GET /api/moderator/reports/<report_id>`

```http
GET /api/moderator/reports/1
Authorization: Bearer <jwt-access-token>
```

The moderator view may include report details and status history. It must not reveal the original case code, which is not stored in the database.

#### 6. Update report status

`PATCH /api/moderator/reports/<report_id>/status`

Request:

```json
{
  "status": "UNDER_REVIEW",
  "note": "Initial review started."
}
```

Use only permitted transitions. A subsequent update can set status to `RESOLVED` or `DISMISSED`.

#### 7. Add a status update

`POST /api/moderator/reports/<report_id>/updates`

Request:

```json
{
  "message": "The team is reviewing the submitted reference."
}
```

This creates an entry in the report's update history. If the implementation combines status changes and history entries, use its documented status endpoint instead.

## HTTP status codes

Responses use standard HTTP status codes, with a JSON error message where appropriate:

- `200 OK` — successful read, login, tracking, or update
- `201 Created` — report or history entry created
- `400 Bad Request` — malformed JSON, missing required fields, or invalid values
- `401 Unauthorized` — missing or invalid moderator authentication, or invalid tracking credentials
- `404 Not Found` — report or case code does not exist
- `409 Conflict` — invalid status transition or conflicting operation, if implemented
- `422 Unprocessable Entity` — structurally valid request that fails field validation, if used by the application
- `500 Internal Server Error` — unexpected server error; responses should not expose secrets or stack traces

The exact status for each validation failure depends on the application's handlers.

## Validation

Requests should be checked for valid JSON, required fields, supported categories (`Security`, `Harassment`, `Corruption`, `Technical`, `Other`), non-empty report text, valid optional URLs, allowed status values, and permitted status transitions. Invalid input should receive a clear client error and should not create a partial report. Avoid returning sensitive internal details in error responses.

## Security and design decisions

- **Anonymous submission:** reporter accounts and identity fields are not part of the reporting flow.
- **Random case codes:** generated with a cryptographically secure random source and independent of database IDs.
- **Hash at rest:** store a one-way SHA-256 hash for case-code lookup rather than the usable secret itself.
- **JWT-protected moderation:** protect moderator-only list, detail, and management operations.
- **Controlled workflow:** allow only documented status transitions and record updates.
- **Configuration through environment:** keep signing keys and database credentials out of source control.
- **HTTPS in deployment:** protect credentials, JWTs, and report content in transit.
- **Least disclosure:** return only the data needed by the public tracking flow.

A plain SHA-256 digest is appropriate here only because case codes are generated with high entropy and are not human-chosen passwords. Passwords must use a dedicated password-hashing method such as Werkzeug's password hashing helpers, not plain SHA-256.

## Threat-model limitations

This recruitment implementation is not a certified whistleblowing platform. The case code is a bearer secret: anyone who obtains it may track the corresponding report. A compromised moderator account, application host, database, deployment secret, or infrastructure log can expose sensitive information. SHA-256 hashing protects the original case code from direct database disclosure but does not protect report contents. The project does not by itself provide end-to-end encryption, independent security audits, tamper-evident storage, formal incident response, or guaranteed anonymity against network-level observation.

## Testing

Run the automated test suite from the project root:

```bash
python -m pytest
```

The project test run recorded for this recruitment implementation reported **4 passing tests**. Re-run the command in the current environment to confirm the result after any changes; the count can change as tests are added or modified.

## Swagger / OpenAPI

The API includes Swagger/OpenAPI documentation through Flasgger. Start the application and open its configured Swagger UI route, commonly `/apidocs/` (for example, `http://127.0.0.1:5000/apidocs/`). The exact path is set by the application configuration. Swagger can be used to inspect schemas and try requests; moderator operations still require a valid JWT.

## cURL examples

Submit a report:

```bash
curl -X POST http://127.0.0.1:5000/api/reports \\
  -H "Content-Type: application/json" \\
  -d '{"category":"Technical","description":"Example report text","evidence_url":"https://example.org/reference"}'
```

Track a report:

```bash
curl -X POST http://127.0.0.1:5000/api/reports/track \\
  -H "Content-Type: application/json" \\
  -d '{"case_code":"CASE-REPLACE-WITH-ISSUED-CODE"}'
```

Log in, then use the returned token for moderator requests:

```bash
curl -X POST http://127.0.0.1:5000/api/moderator/login \\
  -H "Content-Type: application/json" \\
  -d '{"username":"moderator","password":"your-moderator-password"}'
```

```bash
curl http://127.0.0.1:5000/api/moderator/reports \\
  -H "Authorization: Bearer <jwt-access-token>"
```

## Suggested demo flow

1. Start the app and open the Swagger UI.
2. Submit a report without providing reporter identity information.
3. Save the returned case code, then use it to track the report.
4. Log in as a moderator and copy the access token.
5. List reports, inspect the new report, and move it to `UNDER_REVIEW`.
6. Add a status update, then demonstrate a valid terminal transition to `RESOLVED` or `DISMISSED`.
7. Try an invalid transition and show that the API rejects it.
8. Run `python -m pytest` to show the automated checks.

Use synthetic demo content rather than real sensitive reports.

## Deployment on Render

A typical Render deployment uses a Python web service and a PostgreSQL database:

1. Push the application to a Git repository with secrets excluded.
2. Create a PostgreSQL database and a Python web service in Render.
3. Set the service's build command to `pip install -r requirements.txt`.
4. Set its start command to `gunicorn run:app` if `run.py` exports the Flask object as `app`; adjust the module and object name to match the repository.
5. Configure `DATABASE_URL`, `SECRET_KEY`, `JWT_SECRET_KEY`, and any other required values as Render environment variables.
6. Run the database migration/initialization command as required by the project.
7. Create moderator credentials securely and verify the health, submission, tracking, and protected moderator flows.
8. Review HTTPS, access controls, backups, logging, and retention settings before using any sensitive data.

Render configuration and free-tier behavior can change. Confirm current service settings in the Render dashboard. Never use Flask debug mode for a public deployment.

## Git safety

Commit `.env.example`, source code, migrations, and tests. Do not commit `.env`, production credentials, JWT signing keys, moderator passwords, local database files containing reports, virtual environments, or generated secrets. Confirm `.gitignore` excludes these files before pushing. If a secret is accidentally committed, rotate it; deleting the file in a later commit does not invalidate the exposed secret.

## Limitations

- Case-code loss prevents a reporter from tracking their report.
- Case-code possession grants access to the public tracking response.
- Infrastructure may retain network logs outside the application's control.
- Moderator access depends on credential security and deployment configuration.
- Database and report-content confidentiality depend on host and storage security.
- The project does not claim regulatory compliance or independently verified anonymity.
- Route names, schema fields, migration commands, and deployment entry points must match the actual repository implementation.

## Recruitment-task scope

This project demonstrates a backend design for anonymous report submission, case-code tracking, moderator authentication, status management, validation, API documentation, testing, and deployment configuration. It is a recruitment-task implementation and should be evaluated against its code and tests; the README does not substitute for a security review.

## Disclaimer

This software is provided for educational and recruitment-task purposes. Do not use it to submit real confidential, emergency, or legally sensitive information without a thorough security, privacy, operational, and legal review. A real confidential or whistleblowing reporting system would require independent security assessment, carefully governed access, secure deployment and retention controls, tested incident response, and appropriate organizational and legal safeguards.

