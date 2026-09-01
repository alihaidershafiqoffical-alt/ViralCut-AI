"use client";

import { Badge } from "@/components/ui/Badge";
import { Progress } from "@/components/ui/Progress";
import {
  Clock,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  Download,
  MoreHorizontal,
  FileVideo,
} from "lucide-react";
import { formatRelativeTime, formatStatus } from "@/lib/formatters";
import type { Task } from "@/types/task";
import { cn } from "@/lib/utils";

interface TaskCardProps {
  task: Task;
}

const statusConfig = {
  pending: {
    icon: Clock,
    color: "text-yellow-400",
    bgColor: "bg-yellow-400/10",
    badgeClass: "bg-yellow-400/10 text-yellow-400 border-yellow-400/20",
    progressClass: "bg-yellow-400",
  },
  processing: {
    icon: Loader2,
    color: "text-viral-purple",
    bgColor: "bg-viral-purple/10",
    badgeClass: "bg-viral-purple/10 text-viral-purple border-viral-purple/20",
    progressClass: "bg-viral-purple",
  },
  completed: {
    icon: CheckCircle2,
    color: "text-emerald-400",
    bgColor: "bg-emerald-400/10",
    badgeClass: "bg-emerald-400/10 text-emerald-400 border-emerald-400/20",
    progressClass: "bg-emerald-400",
  },
  failed: {
    icon: AlertTriangle,
    color: "text-red-400",
    bgColor: "bg-red-400/10",
    badgeClass: "bg-red-400/10 text-red-400 border-red-400/20",
    progressClass: "bg-red-400",
  },
};

export function TaskCard({ task }: TaskCardProps) {
  const config = statusConfig[task.status];
  const StatusIcon = config.icon;

  return (
    <div className="glass-card rounded-xl p-4 transition-all duration-300 hover:-translate-y-0.5 animate-fade-in">
      <div className="flex items-start gap-4">
        {/* Video thumbnail placeholder */}
        <div
          className={cn(
            "flex h-12 w-12 items-center justify-center rounded-xl shrink-0",
            config.bgColor
          )}
        >
          <FileVideo className={cn("h-5 w-5", config.color)} />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0">
              <h3 className="text-sm font-medium truncate">{task.videoTitle}</h3>
              <p className="text-xs text-muted-foreground mt-0.5">
                {formatRelativeTime(task.createdAt)}
              </p>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <Badge variant="outline" className={cn("text-[10px] px-2 py-0.5 font-medium", config.badgeClass)}>
                <StatusIcon
                  className={cn(
                    "h-3 w-3 mr-1",
                    task.status === "processing" && "animate-spin"
                  )}
                />
                {formatStatus(task.status)}
              </Badge>
              <button className="p-1 rounded-lg text-muted-foreground hover:text-foreground hover:bg-white/5 transition-colors">
                <MoreHorizontal className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Progress bar for active tasks */}
          {(task.status === "processing" || task.status === "pending") && (
            <div className="mt-3 space-y-1.5">
              <Progress
                value={task.progress}
                className="h-1.5 bg-white/5"
              />
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-muted-foreground">
                  {task.status === "pending"
                    ? "Waiting in queue..."
                    : "Processing video..."}
                </span>
                <span className="text-[10px] text-muted-foreground font-mono">
                  {task.progress}%
                </span>
              </div>
            </div>
          )}

          {/* Download button for completed tasks */}
          {task.status === "completed" && task.outputUrls && (
            <div className="mt-3 flex items-center gap-2">
              <button className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-400/10 px-3 py-1.5 text-xs font-medium text-emerald-400 hover:bg-emerald-400/20 transition-colors">
                <Download className="h-3 w-3" />
                Download Clips ({task.outputUrls.length})
              </button>
            </div>
          )}

          {/* Error message for failed tasks */}
          {task.status === "failed" && task.error && (
            <p className="mt-2 text-xs text-red-400/80">{task.error}</p>
          )}
        </div>
      </div>
    </div>
  );
}
