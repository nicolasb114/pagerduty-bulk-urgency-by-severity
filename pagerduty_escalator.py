#!/usr/bin/env python3
"""
PagerDuty Incident Escalator
Automatically escalates low urgency incidents to high urgency based on alert severity.
"""

import json
import urllib.request
import urllib.error
import sys


def load_config(config_file='config.json'):
    """Load configuration from JSON file."""
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)

        # Validate required fields
        required_fields = ['pagerduty_api_token', 'from_email', 'severities_to_escalate']
        for field in required_fields:
            if field not in config:
                print(f"Error: Missing required field '{field}' in config.json")
                sys.exit(1)

        # Set defaults for optional fields
        config.setdefault('incident_limit', 300)
        config.setdefault('filter_acknowledged', False)
        config.setdefault('dry_run', False)

        return config
    except FileNotFoundError:
        print("Error: config.json file not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in config.json - {e}")
        sys.exit(1)


def make_api_request(url, token, method='GET', data=None, from_email=None):
    """Make a request to PagerDuty API using urllib."""
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Token token={token}',
        'Content-Type': 'application/json'
    }

    if from_email:
        headers['From'] = from_email

    request = urllib.request.Request(url, headers=headers, method=method)

    if data:
        request.data = json.dumps(data).encode('utf-8')

    try:
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        raise Exception(f"HTTP {e.code}: {error_body}")
    except urllib.error.URLError as e:
        raise Exception(f"Network error: {e.reason}")


def get_incidents(token, limit=300):
    """Fetch incidents from PagerDuty API."""
    url = f'https://api.pagerduty.com/incidents?limit={limit}'
    response = make_api_request(url, token)
    return response.get('incidents', [])


def filter_incidents(incidents, filter_acknowledged=False):
    """Filter incidents to keep only non-resolved and low urgency ones."""
    filtered = []

    for incident in incidents:
        status = incident.get('status', '')
        urgency = incident.get('urgency', '')

        # Skip resolved incidents
        if status == 'resolved':
            continue

        # Optionally skip acknowledged incidents
        if filter_acknowledged and status == 'acknowledged':
            continue

        # Keep only low urgency incidents
        if urgency == 'low':
            filtered.append(incident)

    return filtered


def get_incident_alerts(incident_id, token):
    """Get all alerts for a specific incident."""
    url = f'https://api.pagerduty.com/incidents/{incident_id}/alerts'
    response = make_api_request(url, token)
    return response.get('alerts', [])


def check_severity_match(alerts, target_severities):
    """Check if any alert has a severity matching the target severities."""
    for alert in alerts:
        severity = alert.get('severity', '').lower()
        if severity in [s.lower() for s in target_severities]:
            return True, severity
    return False, None


def escalate_incident(incident_id, token, from_email):
    """Escalate incident urgency from low to high."""
    url = f'https://api.pagerduty.com/incidents/{incident_id}'
    data = {
        'incident': {
            'type': 'incident_reference',
            'urgency': 'high'
        }
    }
    make_api_request(url, token, method='PUT', data=data, from_email=from_email)


def main():
    """Main execution function."""
    print("PagerDuty Incident Escalator")
    print("=" * 50)

    # Load configuration
    config = load_config()

    token = config['pagerduty_api_token']
    from_email = config['from_email']
    severities = config['severities_to_escalate']
    incident_limit = config['incident_limit']
    filter_ack = config['filter_acknowledged']
    dry_run = config['dry_run']

    if dry_run:
        print("\n*** DRY RUN MODE - No changes will be made ***\n")

    print(f"Configuration:")
    print(f"  - Incident limit: {incident_limit}")
    print(f"  - Filter acknowledged: {filter_ack}")
    print(f"  - Severities to escalate: {', '.join(severities)}")
    print(f"  - From email: {from_email}")
    print()

    # Fetch incidents
    print(f"Fetching last {incident_limit} incidents...")
    try:
        incidents = get_incidents(token, incident_limit)
        print(f"Retrieved {len(incidents)} incidents")
    except Exception as e:
        print(f"Error fetching incidents: {e}")
        sys.exit(1)

    # Filter incidents
    print("Filtering incidents (non-resolved, low urgency)...")
    filtered_incidents = filter_incidents(incidents, filter_ack)
    print(f"Found {len(filtered_incidents)} incidents to analyze")
    print()

    if len(filtered_incidents) == 0:
        print("No incidents to process. Exiting.")
        return

    # Process each incident
    escalated_count = 0
    failed_incidents = []

    for incident in filtered_incidents:
        incident_id = incident['id']
        incident_title = incident.get('title', 'N/A')

        try:
            # Get alerts for this incident
            alerts = get_incident_alerts(incident_id, token)

            # Check if any alert matches severity criteria
            matches, matched_severity = check_severity_match(alerts, severities)

            if matches:
                if dry_run:
                    print(f"[DRY RUN] Would escalate: {incident_id} - {incident_title}")
                    print(f"           Matched severity: {matched_severity}")
                else:
                    escalate_incident(incident_id, token, from_email)
                    print(f"✓ Escalated: {incident_id} - {incident_title}")
                    print(f"  Severity: {matched_severity}")

                escalated_count += 1

        except Exception as e:
            print(f"✗ Failed: {incident_id} - {e}")
            failed_incidents.append(incident_id)

    # Summary
    print()
    print("=" * 50)
    print("Summary:")
    if dry_run:
        print(f"  - Would escalate {escalated_count} incident(s)")
    else:
        print(f"  - Escalated {escalated_count} incident(s)")

    if failed_incidents:
        print(f"  - Failed to process {len(failed_incidents)} incident(s): {', '.join(failed_incidents)}")
    else:
        print(f"  - No failures")

    print("=" * 50)


if __name__ == '__main__':
    main()
