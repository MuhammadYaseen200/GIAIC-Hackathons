# Tasks: Gmail Watcher -- Phase 2 Bronze Tier

**Input**: Design documents from `/specs/005-gmail-watcher/`
**Prerequisites**: spec.md (complete), plan.md (complete), ADR-0001 through ADR-0004 (accepted)
**Constitution**: TDD mandated (Principle V) -- tests included per story
**Branch**: `005-gmail-watcher`

**Organization**: Tasks are grouped by user story. Due to the watcher architecture dependency chain, US2 (BaseWatcher lifecycle) must be implemented before US1 (GmailWatcher email processing), even though US1 has higher business priority.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, dependency management, directory structure

- [x] T001 Create directory structure: `watchers/`, `tests/unit/`, `tests/integration/`, `scripts/`, `vault/Needs_Action/`, `vault/Inbox/`, `vault/Logs/`
- [x] T002 [P] Create `requirements.txt` with: google-api-python-client>=2.100.0, google-auth-oauthlib>=1.2.0, google-auth-httplib2>=0.2.0, pyyaml>=6.0, python-dotenv>=1.0.0
- [x] T003 [P] Create `requirements-dev.txt` with: -r requirements.txt, pytest>=8.0.0, pytest-asyncio>=0.23.0, pytest-cov>=4.1.0
- [x] T004 [P] Create `watchers/__init__.py` with re-exports of Classification, EmailItem, WatcherState, BaseWatcher, GmailWatcher
- [x] T005 Install dependencies: `pip install -r requirements-dev.txt` (verify all resolve via uv venv)

**Checkpoint**: Project structure ready, dependencies installed

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data models and utilities that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

### Tests (TDD -- write first, verify they fail)

- [x] T006 [P] Write unit tests for enums and EmailItem in `tests/unit/test_models.py`: Classification enum values (ACTIONABLE/INFORMATIONAL), LogSeverity enum values (DEBUG/INFO/WARN/ERROR/CRITICAL), EmailItem frozen dataclass field access, EmailItem immutability check
- [x] T007 [P] Write unit tests for WatcherState in `tests/unit/test_models.py`: to_dict() round-trip, from_dict() with valid data, from_dict() with missing keys (defaults), prune_processed_ids() at boundary (100k), prune_processed_ids() under limit (no-op)
- [x] T008 [P] Write unit tests for WatcherLogEntry in `tests/unit/test_models.py`: to_dict() produces correct keys, severity serializes as string value
- [x] T009 [P] Write unit tests for sanitize_filename in `tests/unit/test_utils.py`: normal text, special characters stripped, max_length truncation, empty input, unicode handling
- [x] T010 [P] Write unit tests for atomic_write in `tests/unit/test_utils.py`: successful write (verify file content), directory creation if missing, content matches after write, concurrent writes don't corrupt
- [x] T011 [P] Write unit tests for sanitize_utf8 in `tests/unit/test_utils.py`: valid UTF-8 passthrough, invalid bytes replaced with U+FFFD, empty string
- [x] T012 [P] Write unit tests for truncate_subject in `tests/unit/test_utils.py`: under limit passthrough, over limit truncates at word boundary, exactly at limit, empty string
- [x] T013 [P] Write unit tests for render_yaml_frontmatter in `tests/unit/test_utils.py`: produces `---` delimiters, fields in order, special characters escaped, empty dict
- [x] T014 [P] Write unit tests for FileLock in `tests/unit/test_utils.py`: acquire/release cycle, double-acquire same process raises, stale lock recovery (PID not running), lock file created with PID content
- [x] T015 [P] Write unit tests for load_env in `tests/unit/test_utils.py`: loads from .env file, raises PrerequisiteError when required keys missing
- [x] T016 Create shared test fixtures in `tests/conftest.py`: tmp_vault(tmp_path) with Needs_Action/Inbox/Logs/, sample_email_item() pre-built EmailItem, sample_raw_gmail_message() raw Gmail API dict, mock_gmail_service() mocked Resource, mock_env(tmp_path) temp .env with credential paths

