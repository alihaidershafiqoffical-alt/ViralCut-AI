export type TaskStatus = "pending" | "processing" | "completed" | "failed";

export interface Task {
  id: string;
  status: TaskStatus;
  progress: number; // 0-100
  videoTitle: string;
  originalUrl?: string;
  createdAt: string;
  completedAt?: string;
  outputUrls?: string[];
  error?: string;
  accessToken?: string;
}

export interface UploadResponse {
  taskId: string;
  message: string;
}

export interface TaskListResponse {
  tasks: Task[];
  total: number;
}
