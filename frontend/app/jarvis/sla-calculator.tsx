"use client";
import { useState } from "react";
import { slaPercentage } from "../../lib/metrics";

export default function SlaCalculator() {
  const [total, setTotal] = useState("");
  const [onTime, setOnTime] = useState("");
  const [value, setValue] = useState<number | null>(null);
  const [error, setError] = useState("");
  return <details className="j-calculator">
    <summary>Calcular SLA com quantidades informadas</summary>
    <p>Informe os valores para conferir o cálculo. Este formulário não consulta o banco.</p>
    <form onSubmit={e => {
      e.preventDefault(); setError("");
      try {
        if (!total.trim() || !onTime.trim()) throw new Error("Preencha as duas quantidades.");
        setValue(slaPercentage(Number(onTime), Number(total)));
      } catch (err) { setValue(null); setError((err as Error).message); }
    }}>
      <label>Total de remessas avaliadas<input inputMode="numeric" type="number" min="1" step="1" required value={total} onChange={e => {setTotal(e.target.value);setValue(null);}} /></label>
      <label>Remessas no prazo<input inputMode="numeric" type="number" min="0" step="1" required value={onTime} onChange={e => {setOnTime(e.target.value);setValue(null);}} /></label>
      <button type="submit">Calcular no sistema</button>
    </form>
    {value !== null && <p role="status"><strong>SLA: {value.toLocaleString("pt-BR", { maximumFractionDigits: 2 })}%</strong> · Calculado pelo código: no prazo ÷ total × 100.</p>}
    {error && <p role="alert">{error}</p>}
  </details>;
}
