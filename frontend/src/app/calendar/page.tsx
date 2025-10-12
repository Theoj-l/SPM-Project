"use client";

import FullCalendar from "@fullcalendar/react";
import dayGridPlugin from "@fullcalendar/daygrid";
import timeGridPlugin from "@fullcalendar/timegrid";
import interactionPlugin from "@fullcalendar/interaction";

export default function CalendarPage() {
  const handleDateClick = (arg: any) => {
    alert("Date clicked: " + arg.dateStr);
  };

  const handleEventClick = (arg: any) => {
    alert("Event clicked: " + arg.event.title);
  };

  const handleSelect = (arg: any) => {
    alert("Selected: " + arg.startStr + " to " + arg.endStr);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Calendar</h1>
        <p className="text-muted-foreground">
          Manage your schedule and deadlines
        </p>
      </div>

      <div className="rounded-lg border bg-card p-6">
        <FullCalendar
          plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
          headerToolbar={{
            left: "prev,next today",
            center: "title",
            right: "dayGridMonth,timeGridWeek,timeGridDay",
          }}
          initialView="dayGridMonth"
          editable={true}
          selectable={true}
          selectMirror={true}
          dayMaxEvents={true}
          weekends={true}
          height="auto"
          events={[
            // All-day events
            {
              id: "1",
              title: "Project Deadline",
              start: "2024-12-15",
              allDay: true,
              color: "#ef4444",
            },
            {
              id: "2",
              title: "Holiday - Company Day",
              start: "2024-12-25",
              allDay: true,
              color: "#f59e0b",
            },
            // Timed events
            {
              id: "3",
              title: "Team Meeting",
              start: "2024-12-12T10:00:00",
              end: "2024-12-12T11:00:00",
              color: "#3b82f6",
            },
            {
              id: "4",
              title: "Client Review",
              start: "2024-12-20T14:00:00",
              end: "2024-12-20T15:30:00",
              color: "#10b981",
            },
            {
              id: "5",
              title: "Code Review Session",
              start: "2024-12-18T09:00:00",
              end: "2024-12-18T10:30:00",
              color: "#8b5cf6",
            },
            // Multi-day events
            {
              id: "6",
              title: "Conference - Tech Summit",
              start: "2024-12-22",
              end: "2024-12-24",
              color: "#06b6d4",
            },
            {
              id: "7",
              title: "Sprint Planning",
              start: "2024-12-16T13:00:00",
              end: "2024-12-16T16:00:00",
              color: "#84cc16",
            },
            // Recurring pattern example (weekly)
            {
              id: "8",
              title: "Weekly Standup",
              start: "2024-12-13T09:00:00",
              end: "2024-12-13T09:30:00",
              color: "#f97316",
            },
            {
              id: "9",
              title: "Weekly Standup",
              start: "2024-12-20T09:00:00",
              end: "2024-12-20T09:30:00",
              color: "#f97316",
            },
            // Different event types
            {
              id: "10",
              title: "Lunch with Client",
              start: "2024-12-19T12:00:00",
              end: "2024-12-19T13:30:00",
              color: "#ec4899",
            },
            {
              id: "11",
              title: "Training Session",
              start: "2024-12-17T14:00:00",
              end: "2024-12-17T17:00:00",
              color: "#14b8a6",
            },
          ]}
          dateClick={handleDateClick}
          eventClick={handleEventClick}
          select={handleSelect}
        />
      </div>
    </div>
  );
}
