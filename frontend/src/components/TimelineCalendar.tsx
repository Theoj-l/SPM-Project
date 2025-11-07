"use client";

import { useState, useEffect, useMemo } from "react";
import FullCalendar from "@fullcalendar/react";
import dayGridPlugin from "@fullcalendar/daygrid";
import timeGridPlugin from "@fullcalendar/timegrid";
import interactionPlugin from "@fullcalendar/interaction";
import { useAuth } from "@/contexts/AuthContext";
import { ProjectsAPI, TasksAPI, Project, Task, UsersAPI, User, TeamsAPI, TeamMember, SubTasksAPI, SubTask } from "@/lib/api";
import { isManager, isStaff } from "@/utils/role-utils";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { X, Filter, RefreshCw } from "lucide-react";

interface TimelineCalendarProps {
  onTaskClick?: (task: Task | SubTask, isSubtask: boolean, projectId?: string, taskId?: string) => void;
}

export default function TimelineCalendar({ onTaskClick }: TimelineCalendarProps) {
  const { user } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [subtasks, setSubtasks] = useState<SubTask[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Filter states
  const [selectedProjectId, setSelectedProjectId] = useState<string>("all");
  const [selectedUserId, setSelectedUserId] = useState<string>("all");
  const [showFilters, setShowFilters] = useState(false);

  // Load initial data
  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Reload tasks when filters change
  useEffect(() => {
    if (projects.length > 0) {
      loadTasks();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedProjectId, selectedUserId, projects]);

  const loadData = async () => {
    try {
      setLoading(true);
      
      // Load projects
      const projectsData = await ProjectsAPI.list();
      setProjects(projectsData);

      // Load users (for manager filter)
      if (isManager(user)) {
        try {
          const usersData = await UsersAPI.list();
          setUsers(usersData);
        } catch (err) {
          console.error("Failed to load users:", err);
        }

        // Load team members for current user
        try {
          const teams = await TeamsAPI.list();
          const allTeamMembers: TeamMember[] = [];
          for (const team of teams) {
            try {
              const members = await TeamsAPI.getMembers(team.id);
              allTeamMembers.push(...members);
            } catch (err) {
              console.error(`Failed to load members for team ${team.id}:`, err);
            }
          }
          setTeamMembers(allTeamMembers);
        } catch (err) {
          console.error("Failed to load team members:", err);
        }
      }

      // Load tasks after projects are loaded
      await loadTasks();
    } catch (err) {
      console.error("Failed to load data:", err);
    } finally {
      setLoading(false);
    }
  };

  const loadTasks = async () => {
    try {
      const allTasks: Task[] = [];
      const allSubtasks: SubTask[] = [];
      
      // Determine which projects to fetch tasks from
      let projectsToFetch = projects;
      if (selectedProjectId !== "all") {
        projectsToFetch = projects.filter(p => p.id === selectedProjectId);
      }

      // Fetch tasks and subtasks from each project
      for (const project of projectsToFetch) {
        try {
          const projectTasks = await TasksAPI.list(project.id);
          if (projectTasks && Array.isArray(projectTasks)) {
            allTasks.push(...projectTasks);
          }
          
          // Fetch subtasks for each task
          for (const task of projectTasks) {
            try {
              const taskSubtasks = await SubTasksAPI.list(task.id);
              allSubtasks.push(...taskSubtasks);
            } catch (err) {
              console.error(`Failed to load subtasks for task ${task.id}:`, err);
            }
          }
        } catch (err) {
          console.error(`Failed to load tasks for project ${project.id}:`, err);
        }
      }

      // Filter by user if manager selected a team member
      let filteredTasks = allTasks;
      let filteredSubtasks = allSubtasks;
      
      if (selectedUserId !== "all" && isManager(user)) {
        filteredTasks = allTasks.filter(task => 
          task.assignee_ids?.includes(selectedUserId)
        );
        filteredSubtasks = allSubtasks.filter(subtask => 
          subtask.assignee_ids?.includes(selectedUserId)
        );
      }

      setTasks(filteredTasks);
      setSubtasks(filteredSubtasks);
    } catch (err) {
      console.error("Failed to load tasks:", err);
    }
  };

  // Convert tasks and subtasks to FullCalendar events
  const calendarEvents = useMemo(() => {
    const taskEvents = tasks
      .filter(task => task.due_date || task.created_at) // Only show tasks with dates
      .map(task => {
        // Calculate start date: use created_at if available, otherwise use today
        const startDate = task.created_at 
          ? new Date(task.created_at)
          : new Date();
        
        // Reset time to start of day for consistent display
        startDate.setHours(0, 0, 0, 0);

        // Calculate end date: use due_date if available, otherwise default to 1 day from start
        let endDate: Date;
        if (task.due_date) {
          endDate = new Date(task.due_date);
          // If due_date is just a date without time, set to end of day
          const timeStr = endDate.toTimeString();
          if (timeStr.includes("00:00:00") || timeStr.match(/^\d{2}:\d{2}:\d{2}/)?.[0] === "00:00:00") {
            endDate.setHours(23, 59, 59);
          }
        } else {
          // Default to 1 day duration if no due date
          endDate = new Date(startDate);
          endDate.setDate(endDate.getDate() + 1);
          endDate.setHours(23, 59, 59);
        }

        // Ensure end date is after start date
        if (endDate <= startDate) {
          endDate = new Date(startDate);
          endDate.setDate(endDate.getDate() + 1);
          endDate.setHours(23, 59, 59);
        }

        // Determine color based on status and overdue state
        const now = new Date();
        const isOverdue = task.due_date && new Date(task.due_date) < now && task.status !== "completed";
        const isCompleted = task.status === "completed";
        
        let color: string;
        if (isCompleted) {
          color = "#10b981"; // Green for completed
        } else if (isOverdue) {
          color = "#ef4444"; // Red for overdue
        } else {
          // On track - different colors based on status
          switch (task.status) {
            case "in_progress":
              color = "#3b82f6"; // Blue
              break;
            case "blocked":
              color = "#f59e0b"; // Orange/Amber
              break;
            default:
              color = "#6366f1"; // Indigo for todo
          }
        }

        // Get project name for display
        const project = projects.find(p => p.id === task.project_id);
        const projectName = project?.name || "No Project";

        // Get assignee names
        const assigneeNames = task.assignee_names?.join(", ") || task.assignee_ids?.join(", ") || "Unassigned";

        return {
          id: `task-${task.id}`,
          title: task.title,
          start: startDate,
          end: endDate,
          backgroundColor: color,
          borderColor: color,
          textColor: "#ffffff",
          extendedProps: {
            task,
            isSubtask: false,
            projectId: task.project_id,
            projectName,
            assigneeNames,
            status: task.status,
            isOverdue,
            isCompleted,
          },
        };
      });

    // Convert subtasks to events
    const subtaskEvents = subtasks
      .filter(subtask => subtask.due_date || subtask.created_at) // Only show subtasks with dates
      .map(subtask => {
        // Find parent task to get project_id
        const parentTask = tasks.find(t => t.id === subtask.parent_task_id);
        
        // Calculate start date: use created_at if available, otherwise use today
        const startDate = subtask.created_at 
          ? new Date(subtask.created_at)
          : new Date();
        
        // Reset time to start of day for consistent display
        startDate.setHours(0, 0, 0, 0);

        // Calculate end date: use due_date if available, otherwise default to 1 day from start
        let endDate: Date;
        if (subtask.due_date) {
          endDate = new Date(subtask.due_date);
          // If due_date is just a date without time, set to end of day
          const timeStr = endDate.toTimeString();
          if (timeStr.includes("00:00:00") || timeStr.match(/^\d{2}:\d{2}:\d{2}/)?.[0] === "00:00:00") {
            endDate.setHours(23, 59, 59);
          }
        } else {
          // Default to 1 day duration if no due date
          endDate = new Date(startDate);
          endDate.setDate(endDate.getDate() + 1);
          endDate.setHours(23, 59, 59);
        }

        // Ensure end date is after start date
        if (endDate <= startDate) {
          endDate = new Date(startDate);
          endDate.setDate(endDate.getDate() + 1);
          endDate.setHours(23, 59, 59);
        }

        // Determine color based on status and overdue state
        const now = new Date();
        const isOverdue = subtask.due_date && new Date(subtask.due_date) < now && subtask.status !== "completed";
        const isCompleted = subtask.status === "completed";
        
        let color: string;
        if (isCompleted) {
          color = "#10b981"; // Green for completed
        } else if (isOverdue) {
          color = "#ef4444"; // Red for overdue
        } else {
          // On track - different colors based on status
          switch (subtask.status) {
            case "in_progress":
              color = "#3b82f6"; // Blue
              break;
            case "blocked":
              color = "#f59e0b"; // Orange/Amber
              break;
            default:
              color = "#6366f1"; // Indigo for todo
          }
        }

        // Get project name for display
        const project = projects.find(p => p.id === parentTask?.project_id);
        const projectName = project?.name || "No Project";

        // Get assignee names
        const assigneeNames = subtask.assignee_names?.join(", ") || subtask.assignee_ids?.join(", ") || "Unassigned";

        return {
          id: `subtask-${subtask.id}`,
          title: `• ${subtask.title}`, // Prefix with bullet to indicate subtask
          start: startDate,
          end: endDate,
          backgroundColor: color,
          borderColor: color,
          textColor: "#ffffff",
          className: "fc-subtask", // Add class for styling
          extendedProps: {
            task: subtask,
            isSubtask: true,
            projectId: parentTask?.project_id,
            taskId: subtask.parent_task_id,
            projectName,
            assigneeNames,
            status: subtask.status,
            isOverdue,
            isCompleted,
          },
        };
      });

    return [...taskEvents, ...subtaskEvents];
  }, [tasks, subtasks, projects]);

  // Get available users for filter (team members + all users for managers)
  const availableUsers = useMemo(() => {
    if (!isManager(user)) return [];
    
    const teamMemberUserIds = new Set(teamMembers.map(m => m.user_id));
    const teamMemberUsers = users.filter(u => teamMemberUserIds.has(u.id));
    
    // Also include users who are assigned to any task
    const assignedUserIds = new Set(
      tasks.flatMap(t => t.assignee_ids || [])
    );
    const assignedUsers = users.filter(u => assignedUserIds.has(u.id));
    
    // Combine and deduplicate
    const allUsers = [...teamMemberUsers, ...assignedUsers];
    const uniqueUsers = Array.from(
      new Map(allUsers.map(u => [u.id, u])).values()
    );
    
    return uniqueUsers.sort((a, b) => 
      (a.display_name || a.email).localeCompare(b.display_name || b.email)
    );
  }, [users, teamMembers, tasks, user]);

  // Handle event click
  const handleEventClick = (clickInfo: { event: { extendedProps: { task?: unknown; isSubtask?: boolean; projectId?: string; taskId?: string } } }) => {
    const { task, isSubtask, projectId, taskId } = clickInfo.event.extendedProps;
    if (onTaskClick && task) {
      onTaskClick(task, isSubtask, projectId, taskId);
    }
  };

  // Clear filters
  const clearFilters = () => {
    setSelectedProjectId("all");
    setSelectedUserId("all");
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-muted-foreground">Loading calendar...</div>
      </div>
    );
  }

  return (
    <div className="w-full h-full flex flex-col">
      {/* Filters */}
      <div className="mb-4 flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold">Timeline View</h2>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={loadTasks}
              disabled={loading}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} />
              Refresh
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowFilters(!showFilters)}
            >
              <Filter className="h-4 w-4 mr-2" />
              Filters
            </Button>
            {(selectedProjectId !== "all" || selectedUserId !== "all") && (
              <Button
                variant="ghost"
                size="sm"
                onClick={clearFilters}
              >
                <X className="h-4 w-4 mr-2" />
                Clear
              </Button>
            )}
          </div>
        </div>

        {showFilters && (
          <div className="flex flex-wrap gap-4 p-4 border rounded-lg bg-muted/50">
            {/* Project Filter */}
            <div className="flex-1 min-w-[200px]">
              <label className="text-sm font-medium mb-2 block">Project</label>
              <Select value={selectedProjectId} onValueChange={setSelectedProjectId}>
                <SelectTrigger>
                  <SelectValue placeholder="All Projects" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Projects</SelectItem>
                  {projects.map(project => (
                    <SelectItem key={project.id} value={project.id}>
                      {project.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Team Member Filter (Manager only) */}
            {isManager(user) && (
              <div className="flex-1 min-w-[200px]">
                <label className="text-sm font-medium mb-2 block">Team Member</label>
                <Select value={selectedUserId} onValueChange={setSelectedUserId}>
                  <SelectTrigger>
                    <SelectValue placeholder="All Team Members" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Team Members</SelectItem>
                    {availableUsers.map(user => (
                      <SelectItem key={user.id} value={user.id}>
                        {user.display_name || user.email}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
          </div>
        )}

        {/* Legend */}
        <div className="flex flex-wrap gap-4 items-center text-sm">
          <span className="font-medium">Status:</span>
          <div className="flex items-center gap-1">
            <div className="w-4 h-4 rounded bg-[#10b981]"></div>
            <span>Completed</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-4 h-4 rounded bg-[#ef4444]"></div>
            <span>Overdue</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-4 h-4 rounded bg-[#3b82f6]"></div>
            <span>In Progress</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-4 h-4 rounded bg-[#6366f1]"></div>
            <span>To Do</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-4 h-4 rounded bg-[#f59e0b]"></div>
            <span>Blocked</span>
          </div>
        </div>
      </div>

      {/* Calendar */}
      <div className="flex-1 min-h-[600px]">
        <FullCalendar
          plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
          initialView="timeGridWeek"
          headerToolbar={{
            left: "prev,next today",
            center: "title",
            right: "dayGridMonth,timeGridWeek,timeGridDay",
          }}
          events={calendarEvents}
          eventClick={handleEventClick}
          eventTimeFormat={{
            hour: "2-digit",
            minute: "2-digit",
            hour12: false,
          }}
          height="auto"
          slotMinTime="00:00:00"
          slotMaxTime="24:00:00"
          allDaySlot={false}
          eventDisplay="block"
          eventOverlap={true}
          nowIndicator={true}
          slotDuration="01:00:00"
          slotLabelInterval="01:00:00"
          eventContent={(eventInfo) => {
            const projectName = eventInfo.event.extendedProps.projectName;
            const isSubtask = eventInfo.event.extendedProps.isSubtask;
            return (
              <div className="fc-event-main-frame">
                <div className="fc-event-title-container">
                  <div className={`fc-event-title fc-sticky ${isSubtask ? 'text-sm' : ''}`}>
                    {eventInfo.event.title}
                  </div>
                  <div className="fc-event-time text-xs opacity-80">
                    {projectName}
                  </div>
                </div>
              </div>
            );
          }}
          eventDidMount={(info) => {
            // Add tooltip on hover
            const task = info.event.extendedProps.task;
            const assigneeNames = info.event.extendedProps.assigneeNames;
            const status = info.event.extendedProps.status;
            const isOverdue = info.event.extendedProps.isOverdue;
            
            info.el.title = `${task.title}\nProject: ${info.event.extendedProps.projectName}\nAssignees: ${assigneeNames}\nStatus: ${status}${isOverdue ? " (Overdue)" : ""}`;
          }}
        />
      </div>
    </div>
  );
}

