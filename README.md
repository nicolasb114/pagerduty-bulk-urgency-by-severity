# PagerDuty Incident Escalator

Automatically escalate PagerDuty incidents from low to high urgency based on alert severity. This tool is designed to run at the start of business hours to catch incidents that occurred outside business hours and may need immediate attention.

## Overview

This script:
1. Fetches recent incidents from PagerDuty
2. Filters for non-resolved, low urgency incidents
3. Analyzes alerts within each incident
4. Escalates incidents to high urgency if any alert matches configured severity levels

## Requirements

- Python 3.x (no external libraries required - uses only standard library)
- PagerDuty API token with incident management permissions
- Valid PagerDuty user email address

## Setup

### 1. Get Your PagerDuty API Token

1. Log in to your PagerDuty account
2. Go to **Integrations** → **API Access Keys**
3. Click **Create New API Key**
4. Give it a description (e.g., "Incident Escalator")
5. Copy the generated token

### 2. Configure the Script

Edit `config.json` with your settings:

```json
{
  "pagerduty_api_token": "your_actual_token_here",
  "from_email": "your.email@company.com",
  "severities_to_escalate": ["critical", "error", "warning"],
  "incident_limit": 300,
  "filter_acknowledged": false,
  "dry_run": false
}
```

#### Configuration Options

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `pagerduty_api_token` | string | Yes | Your PagerDuty API token |
| `from_email` | string | Yes | Email of a valid PagerDuty user (for audit trail) |
| `severities_to_escalate` | array | Yes | Alert severities that trigger escalation (e.g., `["critical", "error"]`) |
| `incident_limit` | number | No | Number of recent incidents to fetch (default: 300) |
| `filter_acknowledged` | boolean | No | If `true`, also filters out acknowledged incidents (default: `false`) |
| `dry_run` | boolean | No | If `true`, shows what would be escalated without making changes (default: `false`) |

#### Why `from_email` is Required

PagerDuty's API requires the `From` header to identify which user is making the modification. This is used for:
- **Audit trail**: PagerDuty tracks who changed each incident
- **Permissions**: The email must belong to a valid user in your PagerDuty account
- **Notifications**: Changes may trigger notifications showing this user as the modifier

**Important**: Use an email address associated with a valid PagerDuty user account, preferably a service account or admin account.

## Usage

### Manual Execution

Run the script manually:

```bash
python3 pagerduty_escalator.py
```

### Test First (Dry Run)

Before running for real, test with dry run mode:

1. Set `"dry_run": true` in `config.json`
2. Run the script: `python3 pagerduty_escalator.py`
3. Review the output to see what would be escalated
4. Set `"dry_run": false` when ready

### Automated Scheduling

#### Linux/Mac (cron)

To run every weekday at 9:00 AM:

1. Open crontab editor:
   ```bash
   crontab -e
   ```

2. Add this line (adjust path to your script location):
   ```
   0 9 * * 1-5 cd /path/to/script && /usr/bin/python3 pagerduty_escalator.py >> escalator.log 2>&1
   ```

3. Save and exit

**Cron schedule examples:**
- `0 9 * * 1-5` - 9:00 AM, Monday-Friday
- `0 8 * * *` - 8:00 AM, every day
- `30 8 * * 1-5` - 8:30 AM, Monday-Friday

#### Windows (Task Scheduler)

1. Open **Task Scheduler**
2. Click **Create Basic Task**
3. Name: "PagerDuty Incident Escalator"
4. Trigger: **Daily** or **Weekly** (configure for business days)
5. Action: **Start a program**
   - Program: `python` or `python3`
   - Arguments: `pagerduty_escalator.py`
   - Start in: `C:\path\to\script\directory`
6. Finish and test the task

## Output

The script provides detailed output:

```
PagerDuty Incident Escalator
==================================================
Configuration:
  - Incident limit: 300
  - Filter acknowledged: false
  - Severities to escalate: critical, error, warning
  - From email: user@example.com

Fetching last 300 incidents...
Retrieved 287 incidents
Filtering incidents (non-resolved, low urgency)...
Found 12 incidents to analyze

✓ Escalated: P1A2B3C - Database connection timeout
  Severity: critical
✓ Escalated: P4D5E6F - API rate limit exceeded
  Severity: error

==================================================
Summary:
  - Escalated 2 incident(s)
  - No failures
==================================================
```

## Troubleshooting

### "Error: config.json file not found"
- Ensure `config.json` is in the same directory as the script
- Check file permissions

### "HTTP 401: Unauthorized"
- Verify your API token is correct
- Ensure the token hasn't expired
- Check that the token has proper permissions

### "HTTP 400: Invalid Request"
- Verify `from_email` is a valid PagerDuty user email
- Check that email is associated with your PagerDuty account

### "Failed to process X incidents"
- Check the incident IDs listed in the error
- Verify API rate limits haven't been exceeded
- Check network connectivity

### No incidents are being escalated
- Run in dry run mode to see what would be escalated
- Verify incidents exist with low urgency and matching severity
- Check that `filter_acknowledged` setting matches your needs
- Ensure severities in config match actual alert severities (case-insensitive)

## How It Works

1. **Fetch**: Retrieves the last N incidents (configured limit)
2. **Filter**: Keeps only:
   - Non-resolved incidents (always)
   - Non-acknowledged incidents (if `filter_acknowledged` is `true`)
   - Low urgency incidents only
3. **Analyze**: For each filtered incident:
   - Fetches all alerts
   - Checks if any alert severity matches configured severities
4. **Escalate**: If match found:
   - Changes incident urgency from low to high
   - Logs the action

## Security Notes

- **Never commit `config.json` with real credentials to version control**
- Add `config.json` to `.gitignore`
- Store API tokens securely
- Use a dedicated service account email if possible
- Regularly rotate API tokens

## Example Workflow

**Scenario**: You want to escalate incidents with critical or error alerts that came in overnight.

1. Configure:
   ```json
   {
     "severities_to_escalate": ["critical", "error"],
     "filter_acknowledged": true,
     "incident_limit": 300
   }
   ```

2. Schedule to run at 9:00 AM weekdays

3. Script will:
   - Fetch last 300 incidents
   - Skip resolved and acknowledged incidents
   - Find low urgency incidents with critical/error alerts
   - Escalate them to high urgency
   - Your team sees them prioritized in the morning

## License

This project is provided as-is for use with PagerDuty incident management.

## Support

For issues or questions:
1. Check the Troubleshooting section
2. Review PagerDuty API documentation: https://developer.pagerduty.com/
3. Verify your configuration settings


---
**Setup:** edit `config.json` and replace the placeholder values with your own. Keep your real API key out of commits. Run with `dry_run` enabled first.
