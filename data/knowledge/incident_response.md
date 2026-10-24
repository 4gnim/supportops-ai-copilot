# Incident Response Runbook

## Severity levels

- SEV-1: A critical service is unavailable for many customers, or a security incident is suspected. Notify the incident commander and on-call engineer immediately.
- SEV-2: A major feature is degraded for a significant group of users, but a workaround exists. Notify the service owner and on-call engineer.
- SEV-3: A limited feature or non-critical workflow is degraded. Create a ticket for the owning team and follow the normal triage queue.

## First response checklist

1. Record the start time, affected service, observed symptoms, and a request or correlation ID when available.
2. Check the service health endpoint and recent deployment history.
3. Review application logs for errors around the reported time. Redact secrets and personal data before sharing logs.
4. Estimate user impact and choose a severity level using the criteria above.
5. For SEV-1, notify the incident commander and on-call engineer immediately. Do not wait for a complete root-cause analysis.
6. Record actions taken and the outcome in the incident ticket.

## Communication

For an active SEV-1 or SEV-2 incident, post a short status update whenever the impact or mitigation status materially changes. State confirmed facts separately from hypotheses. Do not promise a recovery time unless the incident commander has approved it.
