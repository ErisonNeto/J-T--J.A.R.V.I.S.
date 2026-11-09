export function slaPercentage(onTime: number, total: number): number {
  if (!Number.isSafeInteger(onTime) || !Number.isSafeInteger(total) || total <= 0 || onTime < 0 || onTime > total) {
    throw new Error("Informe quantidades inteiras: total maior que zero e no prazo entre zero e o total.");
  }
  return Math.round((onTime / total) * 10000) / 100;
}
