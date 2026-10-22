import type { AgentRequest, AgentResponse, ApiErrorBody } from '../types'

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '')

async function errorMessage(response: Response): Promise<string> {
  const body = await response.json().catch(() => null) as ApiErrorBody | null
  const detail = body?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail.map((error) => error.msg || 'Invalid request').join('; ')
  if (detail && typeof detail === 'object') {
    const summary = detail.summary
    if (typeof summary === 'string') return summary
    return `The server returned ${response.status} ${response.statusText}.`
  }
  return `Request failed with ${response.status} ${response.statusText}.`
}

export async function createDocument(payload: AgentRequest): Promise<AgentResponse> {
  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}/agent`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
  } catch {
    throw new Error(`Could not reach the document agent at ${API_BASE_URL}. Check that the API is running and CORS allows this origin.`)
  }

  if (!response.ok) throw new Error(await errorMessage(response))
  try {
    return await response.json() as AgentResponse
  } catch {
    throw new Error('The API returned an invalid response. Please try again.')
  }
}

function getFilename(response: Response, documentId: string): string {
  const disposition = response.headers.get('content-disposition') || ''
  const encoded = disposition.match(/filename\*=UTF-8''([^;]+)/i)?.[1]
  if (encoded) return decodeURIComponent(encoded)
  const plain = disposition.match(/filename="?([^";]+)"?/i)?.[1]
  return plain || `${documentId}.docx`
}

export async function downloadDocument(result: AgentResponse): Promise<void> {
  const path = result.download_url || (result.document_id ? `/documents/${encodeURIComponent(result.document_id)}` : null)
  if (!path) throw new Error('The response did not include a document download link.')

  let response: Response
  try {
    response = await fetch(new URL(path, `${API_BASE_URL}/`))
  } catch {
    throw new Error('Could not connect to the document download endpoint. Check that the API is running and CORS allows this origin.')
  }
  if (!response.ok) throw new Error(await errorMessage(response))
  const blob = await response.blob()
  if (!blob.size) throw new Error('The downloaded document was empty.')

  const filename = getFilename(response, result.document_id || 'document')
  const objectUrl = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = objectUrl
  anchor.download = filename
  document.body.append(anchor)
  anchor.click()
  anchor.remove()
  window.setTimeout(() => URL.revokeObjectURL(objectUrl), 1000)
}