### Implementation

- [x] T017 [P] Implement Classification and LogSeverity enums in `watchers/models.py` -- Classification(ACTIONABLE, INFORMATIONAL), LogSeverity(DEBUG, INFO, WARN, ERROR, CRITICAL)
- [x] T018 [P] Implement EmailItem frozen dataclass in `watchers/models.py` -- fields: message_id, sender, recipients(list[str]), subject, body, date(ISO8601 str), labels(list[str]), classification(Classification), has_attachments(bool=False), raw_size(int=0)
- [x] T019 Implement WatcherState mutable dataclass in `watchers/models.py` -- fields: last_poll_timestamp, processed_ids(list[str]), error_count, total_emails_processed, uptime_start. Methods: to_dict(), from_dict(classmethod), prune_processed_ids(max_ids=100_000)
- [x] T020 Implement WatcherLogEntry frozen dataclass in `watchers/models.py` -- fields: timestamp, watcher_name, event, severity(LogSeverity), details(dict). Method: to_dict() with severity serialized as .value
- [x] T021 [P] Implement sanitize_filename(text, max_length=60) in `watchers/utils.py` -- lowercase, replace non-alphanumeric with hyphens, collapse multiple hyphens, strip leading/trailing hyphens, truncate to max_length
- [x] T022 [P] Implement atomic_write(filepath, content) in `watchers/utils.py` -- write to temp file in same directory, os.replace() to target path (FR-017), ensure parent dirs exist
- [x] T023 [P] Implement sanitize_utf8(text) in `watchers/utils.py` -- encode to UTF-8 with errors='replace', decode back, replace unmappable chars with U+FFFD
- [x] T024 [P] Implement truncate_subject(subject, max_length=200) in `watchers/utils.py` -- truncate at word boundary, append "..." if truncated, handle empty/None
- [x] T025 [P] Implement render_yaml_frontmatter(fields: dict) in `watchers/utils.py` -- produce string with `---\n`, YAML key-value pairs via pyyaml, closing `---\n`. Ensure safe YAML dumping (no Python object tags)
- [x] T026 Implement PrerequisiteError(Exception) in `watchers/utils.py` -- accepts message and ht_reference (e.g., "HT-001") as fields
- [x] T027 Implement FileLock class in `watchers/utils.py` -- __init__(lock_path), acquire() writes PID to lock file (raises if already locked by live process), release() removes lock file, stale detection via os.kill(pid, 0), context manager support (__enter__/__exit__)
- [x] T028 Implement load_env() in `watchers/utils.py` -- load .env via python-dotenv, validate GMAIL_CREDENTIALS_PATH and GMAIL_TOKEN_PATH exist, raise PrerequisiteError with HT-002 reference if missing
- [x] T029 Run `pytest tests/unit/test_models.py tests/unit/test_utils.py -v` -- 57 tests passed (GREEN)

**Checkpoint**: Foundation ready -- all models, utilities, and their tests passing. User story implementation can begin.

---

## Phase 3: User Story 2 -- Watcher Lifecycle Management (Priority: P2, Impl Order: 1st)

**Goal**: BaseWatcher ABC that defines the standard interface for all watchers with start/stop/poll/process_item lifecycle, retry logic, state persistence, and structured logging.

**Independent Test**: Instantiate a MockWatcher that extends BaseWatcher, call start/stop/poll, verify lifecycle hooks fire correctly. No Gmail credentials required.

**Why implemented first**: US1 (GmailWatcher) extends BaseWatcher. This is the architectural foundation per Constitution Principle VI and ADR-0001.

### Tests (TDD)

