const BASE = "/api";

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, options);
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${detail}`);
  }
  return res.json();
}

export function uploadDocument(file) {
  const formData = new FormData();
  formData.append("file", file);
  return request("/documents/upload", { method: "POST", body: formData });
}

export function getDocumentStatus(documentId) {
  return request(`/documents/${documentId}/status`);
}

export function getDocumentDetail(documentId) {
  return request(`/documents/${documentId}`);
}

export function deleteDocument(documentId) {
  return request(`/documents/${documentId}`, { method: "DELETE" });
}

export function confirmExtraction(documentId, documentType, fields) {
  return request(`/documents/${documentId}/confirm`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ document_type: documentType, fields }),
  });
}

export function listDocuments() {
  return request("/documents");
}

export function askQuestion(question) {
  return request("/qa/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
}

export function getSystemMode() {
  return request("/system/mode");
}
