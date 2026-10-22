def analyze_security_event(event):
    event_type = event.event_type
    details = event.details or {}

    severity = "normal"
    create_incident = False
    scope = getattr(event, "scope", None)

    # ==========================================================
    # 1. AUTENTICACIÓN
    # ==========================================================
    if event_type in (
        "authentication_failure",
        "multiple_login_attempts",
        "authentication_burst",
    ):
        attempts = details.get("attempts", 1)
        time_window = details.get("time_window_seconds", 60)
        distinct_users = details.get("distinct_users", 1)

        successful_login = details.get("successful_login", False)
        unauthorized_access = details.get("unauthorized_access", False)
        privilege_escalation = details.get("privilege_escalation", False)

        # Fallo aislado o pocos errores:
        # se guarda, pero NO se considera ataque automáticamente.
        if attempts <= 3:
            severity = "normal"
            create_incident = False

        # Actividad anormal que merece observación.
        elif attempts > 3:
            severity = "warning"
            create_incident = False

        # Patrón más fuerte:
        # mismo origen atacando múltiples cuentas en poco tiempo.
        if (
            attempts >= 10
            and time_window <= 60
            and distinct_users >= 3
        ):
            severity = "high"
            create_incident = True

        # No basta con volumen para declarar CRITICAL.
        # Debe existir evidencia adicional de impacto.
        if (
            successful_login
            and (
                unauthorized_access
                or privilege_escalation
            )
        ):
            severity = "critical"
            create_incident = True
            scope = "IMPACT"

        # Si no vino scope desde el sensor/simulador,
        # proponemos uno únicamente cuando hay evidencia suficiente.
        if scope is None:
            if severity == "normal":
                scope = "BLOCKED"
            elif severity in ("warning", "high"):
                scope = "REACHED"

    # ==========================================================
    # 2. CAMBIO EN ARCHIVO CRÍTICO
    # ==========================================================
    elif event_type == "suspicious_file_change":
        authorized = details.get("authorized", True)
        criticality = details.get("file_criticality", "common")
        change_applied = details.get("change_applied", False)

        if authorized:
            severity = "normal"
            create_incident = False

            if change_applied and scope is None:
                scope = "IMPACT"

        else:
            if criticality == "critical":
                severity = "high"
                create_incident = True

            elif criticality == "important":
                severity = "high"
                create_incident = True

            else:
                severity = "warning"

            if change_applied:
                scope = "IMPACT"

                # Si además hay evidencia de compromiso,
                # entonces sí sube a CRITICAL.
                if details.get("compromise_confirmed", False):
                    severity = "critical"
                    create_incident = True

            elif scope is None:
                scope = "BLOCKED"
    # ==========================================================
    # 2. ACCESO ADMINISTRATIVO DESDE ORIGEN NO AUTORIZADO
    # ==========================================================
    elif event_type == "unauthorized_admin_login":
        attempts = details.get("attempts", 1)
        time_window = details.get(
            "time_window_seconds",
            60,
        )

        credentials_valid = details.get(
            "credentials_valid",
            False,
        )

        origin_authorized = details.get(
            "origin_authorized",
            True,
        )

        admin_protected = details.get(
            "admin_protected",
            False,
        )

        # Credenciales válidas, pero la política de origen
        # impidió el acceso administrativo.
        if (
            credentials_valid
            and not origin_authorized
            and admin_protected
        ):
            severity = "warning"
            create_incident = False
            scope = "BLOCKED"

        # Repetición del mismo comportamiento en poco tiempo.
        # El acceso continúa bloqueado, pero el patrón
        # ya merece abrir un incidente.
        if (
            attempts >= 5
            and time_window <= 60
        ):
            severity = "high"
            create_incident = True
            scope = "BLOCKED"
    # ==========================================================
    # 3. TRÁFICO / CONEXIÓN SOSPECHOSA
    # ==========================================================
    elif event_type in (
        "suspicious_network_traffic",
        "unusual_external_connection",
    ):
        requests = details.get("requests", 0)
        time_window = details.get("time_window_seconds", 60)

        destination_allowed = details.get(
            "destination_allowed",
            True,
        )

        impact_confirmed = details.get(
            "impact_confirmed",
            False,
        )

        # Una conexión externa o volumen aislado
        # no es automáticamente un ataque.
        if destination_allowed:
            severity = "normal"

        else:
            severity = "warning"

        # Patrón anormal sostenido.
        # Estos valores son PROVISIONALES para laboratorio.
        if (
            not destination_allowed
            and requests >= 100
            and time_window <= 60
        ):
            severity = "high"
            create_incident = True

        # CRITICAL requiere evidencia de impacto.
        if impact_confirmed:
            severity = "critical"
            create_incident = True
            scope = "IMPACT"

        elif scope is None:
            if details.get("blocked", False):
                scope = "BLOCKED"
            else:
                scope = "REACHED"
    # ==========================================================
    # 3. ELEVACIÓN / ABUSO DE PRIVILEGIOS
    # ==========================================================
    elif event_type == "privilege_escalation":
        sudo_used = bool(
            details.get(
                "sudo_used",
                details.get("sudo", False),
            )
        )

        authorized = details.get(
            "authorized",
            True,
        )

        success = details.get(
            "success",
            False,
        )

        compromise_confirmed = details.get(
            "compromise_confirmed",
            False,
        )

        # Un evento genérico sin evidencia suficiente
        # queda para observación, sin declarar incidente.
        if not sudo_used:
            severity = "warning"
            create_incident = False

            if scope is None:
                scope = "REACHED"

        # sudo legítimo/autorizado.
        elif authorized:
            severity = "normal"
            create_incident = False

            if scope is None:
                scope = (
                    "IMPACT"
                    if success
                    else "BLOCKED"
                )

        # Intento de sudo no autorizado que no tuvo éxito.
        elif not success:
            severity = "warning"
            create_incident = False
            scope = "BLOCKED"

        # sudo no autorizado y exitoso.
        else:
            severity = "high"
            create_incident = True
            scope = "IMPACT"

            # CRITICAL exige evidencia adicional
            # de compromiso confirmado.
            if compromise_confirmed:
                severity = "critical"
    # ==========================================================
    # EVENTOS AÚN SIN REGLA ESPECÍFICA
    # ==========================================================
    else:
        severity = "normal"
        create_incident = False

    return {
        "detected": severity != "normal",
        "create_incident": create_incident,
        "risk_level": severity,
        "scope": scope,
    }