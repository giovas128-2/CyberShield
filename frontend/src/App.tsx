import { useState } from "react";
import { HashRouter, Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { Login } from "./pages/Login";
import { Register } from "./pages/Register";
import { Console } from "./layout/Console";
import type { User } from "./types";
const readUser=():User|null=>{try{return JSON.parse(localStorage.getItem("cs_user")||"null");}catch{return null;}};
function RegisterRoute(){const nav=useNavigate();return <Register goLogin={()=>nav('/login')} onDone={()=>nav('/login',{state:{notice:'Cuenta creada. Inicia sesión para continuar.'}})}/>;}
function LoginRoute({onUser}:{onUser:(u:User)=>void}){const nav=useNavigate();const {state}=useLocation();return <Login notice={(state as any)?.notice} goRegister={()=>nav('/register')} onLogin={(u)=>{onUser(u);nav('/dashboard');}}/>;}
export default function App(){const [user,setUser]=useState<User|null>(readUser());const saveUser=(u:User)=>{localStorage.setItem('cs_user',JSON.stringify(u));setUser(u);};const logout=()=>{localStorage.removeItem('cs_token');localStorage.removeItem('cs_user');setUser(null);};return <div className="cs"><HashRouter><Routes><Route path="/register" element={<RegisterRoute/>}/><Route path="/login" element={<LoginRoute onUser={saveUser}/>}/><Route path="/dashboard" element={user?<Console user={user} onLogout={logout}/>:<Navigate to="/login" replace/>}/><Route path="*" element={<Navigate to={user?'/dashboard':'/register'} replace/>}/></Routes></HashRouter></div>;}
