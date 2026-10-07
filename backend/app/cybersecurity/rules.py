def analyze_security_event(event):
    event_type = event.event_type
    details = event.details

    severity = "normal"
    create_incident = False

    if event_type == "multiple_login_attempts":
        attempts = details.get("attempts", 0)
        time_window = details.get("time_window_seconds", 0)

        if time_window <= 30:
            if attempts >= 10:
                severity = "critical"
                create_incident = True

            elif attempts >= 7:
                severity = "high"
                create_incident = True

            elif attempts >= 4:
                severity = "warning"

            else:
                severity = "normal"

    elif event_type == "suspicious_file_change":
        authorized = details.get("authorized", True)
        criticality = details.get("file_criticality", "common")

        if not authorized:
            if criticality == "critical":
                severity = "critical"
                create_incident = True

            elif criticality == "important":
                severity = "high"
                create_incident = True

            else:
                severity = "warning"

    elif event_type == "suspicious_network_traffic":
        requests = details.get("requests", 0)
        time_window = details.get("time_window_seconds", 0)

        if time_window <= 30:
            if requests >= 500:
                severity = "critical"
                create_incident = True

            elif requests >= 200:
                severity = "high"
                create_incident = True

            elif requests >= 100:
                severity = "warning"

            else:
                severity = "normal"

    return {
        "detected": severity != "normal",
        "create_incident": create_incident,
        "risk_level": severity
    }