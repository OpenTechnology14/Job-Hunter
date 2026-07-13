# Open-Source Release Checklist

## Current verdict

**Conditional GO for local single-user release; NO-GO for hosted multi-user release.**

## Local P0

- [x] MIT license exists.
- [x] Contributing guide, security policy, code of conduct, and issue/PR templates exist.
- [x] Local secrets, credentials, output, and personal profiles are ignored.
- [ ] Full Git history passes secret/private-data scanning.
- [ ] CI enforces deterministic tests on supported Python versions.
- [ ] Tests use only a synthetic identity and temporary filesystem.
- [ ] Dry-run and confirmation safety invariants have direct tests.
- [ ] `TESTING.md` and `CONTRIBUTING.md` match actual automation.
- [ ] Clean clone setup and health check pass from documented commands.
- [ ] Release notes clearly label live-provider and browser-automation limitations.

## Hosted P0 (separate release profile)

- [ ] Application authentication and secure sessions.
- [ ] Object-level authorization/tenant isolation for all profile-scoped routes.
- [ ] CSRF protection on mutations.
- [ ] Declarative, non-executable hosted profile format.
- [ ] Upload size/type/magic/quota and safe serving.
- [ ] Concurrency-safe persistence and migration/backup story.
- [ ] Production WSGI server, debug disabled, proxy/TLS/security-header configuration.
- [ ] Rate limits, abuse controls, audit logs, retention/deletion policy.

## Release record

Record version/tag, commit, Python/OS matrix, dependency lock/hash, test evidence, known skipped live checks, changelog, rollback steps, and maintainer sign-off.