- [x] T030 Write MockWatcher subclass in `tests/unit/test_base_watcher.py` -- concrete subclass implementing poll() (returns list of items), process_item() (appends to processed list), validate_prerequisites() (passes). Used by all base watcher tests.
- [x] T031 Write test_start_validates_prerequisites in `tests/unit/test_base_watcher.py` -- Given MockWatcher, When start() called, Then validate_prerequisites() is called before poll loop begins
- [x] T032 Write test_start_loads_state in `tests/unit/test_base_watcher.py` -- Given saved state file exists, When start() called, Then state is loaded from JSON file
- [x] T033 Write test_stop_saves_state_and_releases_lock in `tests/unit/test_base_watcher.py` -- Given running watcher, When stop() called, Then state JSON is written and lock file removed
- [x] T034 Write test_poll_cycle_calls_poll_and_process in `tests/unit/test_base_watcher.py` -- Given MockWatcher with items, When _run_poll_cycle() executes, Then poll() called once and process_item() called per item
- [x] T035 Write test_retry_with_backoff in `tests/unit/test_base_watcher.py` -- Given a coro_factory that fails twice then succeeds, When _retry_with_backoff() called with max_retries=3, Then succeeds on 3rd attempt with delays (2s, 4s)
- [x] T036 Write test_retry_exhausted_raises in `tests/unit/test_base_watcher.py` -- Given a coro_factory that always fails, When _retry_with_backoff() called with max_retries=3, Then raises after 3 attempts
- [x] T037 Write test_state_corrupt_recovery in `tests/unit/test_base_watcher.py` -- Given corrupt JSON in state file, When _load_state() called, Then logs warning, resets to clean WatcherState, continues
- [x] T038 Write test_log_writes_jsonl in `tests/unit/test_base_watcher.py` -- Given watcher, When _log() called, Then JSONL line appended to vault/Logs/gmail_watcher_YYYY-MM-DD.log
- [x] T039 Write test_poll_interval_validation in `tests/unit/test_base_watcher.py` -- Given poll_interval=10, When __init__() called, Then raises ValueError (minimum 30s)
- [x] T040 Write test_health_check_returns_status in `tests/unit/test_base_watcher.py` -- Given running watcher, When health_check() called, Then returns dict with name, status, last_poll, error_count

### Implementation

- [x] T041 Implement BaseWatcher.__init__(name, poll_interval=60, vault_path="vault") in `watchers/base_watcher.py` -- validate poll_interval >= 30, initialize WatcherState, set _running=False, configure log/state/lock paths
- [x] T042 Implement BaseWatcher.start() as async method in `watchers/base_watcher.py` -- call validate_prerequisites(), _load_state(), _acquire_lock(), set uptime_start, register SIGINT/SIGTERM handlers via loop.add_signal_handler(), enter while _running loop calling _run_poll_cycle() + asyncio.sleep(poll_interval)
- [x] T043 Implement BaseWatcher.stop() as async method in `watchers/base_watcher.py` -- set _running=False, _save_state(), _release_lock(), _log("stopped", INFO)
- [x] T044 Implement BaseWatcher._run_poll_cycle() in `watchers/base_watcher.py` -- call poll() via _retry_with_backoff(), iterate results calling process_item() for each, update state (last_poll_timestamp, total_emails_processed), _save_state(), _log cycle summary
- [x] T045 Implement BaseWatcher._retry_with_backoff(coro_factory, max_retries=3, base_delay=2.0) in `watchers/base_watcher.py` -- exponential backoff (2s, 4s, 8s), log each retry attempt, re-raise after max_retries exhausted
- [x] T046 Implement BaseWatcher._load_state()/_save_state() in `watchers/base_watcher.py` -- JSON round-trip to vault/Logs/{name}_state.json via atomic_write. On corrupt JSON: log warning, reset to clean WatcherState (accept brief re-processing)
- [x] T047 Implement BaseWatcher._log(event, severity, details) in `watchers/base_watcher.py` -- create WatcherLogEntry, append to_dict() as JSON line to vault/Logs/{name}_YYYY-MM-DD.log
- [x] T048 Implement BaseWatcher._acquire_lock()/_release_lock() in `watchers/base_watcher.py` -- wrap FileLock for vault/Logs/.{name}.lock
- [x] T049 Implement BaseWatcher.health_check() in `watchers/base_watcher.py` -- return dict with name, status (ok/error), last_poll, error_count, uptime_start, total_processed
- [x] T050 Declare abstract methods in `watchers/base_watcher.py` -- @abstractmethod: poll() -> list, process_item(item) -> None, validate_prerequisites() -> None
- [x] T051 Run `pytest tests/unit/test_base_watcher.py -v` -- verify all lifecycle tests pass (GREEN)

