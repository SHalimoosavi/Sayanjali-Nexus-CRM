import { api } from "./client";

export interface Project {
  id: string;
  vertical_id: string;
  client_id?: string;
  name: string;
  description?: string;
  status: string;
  progress_percent: number;
  budget?: number;
  start_date?: string;
  due_date?: string;
  created_at: string;
}

export interface Task {
  id: string;
  project_id?: string;
  title: string;
  description?: string;
  status: string;
  priority: string;
  assignee_id?: string;
  due_date?: string;
}

export const fetchProjects = async (params: { page?: number; page_size?: number; client_id?: string; status?: string }) => {
  const { data } = await api.get("/projects", { params });
  return data as { total: number; page: number; page_size: number; items: Project[] };
};

export const createProject = async (payload: Partial<Project>) => {
  const { data } = await api.post("/projects", payload);
  return data as Project;
};

export const fetchTasks = async (params: { project_id?: string; status?: string }) => {
  const { data } = await api.get("/tasks", { params: { ...params, page_size: 100 } });
  return data as { total: number; items: Task[] };
};

export const createTask = async (payload: Partial<Task>) => {
  const { data } = await api.post("/tasks", payload);
  return data as Task;
};

export const updateTask = async (id: string, payload: Partial<Task>) => {
  const { data } = await api.patch(`/tasks/${id}`, payload);
  return data as Task;
};

export const deleteTask = async (id: string) => {
  await api.delete(`/tasks/${id}`);
};
