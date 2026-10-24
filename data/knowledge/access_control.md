# Access Control and Data Handling

## API keys

API keys authenticate a calling application; they do not replace per-user authorization. Store keys outside source control, rotate them when exposure is suspected, and use different credentials for different environments.

## Least privilege

Grant each service only the permissions needed for its task. An assistant that answers questions about runbooks should not receive write access to production systems unless that capability is explicitly required, reviewed, and protected by an approval flow.

## Sensitive information

Do not paste passwords, access tokens, private keys, or unnecessary personal data into prompts, tickets, or logs. Redact sensitive values before sending diagnostic material to an external AI service.

## Destructive actions

Before deleting data, changing production configuration, or triggering another destructive action, verify the caller's authorization and scope. Require an explicit approval step when policy demands it. A language model's tool request is not itself proof of authorization.
