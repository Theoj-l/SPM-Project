from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import List
from app.models.project import (
    TaskOut, 
    TaskUpdate,
    CommentCreate, 
    CommentOut, 
    SubTaskCreate, 
    SubTaskOut, 
    FileOut
)
from app.services.task_service import TaskService
from app.routers.projects import get_current_user_id

router = APIRouter()

@router.get("/{task_id}", response_model=TaskOut)
async def get_task(task_id: str, user_id: str = Depends(get_current_user_id)):
    """Get a specific task by ID"""
    try:
        task_service = TaskService()
        task = await task_service.get_task_by_id(task_id, user_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return task
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{task_id}", response_model=TaskOut)
async def update_task(task_id: str, updates: TaskUpdate, user_id: str = Depends(get_current_user_id)):
    """Update a task - project cannot be changed, tags can be updated"""
    try:
        task_service = TaskService()
        # Convert TaskUpdate to dict, handling None values
        update_dict = updates.dict(exclude_unset=True)
        # Convert tags list back to dict format if it was parsed
        if 'tags' in update_dict and update_dict['tags'] is not None:
            update_dict['tags'] = update_dict['tags']  # Already parsed as list
        
        task = await task_service.update_task(task_id, update_dict, user_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return task
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{task_id}")
async def delete_task(task_id: str, user_id: str = Depends(get_current_user_id)):
    """Delete a task"""
    try:
        task_service = TaskService()
        success = await task_service.delete_task(task_id, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        return {"message": "Task deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{task_id}/archive", response_model=TaskOut)
async def archive_task(task_id: str, user_id: str = Depends(get_current_user_id)):
    """Archive a task"""
    try:
        task_service = TaskService()
        task = await task_service.archive_task(task_id, user_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return task
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{task_id}/restore", response_model=TaskOut)
async def restore_task(task_id: str, user_id: str = Depends(get_current_user_id)):
    """Restore an archived task"""
    try:
        task_service = TaskService()
        task = await task_service.restore_task(task_id, user_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return task
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Comments endpoints
@router.get("/{task_id}/comments", response_model=List[CommentOut])
async def get_task_comments(task_id: str, user_id: str = Depends(get_current_user_id)):
    """Get all comments for a task"""
    try:
        task_service = TaskService()
        comments = await task_service.get_task_comments(task_id, user_id)
        return comments
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{task_id}/comments", response_model=CommentOut)
async def create_comment(
    task_id: str, 
    comment_data: CommentCreate, 
    user_id: str = Depends(get_current_user_id)
):
    """Create a new comment for a task"""
    try:
        task_service = TaskService()
        comment = await task_service.create_comment(task_id, comment_data, user_id)
        return comment
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/comments/{comment_id}")
async def delete_comment(comment_id: str, user_id: str = Depends(get_current_user_id)):
    """Delete a comment"""
    try:
        task_service = TaskService()
        success = await task_service.delete_comment(comment_id, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Comment not found")
        return {"message": "Comment deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Sub-tasks endpoints
@router.get("/{task_id}/subtasks", response_model=List[SubTaskOut])
async def get_subtasks(task_id: str, user_id: str = Depends(get_current_user_id)):
    """Get all sub-tasks for a task"""
    try:
        task_service = TaskService()
        subtasks = await task_service.get_subtasks(task_id, user_id)
        return subtasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{task_id}/subtasks", response_model=SubTaskOut)
async def create_subtask(
    task_id: str, 
    subtask_data: SubTaskCreate, 
    user_id: str = Depends(get_current_user_id)
):
    """Create a new sub-task"""
    try:
        task_service = TaskService()
        subtask = await task_service.create_subtask(task_id, subtask_data, user_id)
        return subtask
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/subtasks/{subtask_id}", response_model=SubTaskOut)
async def get_subtask(subtask_id: str, user_id: str = Depends(get_current_user_id)):
    """Get a specific sub-task by ID"""
    try:
        task_service = TaskService()
        subtask = await task_service.get_subtask_by_id(subtask_id, user_id)
        if not subtask:
            raise HTTPException(status_code=404, detail="Sub-task not found")
        return subtask
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/subtasks/{subtask_id}", response_model=SubTaskOut)
async def update_subtask(
    subtask_id: str, 
    updates: dict, 
    user_id: str = Depends(get_current_user_id)
):
    """Update a sub-task"""
    try:
        task_service = TaskService()
        subtask = await task_service.update_subtask(subtask_id, updates, user_id)
        if not subtask:
            raise HTTPException(status_code=404, detail="Sub-task not found")
        return subtask
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/subtasks/{subtask_id}")
async def delete_subtask(subtask_id: str, user_id: str = Depends(get_current_user_id)):
    """Delete a sub-task"""
    try:
        task_service = TaskService()
        success = await task_service.delete_subtask(subtask_id, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Sub-task not found")
        return {"message": "Sub-task deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# File endpoints
@router.get("/{task_id}/files", response_model=List[FileOut])
async def get_task_files(task_id: str, user_id: str = Depends(get_current_user_id)):
    """Get all files for a task"""
    try:
        task_service = TaskService()
        files = await task_service.get_task_files(task_id, user_id)
        return files
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{task_id}/files", response_model=FileOut)
async def upload_file(
    task_id: str, 
    file: UploadFile = File(...), 
    user_id: str = Depends(get_current_user_id)
):
    """Upload a file to a task"""
    try:
        if not file.filename:
            raise HTTPException(status_code=422, detail="Filename is required")
        
        # Validate file size (50MB limit)
        file_content = await file.read()
        if len(file_content) > 50 * 1024 * 1024:  # 50MB
            raise HTTPException(status_code=413, detail="File size cannot exceed 50MB")
        
        task_service = TaskService()
        file_data = await task_service.upload_file(
            task_id, 
            file.filename, 
            file.content_type or "application/octet-stream", 
            file_content, 
            user_id
        )
        return file_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/files/{file_id}/download")
async def download_file(file_id: str, user_id: str = Depends(get_current_user_id)):
    """Download a file"""
    try:
        task_service = TaskService()
        file_data = await task_service.download_file(file_id, user_id)
        if not file_data:
            raise HTTPException(status_code=404, detail="File not found")
        
        from fastapi.responses import StreamingResponse
        import io
        
        file_stream = io.BytesIO(file_data["content"])
        return StreamingResponse(
            io.BytesIO(file_data["content"]),
            media_type=file_data["content_type"],
            headers={"Content-Disposition": f"attachment; filename={file_data['filename']}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/files/{file_id}")
async def delete_file(file_id: str, user_id: str = Depends(get_current_user_id)):
    """Delete a file"""
    try:
        task_service = TaskService()
        success = await task_service.delete_file(file_id, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="File not found")
        return {"message": "File deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Subtask file endpoints
@router.get("/subtasks/{subtask_id}/files", response_model=List[FileOut])
async def get_subtask_files(subtask_id: str, user_id: str = Depends(get_current_user_id)):
    """Get all files for a subtask"""
    try:
        task_service = TaskService()
        files = await task_service.get_subtask_files(subtask_id, user_id)
        return files
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/subtasks/{subtask_id}/files", response_model=FileOut)
async def upload_subtask_file(
    subtask_id: str, 
    file: UploadFile = File(...), 
    user_id: str = Depends(get_current_user_id)
):
    """Upload a file to a subtask"""
    try:
        if not file.filename:
            raise HTTPException(status_code=422, detail="Filename is required")
        
        # Validate file size (50MB limit)
        file_content = await file.read()
        if len(file_content) > 50 * 1024 * 1024:  # 50MB
            raise HTTPException(status_code=413, detail="File size cannot exceed 50MB")
        
        task_service = TaskService()
        file_data = await task_service.upload_subtask_file(
            subtask_id, 
            file.filename, 
            file.content_type or "application/octet-stream", 
            file_content, 
            user_id
        )
        return file_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))