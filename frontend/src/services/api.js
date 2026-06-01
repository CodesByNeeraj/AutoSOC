//base url for the backend
const BASE_URL = 'http://127.0.0.1:8000/api'

//submit a new alert for analysis
export const analyseAlert = async (rawLog, source = 'manual') => {
  const response = await fetch(`${BASE_URL}/analyse`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ raw_log: rawLog, source })
  })
  if (!response.ok) throw new Error('analysis failed')
  return response.json()
}

//get all incidents
export const getIncidents = async () => {
  const response = await fetch(`${BASE_URL}/incidents`)
  if (!response.ok) throw new Error('failed to fetch incidents')
  return response.json()
}

//get single incident
export const getIncident = async (id) => {
  const response = await fetch(`${BASE_URL}/incidents/${id}`)
  if (!response.ok) throw new Error('failed to fetch incident')
  return response.json()
}

//get findings for an incident
export const getFindings = async (id) => {
  const response = await fetch(`${BASE_URL}/incidents/${id}/findings`)
  if (!response.ok) throw new Error('failed to fetch findings')
  return response.json()
}

//get report for an incident
export const getReport = async (id) => {
  const response = await fetch(`${BASE_URL}/incidents/${id}/report`)
  if (!response.ok) throw new Error('failed to fetch report')
  return response.json()
}

//get dashboard stats
export const getStats = async () => {
  const response = await fetch(`${BASE_URL}/stats`)
  if (!response.ok) throw new Error('failed to fetch stats')
  return response.json()
}

//manually resolve or reopen an incident
export const updateIncidentStatus = async (id, status) => {
  const response = await fetch(`${BASE_URL}/incidents/${id}/status`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status })
  })
  if (!response.ok) throw new Error('failed to update status')
  return response.json()
}