**Checkpoint**: BaseWatcher ABC fully functional. Any watcher subclass can inherit lifecycle, retry, state, logging, locking.

---

## Phase 4: User Story 3 -- OAuth2 Authentication Flow (Priority: P3, Impl Order: 2nd)

**Goal**: Gmail OAuth2 authentication that guides first-time setup, stores tokens securely, and refreshes automatically.

**Independent Test**: Run `python scripts/gmail_auth.py`, complete browser consent, verify `token.json` is created and API call succeeds.

**Why implemented before US1**: GmailWatcher needs authentication before it can fetch emails.

### Tests (TDD)

- [x] T052 Write test_authenticate_new_token in `tests/unit/test_gmail_watcher.py` -- Given credentials.json exists but no token.json, When _authenticate() called, Then InstalledAppFlow.from_client_secrets_file is invoked, token saved atomically
- [x] T053 Write test_authenticate_existing_valid_token in `tests/unit/test_gmail_watcher.py` -- Given valid token.json exists, When _authenticate() called, Then no browser flow, credentials loaded from file
- [x] T054 Write test_authenticate_expired_token_refreshes in `tests/unit/test_gmail_watcher.py` -- Given token.json with expired but refreshable token, When _authenticate() called, Then creds.refresh() called, updated token saved
- [x] T055 Write test_authenticate_corrupt_token_deletes_and_reauths in `tests/unit/test_gmail_watcher.py` -- Given corrupt token.json, When _authenticate() called, Then corrupt file deleted, browser flow triggered
- [x] T056 Write test_validate_prerequisites_missing_credentials in `tests/unit/test_gmail_watcher.py` -- Given no credentials.json, When validate_prerequisites() called, Then raises PrerequisiteError with HT-002 reference
- [x] T057 Write test_validate_prerequisites_missing_vault_dirs in `tests/unit/test_gmail_watcher.py` -- Given no vault/Needs_Action/, When validate_prerequisites() called, Then raises PrerequisiteError with HT-001 reference
- [x] T058 Write test_validate_prerequisites_missing_env_vars in `tests/unit/test_gmail_watcher.py` -- Given .env without GMAIL_CREDENTIALS_PATH, When validate_prerequisites() called, Then raises PrerequisiteError

### Implementation

- [x] T059 Implement GmailWatcher.__init__(poll_interval=60, vault_path="vault", credentials_path=None, token_path=None) in `watchers/gmail_watcher.py` -- call super().__init__("gmail_watcher", poll_interval, vault_path), read credentials_path/token_path from .env if not provided
- [x] T060 Implement GmailWatcher.validate_prerequisites() in `watchers/gmail_watcher.py` -- check vault dirs exist (HT-001), credentials.json exists (HT-002), .env has required keys. Raise PrerequisiteError with specific HT-xxx reference on failure.
- [x] T061 Implement GmailWatcher._authenticate() in `watchers/gmail_watcher.py` -- load token.json if exists, check creds.valid, refresh if expired, run InstalledAppFlow if no token, save token atomically via atomic_write(). All three scopes: gmail.readonly, gmail.send, gmail.modify (future-proofing per plan).
- [x] T062 Implement `scripts/gmail_auth.py` -- standalone OAuth2 helper: requests all 3 scopes, opens browser, saves token.json, verifies with getProfile(), prints success/failure message with user's email address
- [x] T063 Run `pytest tests/unit/test_gmail_watcher.py -k "authenticate or prerequisite" -v` -- verify auth and prereq tests pass (GREEN)

**Checkpoint**: OAuth2 flow works end-to-end. Token persists across restarts. Prerequisites validate correctly.

