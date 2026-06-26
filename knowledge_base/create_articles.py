import json
import os

articles = [
    {
        "id": "KB-001",
        "title": "What Cloud Providers Does CloudDash Support?",
        "category": "faq",
        "tags": ["cloud providers", "AWS", "GCP", "Azure", "integrations"],
        "content": """CloudDash supports all three major cloud providers: Amazon Web Services (AWS), Google Cloud Platform (GCP), and Microsoft Azure. Each integration provides real-time monitoring, alerting, and cost optimization capabilities.

AWS Integration: CloudDash connects to AWS via CloudWatch metrics, CloudTrail logs, and Cost Explorer APIs. Supported services include EC2, RDS, Lambda, S3, ECS, EKS, and over 150 additional AWS services. Authentication is handled via IAM roles (recommended) or access key pairs.

GCP Integration: CloudDash integrates with Google Cloud Monitoring (formerly Stackdriver), Cloud Logging, and the Cloud Billing API. Supported services include Compute Engine, Cloud Run, GKE, Cloud SQL, and BigQuery. Authentication uses service account JSON keys or Workload Identity Federation.

Azure Integration: CloudDash connects to Azure Monitor, Azure Cost Management, and the Azure Resource Manager API. Supported services include Virtual Machines, AKS, Azure Functions, SQL Database, and Blob Storage. Authentication uses service principals with client secret or certificate-based credentials.

Multi-cloud support: CloudDash can monitor resources across all three providers simultaneously in a single dashboard. Cross-cloud cost comparison and unified alerting are available on Pro and Enterprise plans.

To add a new cloud provider integration, navigate to Settings > Integrations > Add Integration and follow the provider-specific setup wizard. Setup typically takes 5-10 minutes per provider.""",
        "last_updated": "2026-04-15",
        "applies_to": ["Free", "Pro", "Enterprise"]
    },
    {
        "id": "KB-002",
        "title": "How to Reset Your CloudDash API Key",
        "category": "faq",
        "tags": ["API key", "reset", "authentication", "security"],
        "content": """Your CloudDash API key is used to authenticate programmatic access to the CloudDash REST API. If your key is compromised or you need to rotate it for security purposes, you can reset it at any time.

Steps to reset your API key:
1. Log in to your CloudDash dashboard at app.clouddash.io
2. Click your profile avatar in the top-right corner
3. Select Account Settings from the dropdown menu
4. Navigate to the API Keys tab
5. Click Regenerate Key next to the key you want to reset
6. Confirm the action when prompted — this immediately invalidates the old key
7. Copy the new key and store it securely — it will not be shown again

Important: Resetting your API key immediately invalidates the previous key. Any applications, scripts, or integrations using the old key will stop working until they are updated with the new key. Plan your key rotation accordingly.

Security best practices:
- Never commit API keys to version control
- Use environment variables to store keys in your applications
- Set up separate API keys for development and production environments
- Review API key usage logs under Account Settings > API Keys > Usage Log
- Enable IP allowlisting on Enterprise plans to restrict which IPs can use your key

If you believe your API key was compromised, reset it immediately and review your audit logs for unauthorized access under Settings > Audit Logs.""",
        "last_updated": "2026-05-01",
        "applies_to": ["Free", "Pro", "Enterprise"]
    },
    {
        "id": "KB-003",
        "title": "How to Invite Team Members to CloudDash",
        "category": "faq",
        "tags": ["team", "invite", "users", "collaboration", "access"],
        "content": """CloudDash supports multi-user access with role-based permissions. You can invite team members to your organization and assign them appropriate roles.

How to invite a team member:
1. Navigate to Settings > Team Management
2. Click Invite Member
3. Enter the team member's email address
4. Select their role: Viewer, Editor, or Admin (see role descriptions below)
5. Optionally restrict access to specific dashboards or cloud accounts
6. Click Send Invitation

The invited user will receive an email with a link to accept the invitation. The link expires after 72 hours. If it expires, you can resend the invitation from the Pending Invitations section.

Available roles:
- Viewer: Can view dashboards, alerts, and reports. Cannot make changes or access billing.
- Editor: Can create and modify dashboards, configure alerts, and manage integrations. Cannot manage team members or billing.
- Admin: Full access to all features including team management, billing, and organization settings.

Seat limits by plan:
- Free plan: Up to 2 team members
- Pro plan: Up to 10 team members
- Enterprise plan: Unlimited team members

If you need to remove a team member, go to Settings > Team Management, find the user, and click Remove. Their access is revoked immediately. On Enterprise plans, you can also temporarily deactivate a user without removing them.""",
        "last_updated": "2026-04-20",
        "applies_to": ["Free", "Pro", "Enterprise"]
    },
    {
        "id": "KB-004",
        "title": "CloudDash Plan Comparison: Free vs Pro vs Enterprise",
        "category": "faq",
        "tags": ["plans", "pricing", "free", "pro", "enterprise", "features"],
        "content": """CloudDash offers three plans designed to meet the needs of teams at different stages of growth.

Free Plan:
- Up to 2 cloud accounts (AWS, GCP, or Azure)
- Up to 2 team members
- 10 active alert rules
- 7-day metric history retention
- Community support via forums
- Basic dashboards and cost reports
- 1-hour metric refresh interval

Pro Plan ($149/month or $1,490/year):
- Up to 10 cloud accounts
- Up to 10 team members
- Unlimited alert rules
- 90-day metric history retention
- Email and chat support (business hours)
- Advanced dashboards with custom widgets
- 5-minute metric refresh interval
- Anomaly detection and forecasting
- Custom webhook integrations
- API access with 10,000 requests/day

Enterprise Plan (custom pricing):
- Unlimited cloud accounts
- Unlimited team members
- Unlimited alert rules
- 1-year+ metric history retention
- 24/7 dedicated support with SLA
- Custom dashboards with white-labeling
- 1-minute metric refresh interval
- Advanced anomaly detection with ML models
- SSO/SAML integration
- RBAC with custom roles
- Audit logs and compliance exports
- Custom API rate limits
- Dedicated onboarding and customer success manager

To upgrade your plan, go to Settings > Billing > Change Plan. Upgrades take effect immediately and are prorated. Downgrades take effect at the end of your current billing cycle.""",
        "last_updated": "2026-05-10",
        "applies_to": ["Free", "Pro", "Enterprise"]
    },
    {
        "id": "KB-005",
        "title": "Alerts Not Firing After Updating Cloud Integration Credentials",
        "category": "troubleshooting",
        "tags": ["alerts", "not firing", "credentials", "AWS", "integration", "broken"],
        "content": """If your CloudDash alerts stopped firing after updating your cloud provider credentials (AWS access keys, GCP service account, or Azure service principal), follow these steps to diagnose and resolve the issue.

Why this happens: CloudDash caches integration credentials for performance. When you update credentials in your cloud provider console but do not update them in CloudDash, the old (now invalid) credentials continue to be used until the cache expires or you manually refresh them. Additionally, if the new credentials have different IAM permissions, metric collection may partially or fully fail.

Step 1 — Update credentials in CloudDash:
1. Go to Settings > Integrations
2. Find the affected integration and click Edit
3. Enter your new credentials (access key, service account JSON, or service principal details)
4. Click Verify Connection — wait for the green checkmark
5. Click Save

Step 2 — Force a credential refresh:
After saving, click the Sync Now button on the integration card. This forces CloudDash to immediately use the new credentials and attempt metric collection.

Step 3 — Check IAM permissions:
The new credentials must have the same or greater permissions as the previous ones. For AWS, the minimum required policy is the CloudDashReadOnly managed policy (ARN: arn:aws:iam::aws:policy/CloudDashReadOnly). Missing permissions will cause specific metrics to fail silently.

Step 4 — Verify alert configuration:
Go to Alerts > Alert Rules and check that your alert rules are still in Active status. Credential errors can sometimes cause alert rules to enter a Suspended state. Click Resume on any suspended alerts.

Step 5 — Check the integration health dashboard:
Go to Settings > Integrations > [your integration] > Health. This shows a 24-hour log of metric collection attempts, including any errors. Common errors include InvalidClientTokenId (wrong access key), AccessDenied (insufficient permissions), and TokenExpired (rotated credentials not updated).

If alerts still do not fire after completing these steps, contact support with your integration health log and we will investigate further.""",
        "last_updated": "2026-05-12",
        "applies_to": ["Pro", "Enterprise"]
    },
    {
        "id": "KB-006",
        "title": "Dashboard Loading Slowly or Not Loading",
        "category": "troubleshooting",
        "tags": ["dashboard", "slow", "loading", "performance", "timeout"],
        "content": """If your CloudDash dashboard is loading slowly or failing to load, this is usually caused by one of three things: too many widgets with long time ranges, browser cache issues, or a temporary service degradation.

Quick fix — try these first:
1. Hard refresh your browser: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)
2. Clear browser cache and cookies for app.clouddash.io
3. Try an incognito/private browser window
4. Check status.clouddash.io for any ongoing incidents

If the dashboard loads in incognito but not normally, clear your browser cache completely and try again.

Reducing dashboard load time:
Dashboards with many widgets querying long time ranges (30+ days) can be slow because each widget makes a separate API call. To improve performance:
- Reduce the default time range to 24 hours or 7 days
- Use the Dashboard Settings to enable lazy loading (widgets load as you scroll)
- Split large dashboards into multiple focused dashboards
- Use summary widgets instead of raw metric graphs where possible
- Enable dashboard caching under Dashboard Settings > Performance > Cache Results (refreshes every 5 minutes)

Widget-specific timeouts: If only some widgets fail to load and show a timeout error, the underlying metric query is taking too long. Click the widget's settings (gear icon) and either reduce the time range, add metric filters to narrow the data set, or switch from raw data to aggregated data (hourly or daily averages).

Browser compatibility: CloudDash supports Chrome 90+, Firefox 88+, Safari 14+, and Edge 90+. Older browsers may experience performance issues. Internet Explorer is not supported.

If none of the above resolves the issue, export your dashboard configuration (Dashboard Settings > Export) and contact support with the export file and a description of which widgets are failing.""",
        "last_updated": "2026-04-28",
        "applies_to": ["Free", "Pro", "Enterprise"]
    },
    {
        "id": "KB-007",
        "title": "AWS CloudWatch Integration Failing",
        "category": "troubleshooting",
        "tags": ["AWS", "CloudWatch", "integration", "failing", "error", "IAM", "permissions"],
        "content": """If your AWS CloudWatch integration is failing or showing an error in CloudDash, follow this diagnostic guide to identify and fix the issue.

Common error messages and their fixes:

Error: InvalidClientTokenId
Cause: The AWS access key ID is invalid or has been deactivated.
Fix: Go to Settings > Integrations > AWS > Edit, re-enter your access key ID and secret access key. Verify the key is active in your AWS IAM console under Security Credentials.

Error: AccessDenied / Access Denied
Cause: The IAM user or role used by CloudDash does not have the required permissions.
Fix: Attach the CloudDashReadOnly managed policy to your IAM user or role. The required permissions include: cloudwatch:GetMetricData, cloudwatch:ListMetrics, cloudwatch:DescribeAlarms, ec2:DescribeInstances, ce:GetCostAndUsage, and tag:GetResources. For a complete policy document, see the CloudDash AWS Setup Guide.

Error: AuthFailure
Cause: The AWS secret access key is incorrect.
Fix: Regenerate your AWS access key pair in the IAM console and update both the key ID and secret in CloudDash Settings > Integrations > AWS > Edit.

Error: RequestExpired / Token expired
Cause: Clock skew between CloudDash servers and AWS. This is rare but can occur.
Fix: This is resolved automatically. If it persists for more than 1 hour, contact support.

Error: Integration shows as Connected but no metrics appear
Cause: Metrics can take up to 15 minutes to appear after a new integration is connected. If metrics still do not appear after 15 minutes, verify that your AWS resources are tagged correctly and that CloudWatch is enabled for the services you want to monitor.

Verifying the integration is working:
1. Go to Settings > Integrations > AWS
2. Click the Health tab
3. Look for successful metric pulls in the last hour (shown as green entries)
4. Click on any red (failed) entries to see the specific error message

Using IAM roles instead of access keys (recommended):
For better security, use cross-account IAM roles instead of access key pairs. This eliminates the need to rotate keys and reduces the risk of credential exposure. See KB-013 for setup instructions.""",
        "last_updated": "2026-05-15",
        "applies_to": ["Free", "Pro", "Enterprise"]
    },
    {
        "id": "KB-008",
        "title": "Webhooks Not Receiving Alert Events",
        "category": "troubleshooting",
        "tags": ["webhook", "alerts", "notifications", "not receiving", "endpoint"],
        "content": """If your webhook endpoint is not receiving alert notifications from CloudDash, follow these steps to diagnose the issue.

Step 1 — Verify webhook configuration:
1. Go to Settings > Integrations > Webhooks
2. Confirm the webhook URL is correct and publicly accessible
3. Ensure the endpoint uses HTTPS (HTTP webhooks are not supported for security reasons)
4. Check that the selected events include the alert types you expect to receive

Step 2 — Test the webhook:
CloudDash provides a webhook test tool. Go to Settings > Integrations > Webhooks > [your webhook] > Send Test Event. This sends a sample payload to your endpoint. Check your endpoint logs to confirm receipt.

Step 3 — Check webhook delivery logs:
Go to Settings > Integrations > Webhooks > [your webhook] > Delivery Log. This shows all webhook delivery attempts, their HTTP status codes, and response bodies. Common issues:
- 404: Your endpoint URL has changed or is incorrect
- 401/403: Your endpoint requires authentication that CloudDash is not providing
- 500: Your endpoint is erroring when processing the payload
- Timeout: Your endpoint took more than 10 seconds to respond

Step 4 — Check firewall and IP allowlisting:
If your endpoint is behind a firewall, you must allowlist CloudDash's outbound IP ranges. Current CloudDash webhook source IPs are: 34.102.134.0/24 and 35.186.192.0/24. These IPs are published at docs.clouddash.io/webhook-ips and updated with 30 days notice.

Step 5 — Webhook retry behavior:
CloudDash retries failed webhook deliveries up to 3 times with exponential backoff (5 min, 30 min, 2 hours). If all 3 retries fail, the event is marked as undelivered and no further attempts are made. You can manually retry undelivered events from the Delivery Log.

Payload format: CloudDash webhook payloads are JSON. See KB-015 for the full payload schema and example events.""",
        "last_updated": "2026-04-22",
        "applies_to": ["Pro", "Enterprise"]
    },
    {
        "id": "KB-009",
        "title": "Understanding Your CloudDash Invoice",
        "category": "billing",
        "tags": ["invoice", "billing", "charges", "statement", "receipt"],
        "content": """Your CloudDash invoice is generated on the first day of each month and covers usage for the previous billing cycle. This guide explains each line item you may see on your invoice.

Invoice sections:

Base subscription fee: The flat monthly or annual fee for your current plan (Free, Pro, or Enterprise). For annual plans, this reflects the monthly equivalent already paid upfront.

Overage charges (Pro plan): Pro plan includes up to 10 cloud accounts and 10,000 API requests per day. If you exceed these limits, overage charges apply:
- Additional cloud accounts: $15/account/month
- Additional API requests: $0.001 per request above the daily limit

Seat charges (Enterprise plan): Enterprise plan billing includes a per-seat component for team members above the included base seats. Your contract specifies the included seat count and the per-seat overage rate.

Taxes: Applicable sales tax, VAT, or GST is applied based on your billing address. US customers in states with SaaS software tax obligations will see state tax applied. EU customers will see VAT applied unless a valid VAT number is provided in Settings > Billing > Tax Information.

How to access your invoices:
1. Go to Settings > Billing > Invoice History
2. Click any invoice to view or download it as a PDF
3. Invoices are also emailed to the billing contact email address on file

Payment methods accepted: Credit card (Visa, Mastercard, Amex, Discover), ACH bank transfer (US only, Enterprise plans), and wire transfer (Enterprise plans, minimum $5,000/year).

If you believe there is an error on your invoice, contact billing support within 30 days of the invoice date. See KB-011 for the dispute and refund process.""",
        "last_updated": "2026-05-01",
        "applies_to": ["Free", "Pro", "Enterprise"]
    },
    {
        "id": "KB-010",
        "title": "How to Upgrade or Downgrade Your CloudDash Plan",
        "category": "billing",
        "tags": ["upgrade", "downgrade", "plan change", "pro", "enterprise", "billing"],
        "content": """You can change your CloudDash plan at any time from the billing settings. This guide covers how upgrades and downgrades work and how they are billed.

Upgrading your plan (Free to Pro, or Pro to Enterprise):

To upgrade:
1. Go to Settings > Billing > Change Plan
2. Select the new plan
3. Enter or confirm your payment method
4. Click Confirm Upgrade

Upgrades take effect immediately. You gain access to all new plan features right away. Billing is prorated — you are charged only for the remaining days in the current billing cycle at the new plan's rate, minus any credit from the remaining days on your current plan.

Example: If you upgrade from Free to Pro ($149/month) on day 15 of a 30-day billing cycle, you are charged approximately $74.50 for the remaining 15 days.

Downgrading your plan (Pro to Free, or Enterprise to Pro):

To downgrade:
1. Go to Settings > Billing > Change Plan
2. Select the lower plan
3. Review the features you will lose access to
4. Click Confirm Downgrade

Downgrades take effect at the end of your current billing cycle. You retain access to current plan features until that date. No refund is issued for the remaining days on your current plan.

Important: Before downgrading, review your current usage. If you have more cloud accounts, team members, or alert rules than the lower plan allows, you must reduce them before the downgrade takes effect. CloudDash will send reminder emails 7 days and 1 day before the downgrade date listing any items that need to be removed.

Annual plan changes: If you are on an annual plan and want to upgrade mid-year, you receive a prorated credit for the remaining months of your annual plan applied to the new plan's annual fee. Contact sales@clouddash.io for annual plan changes.""",
        "last_updated": "2026-05-10",
        "applies_to": ["Free", "Pro", "Enterprise"]
    },
    {
        "id": "KB-011",
        "title": "Refund Policy and How to Request a Refund",
        "category": "billing",
        "tags": ["refund", "billing dispute", "charge", "money back", "policy"],
        "content": """CloudDash's refund policy is designed to be fair and transparent. This article explains when refunds are available and how to request one.

Refund eligibility:

30-day money-back guarantee (new subscriptions only): If you are a new CloudDash customer and are not satisfied within the first 30 days of your first paid subscription, you are eligible for a full refund. This applies to your first Pro or Enterprise subscription only and cannot be used for plan renewals.

Billing errors: If you were charged incorrectly due to a CloudDash error (for example, charged twice, charged the wrong amount, or charged after cancellation), you are eligible for a full refund of the erroneous charge regardless of when it occurred. Billing error refunds are processed within 3-5 business days.

Annual plan cancellations: If you cancel an annual plan, you are eligible for a prorated refund for the remaining full months of your subscription (partial months are not refunded). For example, if you cancel 4 months into a 12-month annual plan, you receive a refund for 8 months.

Refunds not available: Monthly plan cancellations do not receive refunds for the current month. Downgrades do not receive refunds for unused days on the higher plan.

How to request a refund:
1. Go to Settings > Billing > Invoice History
2. Find the invoice you want to dispute
3. Click Request Refund next to the invoice
4. Select the reason and provide any additional details
5. Submit the request

Alternatively, email billing@clouddash.io with your account email, the invoice number, the amount in dispute, and the reason for the request.

Refund processing time: Approved refunds are returned to the original payment method within 5-10 business days. You will receive an email confirmation when the refund is initiated.

Note: Refund requests that require manager approval (amounts over $500 or disputes involving multiple invoices) are escalated to our billing team and may take up to 5 business days to review.""",
        "last_updated": "2026-05-08",
        "applies_to": ["Free", "Pro", "Enterprise"]
    },
    {
        "id": "KB-012",
        "title": "How to Update Billing Information and Payment Method",
        "category": "billing",
        "tags": ["payment method", "credit card", "billing address", "update", "payment failure"],
        "content": """Keeping your billing information up to date ensures uninterrupted access to CloudDash. This guide covers how to update your payment method, billing address, and billing contact.

Updating your credit card:
1. Go to Settings > Billing > Payment Methods
2. Click Add Payment Method
3. Enter your new card details
4. Click Set as Default to make it the primary payment method
5. Optionally remove the old card by clicking the trash icon next to it

Updating your billing address:
1. Go to Settings > Billing > Billing Information
2. Click Edit next to the billing address
3. Update your address and click Save
Note: Changing your billing address may affect applicable tax calculations starting from your next invoice.

Updating the billing contact email:
The billing contact receives all invoices and payment receipts. To change it:
1. Go to Settings > Billing > Billing Information
2. Click Edit next to the billing contact
3. Enter the new email address and click Save

What happens when a payment fails:
If a payment fails, CloudDash automatically retries the charge 3 times over 7 days (on days 1, 3, and 7 after the initial failure). You will receive an email notification after each failed attempt with a link to update your payment method.

If payment is not resolved within 7 days of the initial failure:
- Free plan features remain accessible
- Pro/Enterprise features are suspended (dashboards become read-only, alerts are paused)
- After 14 days with no payment, the account is downgraded to the Free plan and data older than 7 days is archived

To restore access after a payment failure, update your payment method and the outstanding balance is charged immediately.""",
        "last_updated": "2026-04-30",
        "applies_to": ["Free", "Pro", "Enterprise"]
    },
    {
        "id": "KB-013",
        "title": "CloudDash API Authentication and API Keys",
        "category": "api",
        "tags": ["API", "authentication", "API key", "bearer token", "REST"],
        "content": """The CloudDash REST API uses API key authentication. All API requests must include your API key in the Authorization header as a Bearer token.

Base URL: https://api.clouddash.io/v2

Authentication header format:
Authorization: Bearer YOUR_API_KEY

Example request using curl:
curl -X GET "https://api.clouddash.io/v2/dashboards" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json"

Generating an API key:
1. Log in to your CloudDash dashboard
2. Go to Account Settings > API Keys
3. Click Generate New Key
4. Give the key a descriptive name (e.g., "Production Monitoring Script")
5. Click Generate — copy the key immediately, it is not shown again

API key scopes: By default, API keys have read and write access to all resources in your account. On Enterprise plans, you can create scoped API keys with read-only access or restricted to specific resource types (dashboards, alerts, integrations).

Security best practices:
- Store API keys in environment variables, never in source code
- Use separate keys for different applications and environments
- Rotate keys every 90 days as a security best practice
- Delete unused keys from Account Settings > API Keys

API versioning: The current stable version is v2. The v1 API is deprecated and will be removed on December 31, 2026. Migrate to v2 before that date. See the migration guide at docs.clouddash.io/api/v1-to-v2.

Testing your API key:
curl -X GET "https://api.clouddash.io/v2/me" \
  -H "Authorization: Bearer YOUR_API_KEY"

A successful response returns your account details in JSON format. A 401 Unauthorized response means the key is invalid or expired.""",
        "last_updated": "2026-05-01",
        "applies_to": ["Free", "Pro", "Enterprise"]
    },
    {
        "id": "KB-014",
        "title": "CloudDash API Rate Limits",
        "category": "api",
        "tags": ["API", "rate limits", "throttling", "429", "quota"],
        "content": """CloudDash API rate limits are applied per API key to ensure fair usage and platform stability. Understanding these limits helps you design integrations that stay within bounds.

Rate limits by plan:

Free plan: 1,000 API requests per day, maximum 10 requests per minute
Pro plan: 10,000 API requests per day, maximum 60 requests per minute
Enterprise plan: Custom limits (default 100,000/day, 300/minute) — contact your account manager to adjust

Rate limit headers: Every API response includes headers showing your current usage:
- X-RateLimit-Limit: Your total daily request allowance
- X-RateLimit-Remaining: Requests remaining in the current day
- X-RateLimit-Reset: Unix timestamp when the daily limit resets (midnight UTC)
- X-RateLimit-Minute-Limit: Requests allowed per minute
- X-RateLimit-Minute-Remaining: Requests remaining in the current minute

When you exceed the rate limit, the API returns HTTP 429 Too Many Requests with a Retry-After header indicating how many seconds to wait before retrying.

Handling rate limits in your code:
- Check the X-RateLimit-Remaining header and slow down requests as it approaches zero
- Implement exponential backoff when you receive a 429 response
- Cache responses where possible to reduce redundant API calls
- Use bulk endpoints (e.g., /v2/metrics/batch) instead of multiple single-metric calls

Exemptions: Webhook event deliveries do not count against your API rate limit. Metric data ingestion via the CloudDash agent also does not count against the REST API limit.

If you consistently need higher limits, contact sales@clouddash.io to discuss Enterprise plan options with custom rate limits.""",
        "last_updated": "2026-04-15",
        "applies_to": ["Free", "Pro", "Enterprise"]
    },
    {
        "id": "KB-015",
        "title": "Configuring Webhooks in CloudDash",
        "category": "api",
        "tags": ["webhook", "configuration", "payload", "events", "notifications"],
        "content": """CloudDash webhooks allow you to receive real-time HTTP notifications when events occur in your account, such as alerts firing, integrations failing, or team members being added.

Setting up a webhook:
1. Go to Settings > Integrations > Webhooks
2. Click Add Webhook
3. Enter your endpoint URL (must be HTTPS)
4. Select the events you want to receive (see event types below)
5. Optionally add a secret for payload signature verification
6. Click Save and Test

Event types available:
- alert.triggered: An alert rule threshold was crossed
- alert.resolved: An alert has returned to normal
- integration.failed: A cloud integration stopped collecting metrics
- integration.recovered: A failed integration is collecting metrics again
- billing.payment_failed: A payment attempt failed
- billing.invoice_created: A new invoice is available
- team.member_added: A new user joined your organization
- team.member_removed: A user was removed from your organization

Webhook payload format:
{
  "event": "alert.triggered",
  "timestamp": "2026-05-15T14:23:00Z",
  "account_id": "acc_123456",
  "data": {
    "alert_id": "alrt_789",
    "alert_name": "High CPU on prod-server-1",
    "severity": "critical",
    "metric": "cpu_utilization",
    "current_value": 94.2,
    "threshold": 90.0,
    "resource": "ec2:i-0abc123def456"
  }
}

Verifying webhook signatures: If you configured a webhook secret, CloudDash signs each payload using HMAC-SHA256. The signature is included in the X-CloudDash-Signature header. Verify it in your endpoint to ensure the request is genuine.

Retry behavior: Failed webhook deliveries are retried up to 3 times with exponential backoff. See KB-008 for full retry behavior and troubleshooting.""",
        "last_updated": "2026-05-05",
        "applies_to": ["Pro", "Enterprise"]
    },
    {
        "id": "KB-016",
        "title": "CloudDash SDK Quickstart Guide",
        "category": "api",
        "tags": ["SDK", "Python", "JavaScript", "quickstart", "client library"],
        "content": """CloudDash provides official client SDKs for Python and JavaScript (Node.js) to simplify API integration. This guide covers installation and basic usage for both.

Python SDK:

Installation:
pip install clouddash-sdk

Basic usage:
from clouddash import CloudDashClient

client = CloudDashClient(api_key="YOUR_API_KEY")

# List all dashboards
dashboards = client.dashboards.list()

# Get metrics for a specific resource
metrics = client.metrics.get(
    resource_id="ec2:i-0abc123def456",
    metric="cpu_utilization",
    start_time="2026-05-01T00:00:00Z",
    end_time="2026-05-02T00:00:00Z",
    interval="1h"
)

# Create an alert rule
alert = client.alerts.create(
    name="High CPU Alert",
    metric="cpu_utilization",
    threshold=90,
    condition="greater_than",
    severity="critical",
    notification_channels=["email", "webhook"]
)

JavaScript SDK:

Installation:
npm install @clouddash/sdk

Basic usage:
const { CloudDashClient } = require('@clouddash/sdk');
const client = new CloudDashClient({ apiKey: 'YOUR_API_KEY' });

const dashboards = await client.dashboards.list();
const metrics = await client.metrics.get({ resourceId: 'ec2:i-0abc123', metric: 'cpu_utilization' });

Error handling: The SDK raises CloudDashAPIError for API errors, CloudDashRateLimitError for rate limit errors (includes retryAfter property), and CloudDashAuthError for authentication failures.

SDK documentation: Full API reference and examples are available at docs.clouddash.io/sdk. The SDK source code is open source at github.com/clouddash/sdk-python and github.com/clouddash/sdk-js.""",
        "last_updated": "2026-04-10",
        "applies_to": ["Free", "Pro", "Enterprise"]
    },
    {
        "id": "KB-017",
        "title": "Setting Up SSO with SAML for CloudDash",
        "category": "account",
        "tags": ["SSO", "SAML", "single sign-on", "identity provider", "Okta", "Azure AD"],
        "content": """CloudDash supports Single Sign-On (SSO) via SAML 2.0, allowing your team to log in using your organization's identity provider (IdP). SSO is available on Enterprise plans only.

Supported identity providers: Okta, Azure Active Directory, Google Workspace, OneLogin, JumpCloud, and any SAML 2.0-compliant IdP.

Setup overview:
SSO setup requires configuration on both your identity provider and in CloudDash. The process takes approximately 20-30 minutes.

Step 1 — Get CloudDash SAML metadata:
1. Go to Settings > Security > Single Sign-On
2. Click Configure SSO
3. Download the CloudDash Service Provider metadata XML, or note the following values:
   - Entity ID: https://auth.clouddash.io/saml/metadata
   - ACS URL: https://auth.clouddash.io/saml/callback
   - Single Logout URL: https://auth.clouddash.io/saml/logout

Step 2 — Configure your identity provider:
In your IdP, create a new SAML application for CloudDash using the values from Step 1. Configure the following attribute mappings:
- email (required): User's email address
- firstName (required): User's first name
- lastName (required): User's last name
- role (optional): CloudDash role (viewer, editor, or admin)

Step 3 — Configure CloudDash with your IdP metadata:
1. In CloudDash, go to Settings > Security > Single Sign-On
2. Upload your IdP metadata XML or enter the IdP metadata URL
3. Click Verify Configuration — CloudDash will test the SAML connection
4. Once verified, click Enable SSO

Step 4 — Test SSO before enforcing it:
After enabling SSO, it is optional by default. Test that your team can log in via SSO before enforcing it. To enforce SSO (preventing password-based login):
Go to Settings > Security > Single Sign-On > Enforce SSO and toggle it on.

Troubleshooting SSO issues:
- SAML assertion validation failed: Check that your IdP clock is synchronized (NTP) and that the assertion expiry is at least 5 minutes
- User not provisioned: Ensure the user's email in the IdP matches their CloudDash account email
- Redirect loop: Clear browser cookies and try again in an incognito window
For further SSO troubleshooting, contact support with your SAML assertion (available in browser developer tools during a failed login attempt).""",
        "last_updated": "2026-05-12",
        "applies_to": ["Enterprise"]
    },
    {
        "id": "KB-018",
        "title": "Configuring Role-Based Access Control (RBAC) in CloudDash",
        "category": "account",
        "tags": ["RBAC", "roles", "permissions", "access control", "team"],
        "content": """CloudDash Role-Based Access Control (RBAC) allows you to define what each team member can see and do within your CloudDash organization. Standard roles are available on all plans; custom roles are available on Enterprise plans.

Standard roles:

Viewer:
- View all dashboards and reports
- View alert rules and their status (cannot create or modify)
- View integration status (cannot add or edit)
- Cannot access billing or team settings

Editor:
- All Viewer permissions
- Create, edit, and delete dashboards
- Create, edit, and delete alert rules
- Add and modify integrations
- Cannot manage team members or billing

Admin:
- All Editor permissions
- Invite and remove team members
- Change team member roles
- Access and manage billing settings
- Configure SSO and security settings
- View audit logs

Assigning roles:
1. Go to Settings > Team Management
2. Click the role dropdown next to a team member's name
3. Select the new role
4. The change takes effect immediately

Custom roles (Enterprise only):
Enterprise customers can create custom roles with granular permission sets. To create a custom role:
1. Go to Settings > Team Management > Roles > Create Custom Role
2. Give the role a name and description
3. Select individual permissions from the permission matrix
4. Click Save Role
5. Assign the custom role to team members as needed

Resource-level access control (Enterprise only):
On Enterprise plans, you can restrict users to specific dashboards, cloud accounts, or alert groups, regardless of their role. This is useful for multi-team or multi-tenant setups where different teams should only see their own resources.

To configure resource-level access:
Go to Settings > Team Management > [user] > Resource Access and select which resources the user can access.""",
        "last_updated": "2026-04-25",
        "applies_to": ["Free", "Pro", "Enterprise"]
    },
    {
        "id": "KB-019",
        "title": "Managing Teams and Organizations in CloudDash",
        "category": "account",
        "tags": ["team", "organization", "management", "workspace", "admin"],
        "content": """CloudDash organizes users into organizations. Each organization has its own dashboards, integrations, alerts, and billing. This guide covers how to manage your organization settings.

Organization settings:
Go to Settings > Organization to manage:
- Organization name and logo
- Default timezone for dashboards and reports
- Notification preferences (default channels for new alert rules)
- Data retention settings (Pro and Enterprise)
- API access policies

Managing team members:
See KB-003 for inviting new team members. From Settings > Team Management you can:
- View all current members and their roles
- View pending invitations (resend or cancel them)
- Change member roles
- Remove members (their access is revoked immediately)
- Export a CSV of all team members and their roles

Transferring organization ownership:
If the current owner needs to leave the organization:
1. Go to Settings > Team Management
2. Click Transfer Ownership next to another Admin's name
3. Confirm the transfer
The new owner has full administrative control. The previous owner becomes an Admin. Ownership transfers are logged in the audit trail.

Multiple organizations:
A single CloudDash user account can belong to multiple organizations. To switch between organizations, click the organization name in the top-left corner of the dashboard and select another organization from the dropdown.

To create a new organization under your account, click Create New Organization from the organization switcher. Each organization has its own subscription and billing.

Deleting an organization:
Organization deletion is permanent and removes all dashboards, alerts, integrations, and historical data. To delete:
1. Go to Settings > Organization > Danger Zone
2. Click Delete Organization
3. Type the organization name to confirm
4. Click Delete Permanently
This action cannot be undone. Export any data you need before deleting.""",
        "last_updated": "2026-05-03",
        "applies_to": ["Free", "Pro", "Enterprise"]
    },
    {
        "id": "KB-020",
        "title": "Using CloudDash Audit Logs",
        "category": "account",
        "tags": ["audit logs", "compliance", "security", "activity", "history"],
        "content": """CloudDash Audit Logs provide a complete record of actions taken within your organization, including user logins, configuration changes, and administrative actions. Audit logs are available on Pro and Enterprise plans.

Accessing audit logs:
1. Go to Settings > Audit Logs
2. Use the filters to narrow by date range, user, action type, or resource
3. Click any log entry to see full details

What is logged:
Authentication events: User logins (successful and failed), SSO authentication events, API key usage, session timeouts

Team management: User invitations sent, users added or removed, role changes, ownership transfers

Integration changes: Cloud integrations added, modified, or deleted, credential updates, integration enable/disable actions

Alert changes: Alert rules created, modified, deleted, or muted

Billing events: Plan changes, payment method updates, invoice generation

Dashboard changes: Dashboards created, modified, shared, or deleted

Audit log retention:
- Pro plan: 90 days of audit log history
- Enterprise plan: 1 year of audit log history (extended retention available)

Exporting audit logs:
Audit logs can be exported as CSV or JSON for compliance purposes:
1. Go to Settings > Audit Logs
2. Apply any filters for the export scope
3. Click Export > Choose format (CSV or JSON)
4. The export is emailed to your account email address

Streaming audit logs (Enterprise): Enterprise customers can stream audit logs in real time to their SIEM or log management system via webhook or syslog. Go to Settings > Audit Logs > Streaming to configure.

Compliance use cases: CloudDash audit logs support SOC 2 Type II compliance, ISO 27001 audits, and internal security reviews. Each log entry includes a timestamp, user identity, IP address, action performed, and the specific resource affected.""",
        "last_updated": "2026-05-07",
        "applies_to": ["Pro", "Enterprise"]
    }
]

output_dir = os.path.join(os.path.dirname(__file__), "articles")
os.makedirs(output_dir, exist_ok=True)

for article in articles:
    filename = f"{article['id'].lower().replace('-', '_')}.json"
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w") as f:
        json.dump(article, f, indent=2)

print(f"✓ Created {len(articles)} KB articles in {output_dir}")

categories = {}
for a in articles:
    categories.setdefault(a["category"], []).append(a["id"])
for cat, ids in sorted(categories.items()):
    print(f"  {cat}: {', '.join(ids)}")
