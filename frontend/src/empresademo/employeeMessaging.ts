import { affects, type ModuleId, type Phase, type Scenario } from "./incident";

/**
 * Capa de presentación para el empleado.
 *
 * Regla de diseño: EmpresaDemo no muestra técnica MITRE, severidad, IP de origen,
 * nombres de acciones defensivas, comandos, estados técnicos del SOC ni causa interna.
 * Solo comunica impacto operativo, disponibilidad y siguiente acción útil.
 *
 * Fundamento de diseño del proyecto (alineación, no certificación):
 * - NIST SP 800-53 SI-11: mensajes de usuario útiles sin revelar detalle explotable.
 * - NIST SP 800-53 AC-6: mínimo privilegio / información según rol.
 * - NIST CSF 2.0 + NIST SP 800-61r3: respuesta y comunicación a partes designadas.
 * - OWASP: mensajes de error genéricos para usuario; detalle técnico en logs/soporte.
 */

export type EmployeeTone = "warn" | "info" | "ok" | "bad";
export interface EmployeeMessage {
  title: string;
  body: string;
  label: string;
  tone: EmployeeTone;
  support?: boolean;
}

type Active = Exclude<Phase, "NORMAL">;

const MODULE_NAME: Record<ModuleId, string> = {
  accesos: "Acceso a la cuenta",
  clientes: "Clientes",
  documentos: "Documentos",
  reportes: "Reportes y exportaciones",
  administracion: "Administración",
  perfil: "Perfil y sesiones",
};

const RESTRICTED_BODY: Record<ModuleId, string> = {
  accesos: "Algunas acciones de acceso pueden requerir una nueva verificación. Siga las indicaciones que aparezcan en pantalla.",
  clientes: "Puede seguir consultando la información disponible. Algunas acciones de edición o exportación pueden estar temporalmente no disponibles.",
  documentos: "Puede seguir consultando los documentos disponibles. Las acciones afectadas aparecerán deshabilitadas hasta que finalice la verificación.",
  reportes: "Puede seguir consultando reportes ya disponibles. Algunas opciones de exportación, descarga o uso compartido pueden estar temporalmente restringidas.",
  administracion: "Esta área puede no estar disponible para su cuenta. Si necesita una función administrativa, contacte a soporte interno.",
  perfil: "Puede seguir consultando su perfil. Algunas acciones de cuenta pueden requerir una nueva verificación antes de continuar.",
};

const AVAILABLE_BODY: Record<ModuleId, string> = {
  accesos: "Puede continuar con el acceso autorizado de su cuenta.",
  clientes: "La consulta de clientes continúa disponible según los permisos de su cuenta.",
  documentos: "Las funciones disponibles de documentos pueden utilizarse nuevamente según su rol.",
  reportes: "Las funciones disponibles de reportes pueden utilizarse nuevamente según su rol.",
  administracion: "La disponibilidad de esta área continúa dependiendo de los permisos asignados a su cuenta.",
  perfil: "Las funciones disponibles de su cuenta pueden utilizarse nuevamente según su rol.",
};

export function employeeMessage(sc: Scenario, phase: Active, module: ModuleId, global = false): EmployeeMessage {
  const hit = affects(sc, module);
  const moduleName = MODULE_NAME[module];

  if (global && !hit) {
    if (phase === "CONTAINED") return {
      title: "Verificación finalizada",
      body: "Algunas funciones se han restablecido. La disponibilidad final depende de los permisos de su cuenta.",
      label: "Actualizado",
      tone: "ok",
    };
    if (phase === "FAILED") return {
      title: "Algunas funciones continúan restringidas",
      body: "Puede seguir utilizando las opciones disponibles. Si necesita una función restringida, contacte a soporte interno.",
      label: "Acceso limitado",
      tone: "warn",
      support: true,
    };
    return {
      title: "Algunas funciones están temporalmente restringidas",
      body: "Puede continuar utilizando las funciones disponibles. Las acciones afectadas se indican en cada módulo.",
      label: phase === "DETECTED" ? "Verificando" : "Acceso limitado",
      tone: phase === "DETECTED" ? "info" : "warn",
    };
  }

  if (!hit) {
    return {
      title: `${moduleName} disponible`,
      body: AVAILABLE_BODY[module],
      label: "Disponible",
      tone: "ok",
    };
  }

  if (phase === "DETECTED") {
    return {
      title: `Estamos verificando una operación en ${moduleName.toLowerCase()}`,
      body: "Puede continuar con su trabajo. Si alguna acción requiere verificación adicional, la interfaz se lo indicará.",
      label: "Verificando",
      tone: "info",
    };
  }

  if (phase === "LOCKDOWN" || phase === "RESPONDING") {
    return {
      title: `${moduleName}: función temporalmente restringida`,
      body: RESTRICTED_BODY[module],
      label: "Acceso limitado",
      tone: "warn",
    };
  }

  if (phase === "CONTAINED") {
    return {
      title: `${moduleName}: verificación finalizada`,
      body: AVAILABLE_BODY[module],
      label: "Actualizado",
      tone: "ok",
    };
  }

  return {
    title: `${moduleName}: la restricción continúa activa`,
    body: `${RESTRICTED_BODY[module]} Si necesita continuar con esta operación, contacte a soporte interno.`,
    label: "Acceso limitado",
    tone: "warn",
    support: true,
  };
}

export function summaryMessage(phase: Active): EmployeeMessage {
  if (phase === "DETECTED") return {
    title: "Estamos verificando una operación",
    body: "Puede continuar trabajando normalmente. Si alguna función necesita una verificación adicional, se indicará en el módulo correspondiente.",
    label: "Verificando",
    tone: "info",
  };
  if (phase === "CONTAINED") return {
    title: "Verificación finalizada",
    body: "Las funciones disponibles se han actualizado. Puede continuar trabajando según los permisos de su cuenta.",
    label: "Actualizado",
    tone: "ok",
  };
  if (phase === "FAILED") return {
    title: "Algunas funciones continúan temporalmente restringidas",
    body: "Puede continuar consultando la información disponible. Si necesita una función restringida, contacte a soporte interno.",
    label: "Acceso limitado",
    tone: "warn",
    support: true,
  };
  return {
    title: "Algunas funciones están temporalmente restringidas",
    body: "Puede continuar consultando la información disponible. Las acciones afectadas se indican en cada módulo.",
    label: "Acceso limitado",
    tone: "warn",
  };
}
