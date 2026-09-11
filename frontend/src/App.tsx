import { Navigate, Route, Routes } from "react-router-dom";

import { NavBar } from "./components/NavBar";
import { Ficha } from "./pages/Ficha";
import { Funil } from "./pages/Funil";
import { Triagem } from "./pages/Triagem";

export function App() {
  return (
    <div className="min-h-screen bg-page text-ink">
      <NavBar />
      <Routes>
        <Route path="/" element={<Navigate to="/triagem" replace />} />
        <Route path="/triagem" element={<Triagem />} />
        <Route path="/funil" element={<Funil />} />
        <Route path="/imoveis/:loteId" element={<Ficha />} />
      </Routes>
    </div>
  );
}
