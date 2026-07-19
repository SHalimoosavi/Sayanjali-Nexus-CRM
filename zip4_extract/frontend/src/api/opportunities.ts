import { api } from "./client";

export interface Opportunity {
  id: string;
  vertical_id: string;
  client_id?: string;
  title: string;
  stage: string;
  value?: number;
  probability_percent: number;
  is_won?: boolean | null;
  expected_close_date?: string;
}

export const fetchOpportunities = async (params: { page?: number; page_size?: number; client_id?: string }) => {
  const { data } = await api.get("/opportunities", { params });
  return data as { total: number; page: number; page_size: number; items: Opportunity[]; open_value_total: number };
};

export const markWon = async (id: string) => {
  const { data } = await api.post(`/opportunities/${id}/mark-won`);
  return data as Opportunity;
};

export const markLost = async (id: string, reason?: string) => {
  const { data } = await api.post(`/opportunities/${id}/mark-lost`, null, { params: { reason } });
  return data as Opportunity;
};
