import { api } from "./client";

export interface Lead {
  id: string;
  vertical_id: string;
  full_name: string;
  company_name?: string;
  phone?: string;
  email?: string;
  stage: string;
  priority: string;
  score: number;
  expected_value?: number;
  is_converted: boolean;
  created_at: string;
}

export interface Vertical {
  id: string;
  name: string;
  slug: string;
  color: string;
  icon: string;
  pipeline_stages: string[];
}

export const fetchVerticals = async (): Promise<Vertical[]> => {
  const { data } = await api.get("/verticals");
  return data;
};

export const fetchLeads = async (params: {
  page?: number; page_size?: number; vertical_id?: string; stage?: string;
}) => {
  const { data } = await api.get("/leads", { params });
  return data as { total: number; page: number; page_size: number; items: Lead[] };
};

export const createLead = async (payload: Partial<Lead>) => {
  const { data } = await api.post("/leads", payload);
  return data as Lead;
};

export const updateLead = async (id: string, payload: Partial<Lead>) => {
  const { data } = await api.patch(`/leads/${id}`, payload);
  return data as Lead;
};
