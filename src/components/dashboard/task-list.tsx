"use client";

import { TaskCard } from "./task-card";
import type { Task } from "@/types/task";
import { Loader2, Inbox } from "lucide-react";

interface TaskListProps {
  title: string;
  tasks: Task[];
  isLoading?: boolean;
  emptyMessage?: string;
}

export function TaskList({
  title,
  tasks,
  isLoading = false,
  emptyMessage = "No tasks yet",
}: TaskListProps) {
  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
          {title}
          {tasks.length > 0 && (
            <span className="ml-2 inline-flex items-center justify-center h-5 min-w-[20px] rounded-full bg-white/5 px-1.5 text-[10px] font-medium text-foreground">
              {tasks.length}
            </span>
          )}
        </h2>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-5 w-5 text-viral-purple animate-spin" />
        </div>
      ) : tasks.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
          <Inbox className="h-8 w-8 mb-3 opacity-40" />
          <p className="text-sm">{emptyMessage}</p>
        </div>
      ) : (
        <div className="space-y-3">
          {tasks.map((task) => (
            <TaskCard key={task.id} task={task} />
          ))}
        </div>
      )}
    </div>
  );
}
