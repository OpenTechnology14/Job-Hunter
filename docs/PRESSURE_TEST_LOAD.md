# Pressure and Failure Test Plan

Job-Hunter is not a high-throughput service, but it is exposed to provider drift, long-running browser actions, filesystem contention, and safety-critical submission decisions.

| Scenario | Pressure/failure | Pass condition |
|---|---|---|
| Source drift | Missing/renamed fields, HTML redesign, 404/429/5xx | Source fails visibly without corrupting existing jobs |
| Provider throttling | Burst requests plus Retry-After | Bounded rate/retry; no infinite loop |
| Duplicate jobs | Same job from several sources/runs | Stable dedupe behavior and explainable merge |
| Large dataset | 100k synthetic CSV rows | Bounded memory and documented response time |
| Concurrent edit/scrape | PATCH job while scrape saves results | No lost update or malformed CSV |
| Process interruption | Kill during file write | Original or complete new file remains; never partial CSV |
| Browser navigation failure | Timeout, CAPTCHA, login expiry, changed form | Stops safely; no submit; actionable status |
| Dry run | All supported apply paths | Submit action count remains zero |
| Confirmation replay | Confirm one application, then encounter another | Second submission requires a new confirmation |
| Resume upload | Oversize, wrong MIME/magic, traversal names | Rejected without file escape or partial residue |
| Multi-user hosted test | Cross-profile route and filename attempts | Every cross-tenant access is denied |
| OpenTech outage | Endpoint unavailable then recovers | Local bounded queue retries idempotently; scrape/apply remains local |

Record command, commit, fixture seed, environment, elapsed time, peak memory, error counts, and recovery result. Live-provider tests are smoke tests, not deterministic release evidence.
