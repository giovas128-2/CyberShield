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
        sensor_confirmed_bruteforce = bool(
            details.get(
                "sensor_confirmed_bruteforce",
                False,
            )
        )
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
                
        if sensor_confirmed_bruteforce:
            severity = "high"
            create_incident = True

            if scope != "IMPACT":
                scope = "REACHED"
        # ==========================================================
    # 2. DEVICE TRUST / DISPOSITIVO NO AUTORIZADO
    # ==========================================================
    elif event_type == "unauthorized_device_access":
        auth_result = details.get("auth_result", "success")
        device_state = details.get("device_state", "unregistered")

        # Este control aplica cuando las credenciales fueron aceptadas.
        if auth_result != "success":
            severity = "normal"
            create_incident = False

            if scope is None:
                scope = "BLOCKED"

        elif device_state == "trusted":
            severity = "normal"
            create_incident = False

            if scope is None:
                scope = "REACHED"

        elif device_state == "untrusted":
            severity = "warning"
            create_incident = False

            if scope is None:
                scope = "REACHED"

        elif device_state == "unregistered":
            severity = "high"
            create_incident = True

            if scope is None:
                scope = "BLOCKED"

        elif device_state == "revoked":
            severity = "critical"
            create_incident = True

            if scope is None:
                scope = "BLOCKED"

        else:
            severity = "warning"
            create_incident = False

            if scope is None:
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
        "unusual_outbound_connection",
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
    # 4. POSIBLE EXFILTRACIÓN DE DATOS
    # ==========================================================
    elif event_type == "possible_data_exfiltration":
        bytes_up = int(
            details.get(
                "bytes_toserver_total",
                details.get("bytes_toserver", 0),
            )
        )

        bytes_down = int(
            details.get(
                "bytes_toclient_total",
                details.get("bytes_toclient", 0),
            )
        )

        dest_class = details.get("dest_class", "external")

        bulk_data_access = bool(
            details.get("bulk_data_access", False)
        )

        prior_open_incident = bool(
            details.get("prior_open_incident", False)
        )

        untrusted_session_device = bool(
            details.get("untrusted_session_device", False)
        )

        off_hours = bool(
            details.get("off_hours", False)
        )

        upload_ratio = bytes_up / max(1, bytes_down)
        upload_heavy = upload_ratio >= 5

        # Umbrales de volumen definidos para OLA 3:
        # 10 MB WARNING, 50 MB HIGH, 100 MB CRITICAL.
        if bytes_up >= 100_000_000:
            severity = "critical"

        elif bytes_up >= 50_000_000:
            severity = "high"

        elif bytes_up >= 10_000_000:
            severity = "warning"

        else:
            severity = "normal"

        strong = sum(
            [
                bulk_data_access,
                prior_open_incident,
                untrusted_session_device,
            ]
        )

        weak = sum(
            [
                off_hours,
                upload_heavy,
            ]
        )

        # Cada indicador fuerte eleva un nivel.
        for _ in range(min(strong, 2)):
            if severity == "normal":
                severity = "warning"
            elif severity == "warning":
                severity = "high"
            elif severity == "high":
                severity = "critical"

        # Dos indicadores débiles juntos elevan un nivel.
        if weak >= 2:
            if severity == "normal":
                severity = "warning"
            elif severity == "warning":
                severity = "high"
            elif severity == "high":
                severity = "critical"

        # Destino interno no habitual sin acceso masivo previo:
        # la severidad queda limitada a HIGH.
        if (
            dest_class == "internal_unknown"
            and not bulk_data_access
            and severity == "critical"
        ):
            severity = "high"

        create_incident = severity in (
            "high",
            "critical",
        )

        if scope is None:
            scope = (
                "REACHED"
                if severity != "normal"
                else "BLOCKED"
            )
    # ==========================================================
    # 5. POSIBLE COMPORTAMIENTO TIPO RANSOMWARE
    # ==========================================================
    elif event_type == "possible_ransomware_behavior":
        modified_files = int(
            details.get("modified_files", 0)
        )

        renamed_files = int(
            details.get("renamed_files", 0)
        )

        suspicious_extension = bool(
            details.get("suspicious_extension", False)
        )

        maintenance_mode = bool(
            details.get("maintenance_mode", False)
        )

        sensor_confirmed_ransomware_like = bool(
            details.get(
                "sensor_confirmed_ransomware_like",
                False,
            )
        )

        lab_ransomware_signal = bool(
            details.get(
                "lab_ransomware_signal",
                False,
            )
        )

        # Umbrales PROVISIONALES para laboratorio.
        # No se cifra ni destruye información real.
        if maintenance_mode:
            severity = "normal"
            create_incident = False

        # Wazuh FIM confirmó un cambio real dentro de la carpeta
        # dedicada exclusivamente al simulador ransomware-like.
        elif (
            sensor_confirmed_ransomware_like
            and lab_ransomware_signal
        ):
            severity = "high"
            create_incident = True
            scope = "IMPACT"

        elif modified_files >= 100 and renamed_files >= 50:
            severity = "critical"
            create_incident = True

        elif modified_files >= 50:
            severity = "high"
            create_incident = True

        elif modified_files >= 10:
            severity = "warning"
            create_incident = False

        else:
            severity = "normal"
            create_incident = False

        # Refuerza la señal si además aparece un patrón
        # de extensión anómala en archivos ficticios.
        if (
            suspicious_extension
            and severity == "warning"
        ):
            severity = "high"
            create_incident = True

        elif (
            suspicious_extension
            and severity == "high"
        ):
            severity = "critical"
            create_incident = True

        if scope is None:
            scope = (
                "IMPACT"
                if severity in ("high", "critical")
                else "REACHED"
            )
    # ==========================================================
    # 6. POSIBLE MOVIMIENTO LATERAL
    # ==========================================================
    elif event_type == "possible_lateral_movement":
        protocol = str(
            details.get("protocol", "")
        ).lower()

        login_successful = bool(
            details.get("login_successful", False)
        )

        pair_authorized = bool(
            details.get("pair_authorized", False)
        )

        maintenance_mode = bool(
            details.get("maintenance_mode", False)
        )

        prior_open_incident = bool(
            details.get("prior_open_incident", False)
        )

        # Regla PROVISIONAL para laboratorio.
        # Una conexión SSH autorizada no se considera incidente.
        if maintenance_mode:
            severity = "normal"
            create_incident = False
            scope = "REACHED"

        elif protocol != "ssh":
            severity = "normal"
            create_incident = False
            scope = "REACHED"

        elif pair_authorized:
            severity = "normal"
            create_incident = False
            scope = "REACHED"

        elif not login_successful:
            severity = "warning"
            create_incident = False
            scope = "BLOCKED"

        else:
            # SSH exitoso entre un par no autorizado/no habitual.
            severity = "high"
            create_incident = True
            scope = "REACHED"

            # Contexto adicional fuerte.
            if prior_open_incident:
                severity = "critical"
                create_incident = True
                scope = "IMPACT"
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