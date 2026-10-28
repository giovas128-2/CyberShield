import { ED_BARS, ED_REPORTS } from "../../empresademo/fixtures";

export default function EDReportes() {
  const max = Math.max(...ED_BARS);
  return (
    <>
      <div className="ed-h"><div><div className="ed-eyebrow">EmpresaDemo / Corporativo</div><h1>Una mirada más amplia.</h1><div className="ed-sub">Actividad del espacio y seguimiento del trabajo. Cifras ilustrativas, sin conexión a datos reales.</div></div>
        <span className="ed-tag">Periodo · Octubre 2026</span></div>
      <div className="ed-grid4">
        {[["Documentos actualizados", "38", "En el periodo · Actividad ficticia"], ["Revisiones completadas", "26", "68 % del total de la muestra"], ["Clientes con actividad", "16", "De 24 clientes ficticios"], ["Reportes disponibles", "06", "Consultados hoy: 1"]].map(([l, v, h]) => (
          <div className="ed-card ed-kpi" key={l}><small>{l}</small><b>{v}</b><small>{h}</small></div>))}
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "minmax(0,1fr) minmax(0,2fr)", gap: 16 }} className="ed-rep-cols">
        <div className="ed-card"><div className="ed-h"><h3>Actividad documental</h3><small className="ed-mu">Actualizaciones / día</small></div>
          <div className="ed-bars" role="img" aria-label="Gráfico ilustrativo de actualizaciones de documentos del 1 al 20 de octubre">{ED_BARS.map((v, i) => <i key={i} style={{ height: `${(v / max) * 100}%` }} title={`${v}`} />)}</div>
          <small className="ed-foot-note">Distribución ilustrativa del 1 al 20 de octubre. No representa productividad real.</small></div>
        <div className="ed-card"><div className="ed-h"><h3>Resumen del equipo</h3><small className="ed-mu">REP-006</small></div>
          <h2 className="serif" style={{ fontSize: 26, margin: "6px 0" }}>Octubre, en perspectiva.</h2>
          <p className="ed-mu">La muestra concentra actividad en propuestas y resúmenes de servicio. Hay dos documentos pendientes de revisión en el espacio actual.</p>
          <span className="ed-tag">Última consulta · Hoy 09:30</span>
          <p className="ed-mu" style={{ fontSize: 13 }}>Analista Demo · Dispositivo de confianza<br />Origen: DEMO · Generado como fixture</p></div>
      </div>
      <div className="ed-card"><div className="ed-h"><h3>Biblioteca de reportes</h3><small className="ed-mu">6 disponibles · 3 destacados</small></div>
        <div className="ed-tw" style={{ marginTop: 8 }}><table><thead><tr><th>Reporte / referencia</th><th>Periodo</th><th>Contenido</th><th>Estado</th><th>Última consulta</th></tr></thead>
          <tbody>{ED_REPORTS.map((r) => <tr key={r.code}><td>{r.name} · {r.code}</td><td>{r.period}</td><td>{r.content}</td><td><b>Disponible</b></td><td>{r.last}</td></tr>)}</tbody></table></div></div>
    </>
  );
}
