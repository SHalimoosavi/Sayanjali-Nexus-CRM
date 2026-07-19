import { api } from "./client";

export interface Contact {
  id: string;
  first_name: string;
  last_name?: string;
  email?: string;
  phone?: string;
  is_primary: boolean;
}

export interface Client {
  id: string;
  display_name: string;
  client_code?: string;
  status: string;
  account_owner_id?: string;
  notes?: string;
  created_at: string;
}

export interface ClientDetail extends Client {
  contacts: Contact[];
  vertical_ids: string[];
}

export const fetchClients = async (params: { page?: number; page_size?: number; status?: string }) => {
  const { data } = await api.get("/clients", { params });
  return data as { total: number; page: number; page_size: number; items: Client[] };
};

export const fetchClient = async (id: string): Promise<ClientDetail> => {
  const { data } = await api.get(`/clients/${id}`);
  return data;
};

export const createClient = async (payload: Partial<Client> & { vertical_ids?: string[] }) => {
  const { data } = await api.post("/clients", payload);
  return data as Client;
};

export const updateClient = async (id: string, payload: Partial<Client>) => {
  const { data } = await api.patch(`/clients/${id}`, payload);
  return data as Client;
};

export const addContact = async (clientId: string, payload: Partial<Contact>) => {
  const { data } = await api.post(`/clients/${clientId}/contacts`, payload);
  return data as Contact;
};
