INVESTIGATION_GUIDES = {
    "multiple_login_attempts": {
        "recommendation": (
            "Validar la IP de origen, el usuario y el horario. "
            "Si el origen no es reconocido, revisar sesiones activas, "
            "credenciales y accesos posteriores."
        ),
        "investigation_steps": [
            "Identificar la IP de origen.",
            "Revisar el usuario afectado.",
            "Comprobar la cantidad de intentos y la ventana de tiempo.",
            "Verificar si hubo un inicio de sesión exitoso posteriormente.",
            "Revisar logs de autenticación y actividad relacionada."
        ],
        "resolution_criteria": (
            "La actividad fue validada como legítima o se aplicó una "
            "mitigación autorizada y no se detectaron nuevos intentos anómalos."
        )
    },

    "suspicious_file_change": {
        "recommendation": (
            "Confirmar si la modificación estaba autorizada. "
            "Si no existe una explicación válida, revisar el proceso, "
            "usuario, hash y otros cambios relacionados."
        ),
        "investigation_steps": [
            "Identificar la ruta del archivo.",
            "Determinar el tipo de modificación.",
            "Revisar fecha y hora del cambio.",
            "Identificar usuario o proceso responsable.",
            "Comparar hash y permisos cuando estén disponibles.",
            "Buscar eventos relacionados."
        ],
        "resolution_criteria": (
            "El cambio fue validado como autorizado o fue mitigado/revertido "
            "y el archivo quedó en un estado esperado."
        )
    },

    "suspicious_network_traffic": {
        "recommendation": (
            "Validar si el destino y el servicio forman parte de la operación "
            "normal. Si el patrón es anormal, revisar el equipo de origen, "
            "el proceso responsable y los eventos relacionados."
        ),
        "investigation_steps": [
            "Revisar IP de origen y destino.",
            "Identificar puertos y protocolo.",
            "Comprobar frecuencia y duración del tráfico.",
            "Validar si el destino es habitual.",
            "Identificar el proceso o aplicación cuando sea posible.",
            "Revisar eventos del mismo host."
        ],
        "resolution_criteria": (
            "El tráfico fue validado como esperado o se aplicó una mitigación "
            "autorizada y ya no existen conexiones anómalas relacionadas."
        )
    }
}


DEFAULT_GUIDE = {
    "recommendation": (
        "Revisar el evento asociado y validar si la actividad está autorizada."
    ),
    "investigation_steps": [
        "Revisar los datos del evento.",
        "Validar el origen.",
        "Buscar actividad relacionada.",
        "Documentar los hallazgos."
    ],
    "resolution_criteria": (
        "El evento fue investigado y existe evidencia suficiente para "
        "considerarlo legítimo o mitigado."
    )
}


def get_investigation_guide(event_type: str):
    return INVESTIGATION_GUIDES.get(
        event_type,
        DEFAULT_GUIDE
    )