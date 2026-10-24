# Application Deployment Runbook

## Before deployment

1. Confirm that the change has passed automated tests and the required code review.
2. Verify configuration values are supplied through environment variables or a secret manager. Do not commit credentials to source control.
3. Confirm the release version and rollback procedure.
4. Check database migration compatibility before deploying a version that changes the schema.

## Deployment checks

1. Deploy to the intended environment using the approved release pipeline.
2. Check the application liveness endpoint.
3. Review startup logs for configuration errors and failed dependency connections.
4. Run a small smoke test against the main user flow.
5. Monitor error rate and latency after deployment.

## Rollback criteria

Consider rollback when the release causes a sustained increase in error rates, prevents a critical user flow from working, or introduces a data-integrity problem. Notify the service owner, record the reason, and verify health after rollback.

## Configuration

Development, staging, and production must use separate configuration values. Production secrets must not be copied into local development files. A successful build alone does not prove the service is healthy; a smoke test and post-release observation are required.
