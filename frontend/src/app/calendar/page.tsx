"use client";

import { useRouter } from "next/navigation";
import TimelineCalendar from "@/components/TimelineCalendar";
import { Task, SubTask } from "@/lib/api";

export default function CalendarPage() {
  const router = useRouter();

  const handleTaskClick = (task: Task | SubTask, isSubtask: boolean, projectId?: string, taskId?: string) => {
    if (isSubtask) {
      // Navigate to subtask page
      if (projectId && taskId && task.id) {
        router.push(`/projects/${projectId}/tasks/${taskId}/subtasks/${task.id}`);
      }
    } else {
      // Navigate to task page
      const regularTask = task as Task;
      if (regularTask.project_id && regularTask.id) {
        router.push(`/projects/${regularTask.project_id}/tasks/${regularTask.id}`);
      }
    }
  };

  return (
    <div className="container mx-auto p-6">
      <TimelineCalendar onTaskClick={handleTaskClick} />
    </div>
  );
}
