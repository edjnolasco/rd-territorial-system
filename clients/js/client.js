export async function resolve(text) {
  const res = await fetch("http://localhost:8000/api/v1/resolve", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ text })
  });
  return res.json();
}