---

## Phase 5: User Story 1 -- Email to Action Item (Priority: P1, Impl Order: 3rd) MVP

**Goal**: GmailWatcher reads unread inbox emails, classifies them as actionable/informational via keyword heuristics, and writes structured markdown files to the correct vault directory.

**Independent Test**: Send a test email, run watcher, verify markdown file appears in `vault/Needs_Action/` within 90 seconds with correct YAML frontmatter.

**Why this is MVP**: This is the core value proposition -- email-to-vault conversion. All downstream phases (Ralph Wiggum, HITL, MCP) depend on this output.

### Tests (TDD)

- [x] T064 Write test_parse_email_full_message in `tests/unit/test_gmail_watcher.py` -- Given raw Gmail API message dict with headers/body/attachments, When _parse_email() called, Then returns correct sender, recipients, subject, body (HTML stripped), date, has_attachments
- [x] T065 Write test_parse_email_no_body in `tests/unit/test_gmail_watcher.py` -- Given message with subject only (no body parts), When _parse_email() called, Then body is "No email body content."
- [x] T066 Write test_parse_email_non_utf8 in `tests/unit/test_gmail_watcher.py` -- Given message with non-UTF8 characters, When _parse_email() called, Then body is sanitized via sanitize_utf8()
- [x] T067 Write test_classify_actionable in `tests/unit/test_gmail_watcher.py` -- Given email with subject "Urgent: Please review contract", When _classify_email() called, Then returns Classification.ACTIONABLE
- [x] T068 Write test_classify_informational in `tests/unit/test_gmail_watcher.py` -- Given email from noreply@ with subject "Weekly Newsletter", When _classify_email() called, Then returns Classification.INFORMATIONAL
- [x] T069 Write test_classify_default_actionable in `tests/unit/test_gmail_watcher.py` -- Given ambiguous email with no strong signals, When _classify_email() called, Then returns Classification.ACTIONABLE (default-to-actionable policy per ADR-0004)
- [x] T070 Write test_generate_filename_normal in `tests/unit/test_gmail_watcher.py` -- Given email with date and subject, When _generate_filename() called, Then returns "YYYY-MM-DD-HHmm-sanitized-subject.md"
- [x] T071 Write test_generate_filename_collision in `tests/unit/test_gmail_watcher.py` -- Given target file already exists, When _generate_filename() called, Then returns filename with "-001" suffix
- [x] T072 Write test_render_markdown in `tests/unit/test_gmail_watcher.py` -- Given EmailItem, When _render_markdown() called, Then output has YAML frontmatter with all required fields (type, status:pending, source:gmail, message_id, from, subject, date_received, date_processed, classification, priority:standard, has_attachments, watcher) followed by body
- [x] T073 Write test_process_item_actionable_routes_to_needs_action in `tests/unit/test_gmail_watcher.py` -- Given ACTIONABLE EmailItem, When process_item() called, Then file written to vault/Needs_Action/
- [x] T074 Write test_process_item_informational_routes_to_inbox in `tests/unit/test_gmail_watcher.py` -- Given INFORMATIONAL EmailItem, When process_item() called, Then file written to vault/Inbox/
- [x] T075 Write test_poll_filters_already_processed in `tests/unit/test_gmail_watcher.py` -- Given email ID already in state.processed_ids, When poll() called, Then email is skipped (zero duplicate files)
- [x] T076 Write test_fetch_unread_emails_wraps_in_thread in `tests/unit/test_gmail_watcher.py` -- Given mocked Gmail service, When _fetch_unread_emails() called, Then asyncio.to_thread() is used for the sync SDK call (ADR-0002)

### Implementation

