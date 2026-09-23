import { request } from './client'

export const listTeams = () => request('/teams')
