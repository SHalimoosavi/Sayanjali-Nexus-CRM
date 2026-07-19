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

export const convertLeadToClient = async (leadId: string) => {
  const { data } = await api.post(`/clients/convert-lead/${leadId}`);
  return data;
};

export const updateLead = async (id: string, payload: Partial<Lead>) => {
  const { data } = await api.patch(`/leads/${id}`, payload);
  return data as Lead;
};

export interface LeadNote {
  id: string;
  note: string;
  created_by?: string;
  created_at: string;
}

export interface LeadActivity {
  id: string;
  activity_type: string;
  description?: string;
  created_at: string;
}

export const fetchLeadNotes = async (leadId: string): Promise<LeadNote[]> => {
  const { data } = await api.get(`/leads/${leadId}/notes`);
  return data;
};

export const addLeadNote = async (leadId: string, note: string): Promise<LeadNote> => {
  const { data } = await api.post(`/leads/${leadId}/notes`, { note });
  return data;
};

export const fetchLeadTimeline = async (leadId: string): Promise<LeadActivity[]> => {
  const { data } = await api.get(`/leads/${leadId}/timeline`);
  return data;
};

export const bulkUpdateLeads = async (ids: string[], updates: Partial<Lead>) => {
  const { data } = await api.patch("/leads/bulk", { ids, updates });
  return data as { affected: number; not_found: string[] };
};

export const bulkDeleteLeads = async (ids: string[]) => {
  const { data } = await api.post("/leads/bulk-delete", { ids });
  return data as { affected: number; not_found: string[] };
};

export const importLeadsCSV = async (verticalId: string, file: File) => {
  const form = new FormData();
  form.append("vertical_id", verticalId);
  form.append("file", file);
  const { data } = await api.post("/leads/import", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data as { created: number; skipped_duplicates: number; errors: string[] };
};

export const exportLeadsCSV = async (verticalId?: string) => {
  const response = await api.get("/leads/export", {
    params: verticalId ? { vertical_id: verticalId } : {},
    responseType: "blob",
  });
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement("a");
  link.href = url;
  link.download = "leads_export.csv";
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};
