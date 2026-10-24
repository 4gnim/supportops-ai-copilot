# Backup and Restore Procedure

## Backup verification

A successful backup job does not prove that data can be restored. Verify backup completion, retention, and restore readiness according to the service's recovery objectives.

## Restore process

1. Confirm the incident and obtain approval from the service owner before restoring production data.
2. Identify the correct backup point and the expected data-loss window.
3. Restore first into an isolated environment when practical.
4. Validate record counts, application health, and key business operations.
5. Coordinate the production cutover and communicate the result.
6. Record the recovery point, recovery duration, validation results, and any remaining data gaps.

## Important limitation

This document does not define service-specific retention periods, recovery point objectives, or recovery time objectives. Obtain those values from the service owner before making a production recovery decision.
