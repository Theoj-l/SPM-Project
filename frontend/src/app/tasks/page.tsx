"use client";
import { useState, useEffect } from "react";

interface Task {
  id: string;
  title: string;
  due_date: string | null;
  status: string;
  overdue_reason?: string | null;
  assigned_user?: string | null;
}

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [title, setTitle] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [error, setError] = useState("");

  const loadTasks = async () => {
    const res = await fetch("http://localhost:5000/tasks");
    const data = await res.json();

    // Sort by due date (soonest first)
    const sorted = [...data].sort((a, b) => {
      if (!a.due_date) return 1;
      if (!b.due_date) return -1;
      return new Date(a.due_date).getTime() - new Date(b.due_date).getTime();
    });
    setTasks(sorted);
  };

  useEffect(() => {
    loadTasks();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      const res = await fetch("http://localhost:5000/tasks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title,
          due_date: dueDate || null,
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to create task");
      }

      setTitle("");
      setDueDate("");
      loadTasks();
    } catch (err: any) {
      setError(err.message);
    }
  };

  // Helper for color coding (non-overdue only)
  // Helper for color coding based on urgency
const getColor = (task: Task) => {
  if (task.status === "Overdue") return "red"; // 🔴 Overdue = red
  if (!task.due_date) return "green"; // 🟢 No deadline = green

  const today = new Date();
  const due = new Date(task.due_date);

  // Difference in full days
  const diffDays = Math.ceil((due.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));

  if (diffDays <= 0) return "red"; // overdue safeguard
  if (diffDays <= 3) return "#FF8C00"; // 🟠 Dark orange for 1–3 days
  if (diffDays <= 7) return "orange"; // 🟡 Light orange for 4–7 days
  return "green"; // 🟢 Safe zone
};


  const overdueTasks = tasks.filter((t) => t.status === "Overdue");
  const otherTasks = tasks.filter((t) => t.status !== "Overdue");

  return (
    <main style={{ padding: "2rem", maxWidth: "600px", margin: "auto" }}>
      <h2>Create Task</h2>
      <form onSubmit={handleSubmit} style={{ marginBottom: "1rem" }}>
        <div>
          <label>Title:</label>
          <input
            style={{ marginLeft: "10px" }}
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
            placeholder="Enter task title"
          />
        </div>
        <div style={{ marginTop: "10px" }}>
          <label>Due Date:</label>
          <input
            type="date"
            style={{ marginLeft: "10px" }}
            value={dueDate}
            onChange={(e) => setDueDate(e.target.value)}
          />
        </div>
        {error && <p style={{ color: "red" }}>{error}</p>}
        <button
          type="submit"
          style={{
            marginTop: "15px",
            padding: "6px 12px",
            borderRadius: "6px",
            cursor: "pointer",
          }}
        >
          Save Task
        </button>
      </form>

      {/* Dashboard Summary */}
      <h3>Dashboard Summary</h3>
      <p>
        Total Tasks: {tasks.length} | Overdue: {overdueTasks.length}
      </p>

      {/* Overdue Section */}
      {overdueTasks.length > 0 && (
        <section style={{ marginTop: "1rem" }}>
          <h3 style={{ color: "red" }}>Overdue Tasks</h3>
          <ul style={{ listStyle: "none", paddingLeft: 0 }}>
            {overdueTasks.map((t) => (
              <li
                key={t.id}
                style={{
                  marginBottom: "10px",
                  borderLeft: "6px solid red",
                  paddingLeft: "10px",
                }}
              >
                <strong>{t.title}</strong> —{" "}
                {t.due_date ? t.due_date : "No deadline"} ({t.status})
                <br />
                <small>
                  {t.overdue_reason && `Reason: ${t.overdue_reason}`}
                  {t.assigned_user && ` | Assigned to: ${t.assigned_user}`}
                </small>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Other Tasks */}
      <section style={{ marginTop: "2rem" }}>
        <h3>All Other Tasks</h3>
        <ul style={{ listStyle: "none", paddingLeft: 0 }}>
          {otherTasks.map((t) => {
            const color = getColor(t);
            return (
              <li
                key={t.id}
                style={{
                  marginBottom: "10px",
                  borderLeft: `6px solid ${color}`,
                  paddingLeft: "10px",
                }}
              >
                <strong>{t.title}</strong> —{" "}
                {t.due_date ? t.due_date : "No deadline"} ({t.status})
              </li>
            );
          })}
        </ul>
      </section>
    </main>
  );
}
