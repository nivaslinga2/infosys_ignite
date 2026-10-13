# AgentShield: OWASP Top 10 for LLM Applications (2025) Risk Register

| OWASP Risk ID | Vulnerability Title | Risk Description in Autonomous Agents | AgentShield Mitigation / Implementation | Defense Tier | Status |
| :--- | :--- | :--- | :--- | :---: | :---: |
| **LLM01:2025** | **Prompt Injection & Adversarial Evasion** | Malicious instructions inserted via user input or retrieved web context hijacking agent intent. Character manipulation, zero-width spaces, homoglyphs, and obfuscated text evading prompt detectors (Hackett et al., arXiv:2504.09559). | **Text Normalizer, Provenance & Independent Auth** (`normalize.py`, `provenance.py`, `jailbreak.py`, `interceptor.py`): Canonical NFKC normalization, detection of invisible/control characters (`Cf`, `Cc`, `Cs`), mixed-script homoglyph detection, and architectural rule that *detector `SAFE` never authorizes tool execution*. | P0 | **MITIGATED** |
| **LLM02:2025** | **Sensitive Information Disclosure** | Exposure of PII, secrets, credentials, or proprietary databases in agent prompts or outputs. | **PII Masking & Vault Engine** (`pii.py`): Automatic detection of SSN, Aadhaar, Credit Cards, Emails, API Keys with reversible session vault tokenization and exfiltration blocking. | P1 | **MITIGATED** |
| **LLM03:2025** | **Supply Chain Vulnerabilities** | Compromised plugins, external packages, or dependencies. | Strict zero-direct-execution sandbox, pinned dependency versions, deterministic OPA policy constraints. | P2 | **MITIGATED** |
| **LLM04:2025** | **Data and Model Poisoning** | Malicious fine-tuning data or corrupt training data influencing model reasoning. | Semantic validation with Qualcomm Cloud AI 100 / Snapdragon NPU cross-validated against deterministic OPA Rego policies. | P2 | **MITIGATED** |
| **LLM05:2025** | **Improper Output Handling** | Unvalidated agent tool call arguments resulting in command injection, SQL corruption, or system crashes. | **Tool Schema & Argument Validator** (`tool_schemas.py`): Strict type, boundary, non-empty, and path-traversal validation for all tool parameters before gateway handoff. | P0 | **MITIGATED** |
| **LLM06:2025** | **Excessive Agency** | Autonomous agents executing side-effecting operations (refunds, database deletes, emails) without boundary checks. | **Policy Enforcement Point (PEP)** (`execution.py`, `opa_client.py`): Zero direct tool access. OPA Rego declarative policies enforce ALLOW, HUMAN REVIEW, and BLOCK. | P0 | **MITIGATED** |
| **LLM07:2025** | **System Prompt Leakage** | Extraction of internal system prompts and confidential instructions. | **Adversarial Extraction Defense** (`jailbreak.py`): Blocks prompts attempting to dump system directives, secret instructions, or delimiter tokens. | P1 | **MITIGATED** |
| **LLM08:2025** | **Vector and Embedding Weaknesses** | Poisoned retrieval sources in RAG pipelines executing secondary attacks. | Untrusted provenance source taint tracking (`EXTERNAL_WEB`, `UNTRUSTED_DOCUMENT`) halts high-risk tool dispatch. | P2 | **MITIGATED** |
| **LLM09:2025** | **Misinformation & Hallucination** | Agent hallucinating false execution authorization or fictitious customer approval. | **Intent Alignment Engine** (`intent_alignment.py`): Detects goal drift between original user prompt and agent tool proposal. | P1 | **MITIGATED** |
| **LLM10:2025** | **Unbounded Consumption** | Infinite agent loops, excessive inference consumption, or denial-of-service tool spam. | **Rate Limiting & Fail-Closed Defense** (`rate_limit.py`, `decision_engine.py`): Sliding window rate-limiting (120 req/min) and fail-closed halt if validators offline. | P1 | **MITIGATED** |

---

### NIST AI RMF Governance Integration
- **GOVERN**: Declarative enterprise policies ([`finance.rego`](file:///c:/Users/nivas/Desktop/Gaurdrail/backend/app/policy/policies/finance.rego), [`database.rego`](file:///c:/Users/nivas/Desktop/Gaurdrail/backend/app/policy/policies/database.rego)) and supervisor authorization gate.
- **MAP**: Standardized Action Contract mapping `Who`, `What`, `Why`, `Tool`, `Target`, `Environment`, `Data Sensitivity`, `Reversibility`.
- **MEASURE**: Automated 8-scenario acceptance suite and regression tests.
- **MANAGE**: Fail-closed execution gate, immutable audit logging, and human supervisor reviews.
