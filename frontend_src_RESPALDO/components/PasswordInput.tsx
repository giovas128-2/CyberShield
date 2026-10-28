import { useState } from "react";
import { Eye, EyeOff } from "lucide-react";

export function PasswordInput({ value = "", onChange, onBlur, state = "", placeholder }: { value?: string; onChange?: (e: any) => void; onBlur?: () => void; state?: string; placeholder?: string }) {
  const [show, setShow] = useState(false);
  return <div className={`inp ${state}`}><input type={show ? "text" : "password"} value={value} onChange={onChange} onBlur={onBlur} placeholder={placeholder} /><button type="button" onClick={() => setShow(!show)} aria-label="Mostrar contraseña">{show ? <EyeOff size={16} /> : <Eye size={16} />}</button></div>;
}
