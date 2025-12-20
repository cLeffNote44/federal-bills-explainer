# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Currently supported versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of Federal Bills Explainer seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### Where to Report

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to: **cLeffNote44@pm.me**

Please include the following information in your report:

- Type of issue (e.g., buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

### What to Expect

- You should receive an acknowledgment within 48 hours
- We will keep you informed about the progress of the fix
- We may ask for additional information or guidance
- Once the issue is resolved, we will publicly disclose the vulnerability (with credit to you if desired)

## Security Best Practices

When deploying Federal Bills Explainer:

### Environment Variables

- **Never use default secrets in production** - Change all default passwords and tokens
- Use a secrets manager (AWS Secrets Manager, HashiCorp Vault, etc.)
- Rotate credentials regularly
- Use strong, randomly generated passwords

### Database Security

- Never expose PostgreSQL directly to the internet
- Use strong passwords for database users
- Enable SSL/TLS for database connections
- Regularly update PostgreSQL and pgvector
- Implement database access controls and auditing

### API Security

- Enable rate limiting on all endpoints
- Implement proper authentication and authorization
- Use HTTPS in production (enforce TLS 1.2+)
- Set appropriate CORS policies
- Validate and sanitize all inputs
- Implement request size limits

### Container Security

- Use specific image tags (avoid `latest`)
- Regularly scan images for vulnerabilities
- Run containers as non-root users
- Use read-only filesystems where possible
- Keep Docker and dependencies updated

### Application Security

- Keep all dependencies up to date
- Monitor for security advisories
- Enable security headers (CSP, HSTS, etc.)
- Implement proper error handling (don't leak sensitive info)
- Log security events for auditing

### Network Security

- Use private networks for service communication
- Implement network segmentation
- Use firewalls to restrict access
- Monitor network traffic for anomalies

## Security Updates

Security updates will be released as soon as possible after a vulnerability is confirmed. Updates will be announced via:

- GitHub Security Advisories
- Release notes in CHANGELOG.md
- Email notification to security@federalbills.com (if available)

## Known Security Considerations

### Current Implementation Notes

1. **Admin Authentication** - Currently uses simple token authentication. For production, implement OAuth2/OIDC.
2. **Rate Limiting** - Implemented for Congress.gov API but needs addition to all API endpoints.
3. **Session Management** - JWT implementation is prepared but needs full integration.
4. **Input Validation** - Pydantic provides basic validation; additional sanitization recommended.

## Acknowledgments

We thank the following security researchers for their responsible disclosure:

- (List will be updated as vulnerabilities are reported and fixed)

## Contact

For general security questions: cLeffNote44@pm.me

For urgent security issues: cLeffNote44@pm.me (mark as URGENT - SECURITY)

---

Last updated: 2025-11-09