- [x] T077 Define ACTIONABLE_KEYWORDS and INFORMATIONAL_KEYWORDS score dictionaries and INFORMATIONAL_SENDER_PATTERNS regex list at module level in `watchers/gmail_watcher.py` -- per ADR-0004 (e.g., "urgent":3, "action required":5, "deadline":3, "please review":4, "approve":4, "meeting":2, "invoice":3 for actionable; "newsletter":5, "unsubscribe":4, "no-reply":3, "digest":3, "automated":3, "notification":2 for informational)
- [x] T078 Implement GmailWatcher._classify_email(email: EmailItem) in `watchers/gmail_watcher.py` -- score sender+subject+body[:500] against both dictionaries (case-insensitive), check sender against INFORMATIONAL_SENDER_PATTERNS. If informational_score > actionable_score + threshold(2), return INFORMATIONAL, else ACTIONABLE.
- [x] T079 Implement GmailWatcher._parse_email(raw: dict) in `watchers/gmail_watcher.py` -- extract From, To, Subject, Date from headers; decode body from payload parts (prefer text/plain, fallback text/html with tag stripping); detect attachments from parts with filename; sanitize_utf8 on all text fields; handle missing body gracefully
- [x] T080 Implement GmailWatcher._fetch_unread_emails() in `watchers/gmail_watcher.py` -- wrap in asyncio.to_thread(): call messages.list(userId="me", q="is:unread in:inbox", maxResults=50), then messages.get(userId="me", id=msg_id, format="full") per result. Return list of raw message dicts.
- [x] T081 Implement GmailWatcher.poll() in `watchers/gmail_watcher.py` -- call _fetch_unread_emails(), filter out IDs in state.processed_ids, _parse_email() each, _classify_email() each, return list of EmailItem
- [x] T082 Implement GmailWatcher._generate_filename(email: EmailItem) in `watchers/gmail_watcher.py` -- format date as YYYY-MM-DD-HHmm, sanitize_filename(subject, max_length=60), combine. If file exists at target path, append "-001", "-002" etc.
- [x] T083 Implement GmailWatcher._render_markdown(email: EmailItem) in `watchers/gmail_watcher.py` -- render_yaml_frontmatter() with fields: type:email, status:pending, source:gmail, message_id, from, subject(truncated to 200), date_received, date_processed(now ISO), classification, priority:standard, has_attachments, watcher:gmail_watcher. Then newline + email.body
- [x] T084 Implement GmailWatcher._get_vault_target_dir(classification) in `watchers/gmail_watcher.py` -- ACTIONABLE -> vault_path/Needs_Action/, INFORMATIONAL -> vault_path/Inbox/
- [x] T085 Implement GmailWatcher.process_item(email: EmailItem) in `watchers/gmail_watcher.py` -- generate filename, render markdown, atomic_write to target dir, add email.message_id to state.processed_ids, _log the processing event
- [x] T086 Add `__main__` block to `watchers/gmail_watcher.py` -- parse optional CLI args (--poll-interval, --vault-path), instantiate GmailWatcher, asyncio.run(watcher.start())
- [x] T087 Run `pytest tests/unit/test_gmail_watcher.py -v` -- verify all Gmail watcher tests pass (GREEN)

**Checkpoint**: Full email-to-vault pipeline works. Emails classified, routed to correct directories, duplicates prevented. This is the MVP.

---

## Phase 6: User Story 4 -- Vault File Routing and Ralph Wiggum Compatibility (Priority: P4)

**Goal**: Verify watcher output files follow vault routing conventions and YAML frontmatter is compatible with the Phase 3 reasoning loop state machine.

**Independent Test**: Create a sample watcher output file and verify it passes validation against the LOOP.md state machine schema.

**Note**: Most implementation is embedded in US1 (T083, T084). This phase adds explicit verification.

