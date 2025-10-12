# Task Features Database Migration

This migration adds support for comments, sub-tasks, and file uploads to your SPM project.

## What This Migration Adds

### 1. **Comments Table** (`comments`)

- Store comments on tasks
- Track who made the comment and when
- Link comments to specific tasks

### 2. **Sub-tasks Table** (`subtasks`)

- Create sub-tasks under main tasks
- Support for assignees (up to 5)
- Status tracking (todo, in_progress, completed, blocked)

### 3. **Files Table** (`task_files`)

- Store file metadata for task attachments
- Link to files stored in Supabase Storage bucket `task_files`
- Support for files up to 50MB

## How to Run the Migration

### Step 1: Run the SQL Migration

1. Open your Supabase dashboard
2. Go to **SQL Editor**
3. Copy and paste the contents of `migrate_add_task_features.sql`
4. Click **Run**

### Step 2: Set Up Storage Bucket Policy

1. Go to **Storage** in your Supabase dashboard
2. Click on the `task_files` bucket
3. Go to **Policies** tab
4. Add a new policy with these settings:

**Policy Name**: `Users can upload files for tasks they have access to`

**Policy Definition**:

```sql
bucket_id = 'task_files' AND auth.uid()::text = (storage.foldername(name))[1]
```

**Policy Check**:

```sql
bucket_id = 'task_files' AND auth.uid()::text = (storage.foldername(name))[1]
```

### Step 3: Verify the Migration

After running the migration, you should see these new tables in your database:

- `comments`
- `subtasks`
- `task_files`

## Database Schema Overview

### Comments Table

```sql
comments (
    id UUID PRIMARY KEY,
    task_id UUID REFERENCES tasks(id),
    user_id UUID REFERENCES users(id),
    content TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
```

### Sub-tasks Table

```sql
subtasks (
    id UUID PRIMARY KEY,
    parent_task_id UUID REFERENCES tasks(id),
    title VARCHAR(255),
    description TEXT,
    status VARCHAR(20),
    assigned UUID[], -- Array of user IDs
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
```

### Files Table

```sql
task_files (
    id UUID PRIMARY KEY,
    task_id UUID REFERENCES tasks(id),
    user_id UUID REFERENCES users(id),
    filename VARCHAR(255),
    original_filename VARCHAR(255),
    content_type VARCHAR(100),
    file_size INTEGER,
    storage_path VARCHAR(500),
    created_at TIMESTAMP
)
```

## Security Features

- **Row Level Security (RLS)** enabled on all tables
- **Access Control**: Users can only see/edit comments, sub-tasks, and files for tasks they have access to
- **File Security**: Files are stored with user-specific paths in Supabase Storage
- **Cascade Deletes**: When a task is deleted, all related comments, sub-tasks, and files are automatically deleted

## What You Get After Migration

✅ **Comments**: Users can add comments to tasks they have access to  
✅ **Sub-tasks**: Create and manage sub-tasks under main tasks  
✅ **File Uploads**: Upload files up to 50MB to tasks  
✅ **Access Control**: Proper security with RLS policies  
✅ **Performance**: Optimized with proper indexes

## Next Steps

After running this migration, the backend API endpoints for comments, sub-tasks, and files will work properly. The frontend task detail page will be able to:

1. Display and add comments
2. Show and create sub-tasks
3. Upload and download files
4. Manage all task-related data securely

## Troubleshooting

If you encounter any issues:

1. **Check RLS Policies**: Make sure Row Level Security is working correctly
2. **Verify Storage Bucket**: Ensure the `task_files` bucket exists and has proper policies
3. **Check Permissions**: Verify that authenticated users have proper permissions
4. **Review Logs**: Check Supabase logs for any error messages

The migration is designed to be safe and won't affect existing data.
