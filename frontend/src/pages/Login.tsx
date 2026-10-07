import { useState } from "react";
import { ArrowRight, Check, Loader2, ShieldCheck } from "lucide-react";
import { login, isNet } from "../api/client";
import { emailOk } from "../utils/format";
import { PasswordInput } from "../components/PasswordInput";
import { AuthShell } from "../components/AuthShell";
import type { User } from "../types";

export function Login({ onLogin, goRegister, notice }: { onLogin: (u: User) => void; goRegister: () => void; notice?: string }) {
  const [f,setF]=useState({email:"",password:""}); const [error,setError]=useState(""); const [loading,setLoading]=useState(false);
  const submit=async(e:any)=>{e.preventDefault(); if(loading)return; setError(""); if(!emailOk(f.email)||!f.password)return setError("Correo o contraseña incorrectos. Revisa tus datos."); setLoading(true); try { let data; try { data=await login(f); } catch(err){ if(!isNet(err)) throw err; const users=JSON.parse(localStorage.getItem("cs_users")||"[]"); const u=users.find((x:any)=>x.email===f.email&&x.password===f.password); if(!u) throw new Error("Correo o contraseña incorrectos. Revisa tus datos."); data={token:"demo",user:{name:u.name,email:u.email}}; } localStorage.setItem("cs_token",data.token); onLogin(data.user); } catch(err:any){ setError(err.message); } finally{ setLoading(false); }};
  return <AuthShell><form className="form" onSubmit={submit} noValidate><div className="eyebrow">Bienvenido a CyberShield</div><h2>Iniciar sesión</h2><p className="mu">Accede a tu consola y consulta el estado de seguridad de tu infraestructura.</p>{notice&&<div className="note" style={{color:"var(--ok)"}}><Check size={16}/>{notice}</div>}<label>Correo electrónico</label><div className="inp"><input type="email" placeholder="cesar@empresa.com" value={f.email} onChange={(e)=>setF({...f,email:e.target.value})}/></div><label>Contraseña</label><PasswordInput value={f.password} placeholder="Introduce tu contraseña" onChange={(e)=>setF({...f,password:e.target.value})}/><div className="hint">Usa las credenciales de tu cuenta CyberShield.</div>{error&&<div className="errbox"><b>No pudimos iniciar sesión</b>{error}</div>}<button className="btn" disabled={loading}>{loading?<><Loader2 size={16} className="spin"/>Iniciando sesión...</>:<><ArrowRight size={16}/>Iniciar sesión</>}</button><div className="foot mu">¿Aún no tienes una cuenta? <button type="button" className="lnk" onClick={goRegister}>Crear cuenta</button></div><div className="note"><ShieldCheck size={16}/>Solo usuarios autorizados. La actividad de acceso puede registrarse por seguridad.</div></form></AuthShell>;
}