- [x] T088 [US4] Write test_frontmatter_ralph_wiggum_compatible in `tests/unit/test_gmail_watcher.py` -- Given rendered markdown, When parsed as YAML, Then contains all required fields: type(email), status(pending), source(gmail), message_id, from, subject, date_received, date_processed, classification, priority, has_attachments, watcher
- [x] T089 [US4] Write test_filename_pattern_compliance in `tests/unit/test_gmail_watcher.py` -- Given generated filename, When matched against regex `^\d{4}-\d{2}-\d{2}-\d{4}-[a-z0-9-]+\.md$`, Then matches (YYYY-MM-DD-HHmm-sanitized.md)
- [x] T090 [US4] Write test_vault_directory_compliance in `tests/unit/test_gmail_watcher.py` -- Given ACTIONABLE email processed, When file written, Then path starts with vault/Needs_Action/. Given INFORMATIONAL, Then path starts with vault/Inbox/
- [x] T091 [US4] Run `pytest tests/unit/test_gmail_watcher.py -k "ralph_wiggum or filename_pattern or directory_compliance" -v` -- verify routing compliance (GREEN)

**Checkpoint**: Output format verified compatible with Phase 3 Ralph Wiggum loop.

---

## Phase 7: User Story 5 -- Observability and Health Reporting (Priority: P5)

**Goal**: Structured JSONL logging to vault/Logs/ for Obsidian Dataview dashboard integration.

**Independent Test**: Start watcher, let it run through 5 poll cycles, verify structured log entries in vault/Logs/.

**Note**: Core logging is embedded in US2 (T047). This phase verifies Dataview compatibility and completeness.

- [x] T092 [US5] Write test_log_entry_dataview_parseable in `tests/unit/test_base_watcher.py` -- Given log entry written, When parsed as JSON, Then contains: timestamp (ISO8601), watcher_name, event, severity, details dict -- all Dataview-queryable fields
- [x] T093 [US5] Write test_log_started_event in `tests/unit/test_base_watcher.py` -- Given watcher starts, When first log written, Then event="started", severity="info", details includes status="ok"
- [x] T094 [US5] Write test_log_poll_cycle_summary in `tests/unit/test_base_watcher.py` -- Given poll cycle completes, When log written, Then details includes: emails_found, emails_processed, errors, next_poll_time
- [x] T095 [US5] Write test_log_error_includes_severity_and_type in `tests/unit/test_base_watcher.py` -- Given error occurs, When logged, Then severity is "error" or "critical", details includes error_type and error_message
- [x] T096 [US5] Run `pytest tests/unit/test_base_watcher.py -k "log_entry or log_started or log_poll or log_error" -v` -- verify observability tests pass (GREEN)

**Checkpoint**: All log output is structured JSON, parseable by Obsidian Dataview for Dashboard.md.

---

## Phase 8: Integration & Polish

**Purpose**: Full-cycle integration tests, cross-story validation, edge cases

### Integration Tests

- [x] T097 [P] Write test_full_email_cycle in `tests/integration/test_gmail_integration.py` -- Mock Gmail returns 3 emails (2 actionable, 1 informational), run full poll+process cycle, verify 2 files in Needs_Action/, 1 in Inbox/, all with correct frontmatter
- [x] T098 [P] Write test_duplicate_prevention_across_cycles in `tests/integration/test_gmail_integration.py` -- Mock Gmail returns same 3 emails across 5 poll cycles, verify exactly 3 files created (zero duplicates)
- [x] T099 [P] Write test_state_persistence_across_restart in `tests/integration/test_gmail_integration.py` -- Process emails, save state, create new watcher instance, load state, poll again with same emails, verify no new files created
- [x] T100 [P] Write test_classification_routing_accuracy in `tests/integration/test_gmail_integration.py` -- 10 test emails (5 clearly actionable, 5 clearly informational), verify correct routing for all 10
- [x] T101 Write test_error_recovery_mid_cycle in `tests/integration/test_gmail_integration.py` -- Mock Gmail fails on 2nd email of 5, verify 1st email processed, 3rd-5th not attempted, error logged, next cycle retries
- [x] T102 Write test_concurrent_lock_prevention in `tests/integration/test_gmail_integration.py` -- Start watcher (acquires lock), attempt second instance, verify second raises error about existing lock

### Polish

- [x] T103 Update `watchers/__init__.py` re-exports to match final public API
- [x] T104 Run full test suite: `pytest tests/ -v --cov=watchers --cov-report=term-missing` -- verify >80% coverage (Constitution V target)
- [x] T105 Verify `.gitignore` includes credentials.json, token.json, *.pyc, __pycache__/, .venv/ (already confirmed in setup)

