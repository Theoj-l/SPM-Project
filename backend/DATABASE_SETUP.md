# Database Setup for SPM Project

This document explains how to set up the database tables and storage for the SPM (Software Project Management) system.

## Prerequisites

- Supabase project set up
- Database connection configured
- Storage bucket configured

## Database Tables

The system requires the following additional tables beyond the existing ones:

### 1. Task Comments (`task_comments`)

- Stores comments on tasks
- Links to tasks and users
- Includes content and timestamp

### 2. Sub-tasks (`subtasks`)

- Stores sub-tasks for main tasks
- Links to parent tasks
- Includes status and assignees

### 3. Task Files (`task_files`)

- Stores file metadata for task attachments
- Links to tasks and uploaders
- Includes file information and download URLs

## Setup Instructions

### 1. Run the Database Schema

Execute the SQL commands in `database_schema.sql` in your Supabase SQL editor:

```sql
-- Copy and paste the contents of database_schema.sql
-- This will create all necessary tables, indexes, and policies
```

### 2. Create Storage Bucket

In your Supabase dashboard:

1. Go to **Storage** section
2. Create a new bucket named `task-files`
3. Set it as **Public** (for file downloads)
4. Configure appropriate policies

### 3. Storage Policies

Add the following storage policies for the `task-files` bucket:

```sql
-- Allow authenticated users to upload files
CREATE POLICY "Authenticated users can upload files" ON storage.objects
FOR INSERT WITH CHECK (
    bucket_id = 'task-files' AND
    auth.role() = 'authenticated'
);

-- Allow users to view files for tasks they have access to
CREATE POLICY "Users can view files for accessible tasks" ON storage.objects
FOR SELECT USING (
    bucket_id = 'task-files' AND
    EXISTS (
        SELECT 1 FROM task_files tf
        JOIN tasks t ON tf.task_id = t.id
        JOIN projects p ON t.project_id = p.id
        LEFT JOIN project_members pm ON p.id = pm.project_id
        WHERE tf.filename = storage.objects.name
        AND (p.owner_id = auth.uid() OR pm.user_id = auth.uid())
    )
);

-- Allow users to delete files they uploaded
CREATE POLICY "Users can delete their own files" ON storage.objects
FOR DELETE USING (
    bucket_id = 'task-files' AND
    EXISTS (
        SELECT 1 FROM task_files tf
        WHERE tf.filename = storage.objects.name
        AND tf.uploaded_by = auth.uid()
    )
);
```

## Features Enabled

After setup, the following features will be available:

### Task Detail Page

- **URL**: `/projects/[projectId]/tasks/[taskId]`
- **Features**:
  - View task details
  - Edit task information
  - Delete tasks

### Comments System

- Add comments to tasks
- View all comments with timestamps
- Delete own comments
- Real-time updates (if implemented)

### Sub-tasks System

- Create sub-tasks for main tasks
- Assign sub-tasks to team members
- Update sub-task status
- Delete sub-tasks

### File Upload System

- Upload files up to 50MB
- View uploaded files
- Download files
- Delete uploaded files
- File type validation

## Security Features

- **Row Level Security (RLS)** enabled on all tables
- **Access Control**: Users can only access tasks from projects they're members of
- **File Security**: Files are only accessible to project members
- **Comment Security**: Users can only delete their own comments
- **File Deletion**: Users can only delete files they uploaded

## API Endpoints

The following new API endpoints are available:

### Task Management

- `GET /api/tasks/{taskId}` - Get task details
- `DELETE /api/tasks/{taskId}` - Delete task

### Comments

- `GET /api/tasks/{taskId}/comments` - Get task comments
- `POST /api/tasks/{taskId}/comments` - Create comment
- `DELETE /api/tasks/comments/{commentId}` - Delete comment

### Sub-tasks

- `GET /api/tasks/{taskId}/subtasks` - Get sub-tasks
- `POST /api/tasks/{taskId}/subtasks` - Create sub-task
- `PATCH /api/tasks/subtasks/{subtaskId}` - Update sub-task
- `DELETE /api/tasks/subtasks/{subtaskId}` - Delete sub-task

### Files

- `GET /api/tasks/{taskId}/files` - Get task files
- `POST /api/tasks/{taskId}/files` - Upload file
- `DELETE /api/tasks/files/{fileId}` - Delete file

## Testing

After setup, you can test the functionality by:

1. Creating a project
2. Adding tasks to the project
3. Clicking on a task to view its detail page
4. Adding comments, sub-tasks, and files
5. Verifying access controls work correctly

## Troubleshooting

### Common Issues

1. **Storage bucket not found**: Ensure the `task-files` bucket is created and public
2. **Permission denied**: Check RLS policies are correctly set up
3. **File upload fails**: Verify file size is under 50MB and storage policies allow uploads
4. **Comments not showing**: Check if user has access to the task's project

### Debugging

- Check Supabase logs for detailed error messages
- Verify RLS policies in the Supabase dashboard
- Test API endpoints using the Supabase API documentation
- Check browser network tab for failed requests
