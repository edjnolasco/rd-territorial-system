export async function resolve(text, { timeout = 5000 } = {}) {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);

  let res;

  try {
    res = await fetch("http://localhost:8000/api/v1/resolve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
      signal: controller.signal,
    });
  } catch (err) {
    clearTimeout(id);
    throw new Error(`Error de red o timeout: ${err.message}`);
  }

  clearTimeout(id);

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Error en API (${res.status}): ${text}`);
  }

  const data = await res.json();

  // 👇 validación mínima del contrato
  if (!data.status) {
    throw new Error("Respuesta inválida: falta 'status'");
  }

  if (!data.catalog_version) {
    throw new Error("Respuesta inválida: falta 'catalog_version'");
  }

  return data;
}