**Checkpoint**: All tests pass, >80% coverage, no security leaks, integration verified.

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup) ─────────────────────────► Phase 2 (Foundational)
                                                    │
                                                    ▼
                                           Phase 3 (US2: BaseWatcher)
                                                    │
                                          ┌─────────┴──────────┐
                                          ▼                    ▼
                                Phase 4 (US3: OAuth2)   Phase 7 (US5: Observability)
                                          │
                                          ▼
                                Phase 5 (US1: Email→Vault) ◄── MVP
                                          │
                                          ▼
                                Phase 6 (US4: Routing Compliance)
                                          │
                                          ▼
                                Phase 8 (Integration & Polish)
```

### User Story Dependencies

- **US2 (BaseWatcher)**: Foundational -- depends only on Phase 2 models/utils. MUST complete first.
- **US3 (OAuth2)**: Depends on US2 (GmailWatcher inherits BaseWatcher). Can run in parallel with US5.
- **US1 (Email→Vault)**: Depends on US2 + US3. This is the MVP delivery point.
- **US4 (Routing)**: Verification of US1 output. Depends on US1 completion.
- **US5 (Observability)**: Verification of US2 logging. Can run in parallel with US3/US4.

### Within Each User Story

1. Tests MUST be written first and verified to FAIL (RED)
2. Implementation proceeds (GREEN)
3. Run tests to verify pass
4. Checkpoint before moving to next story

### Parallel Opportunities

Within Phase 2:
- T006-T015 (all foundational tests) can run in parallel
- T017-T018, T021-T025 (independent models/utils) can run in parallel

Within Phase 5:
- T064-T076 (all US1 tests) can run in parallel
- T077-T078 (keywords + classify) can run in parallel with T079 (parse)

Across Stories:
- US3 (OAuth2) and US5 (Observability) can run in parallel after US2 completes

---

## Implementation Strategy

### MVP First (Stop After Phase 5)

1. Complete Phase 1: Setup (~5 min)
2. Complete Phase 2: Foundational models + utils (~20 min)
3. Complete Phase 3: BaseWatcher lifecycle (~25 min)
4. Complete Phase 4: OAuth2 auth flow (~15 min)
5. Complete Phase 5: Email→Vault pipeline (~30 min)
6. **STOP AND VALIDATE**: Send test email, verify markdown in vault/Needs_Action/

### Full Delivery (All Phases)

7. Phase 6: Verify Ralph Wiggum compatibility (~10 min)
8. Phase 7: Verify observability/logging (~10 min)
9. Phase 8: Integration tests + polish (~20 min)
10. Final: `pytest tests/ -v --cov=watchers` -- all pass, >80% coverage

### Session Strategy (82% context used)

Given context constraints, recommended approach:
1. This session: Generate tasks.md (this file) + start Phase 1-2 implementation
2. Next session: Resume from Phase 3 onwards using this tasks.md as the guide

---

## Summary

| Metric | Value |
|--------|-------|
| Total tasks | 105 |
| Phase 1 (Setup) | 5 tasks |
| Phase 2 (Foundational) | 24 tasks |
| Phase 3 (US2: BaseWatcher) | 22 tasks |
| Phase 4 (US3: OAuth2) | 12 tasks |
| Phase 5 (US1: Email→Vault) | 24 tasks |
| Phase 6 (US4: Routing) | 4 tasks |
| Phase 7 (US5: Observability) | 5 tasks |
| Phase 8 (Integration) | 9 tasks |
| Parallel opportunities | 40+ tasks marked [P] |
| MVP scope | Phases 1-5 (87 tasks) |
| Files to create | 13 |
| Target coverage | >80% |

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Constitution V mandates TDD: write tests first, verify RED, then implement GREEN
- ADR-0001 through ADR-0004 inform specific implementation choices
- Commit after each phase checkpoint
- Stop at any checkpoint to validate story independently
