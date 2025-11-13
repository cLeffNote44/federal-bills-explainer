"""
Social features API endpoints: bookmarks, collections, comments, votes, notifications.
"""

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

router = APIRouter()


# ============================================================================
# Pydantic Models
# ============================================================================

class BookmarkCreate(BaseModel):
    bill_id: str
    notes: Optional[str] = None
    tags: Optional[List[str]] = None


class Bookmark(BaseModel):
    id: str
    user_id: str
    bill_id: str
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    created_at: datetime


class CollectionCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_public: bool = False


class Collection(BaseModel):
    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    is_public: bool
    item_count: int = 0
    created_at: datetime


class CollectionItemCreate(BaseModel):
    bill_id: str
    notes: Optional[str] = None


class CommentCreate(BaseModel):
    bill_id: str
    content: str
    parent_id: Optional[str] = None


class Comment(BaseModel):
    id: str
    user_id: str
    username: str
    bill_id: str
    parent_id: Optional[str] = None
    content: str
    upvotes: int = 0
    downvotes: int = 0
    is_deleted: bool = False
    created_at: datetime
    updated_at: datetime


class NotificationCreate(BaseModel):
    type: str
    title: str
    message: Optional[str] = None
    link: Optional[str] = None


class Notification(BaseModel):
    id: str
    type: str
    title: str
    message: Optional[str] = None
    link: Optional[str] = None
    is_read: bool = False
    created_at: datetime


# ============================================================================
# In-Memory Storage (replace with database in production)
# ============================================================================

bookmarks_db = {}
collections_db = {}
collection_items_db = {}
comments_db = {}
votes_db = {}
notifications_db = {}
bill_watches_db = {}


# ============================================================================
# Bookmarks Endpoints
# ============================================================================

@router.post("/bookmarks", response_model=Bookmark, status_code=status.HTTP_201_CREATED)
async def create_bookmark(bookmark_data: BookmarkCreate, user_id: str = "mock-user"):
    """
    Create a new bookmark for a bill.

    Allows users to save bills for later with notes and tags.
    """
    # Check if already bookmarked
    existing = [b for b in bookmarks_db.values()
                if b["user_id"] == user_id and b["bill_id"] == bookmark_data.bill_id]

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bill already bookmarked"
        )

    bookmark_id = str(uuid.uuid4())
    bookmark = {
        "id": bookmark_id,
        "user_id": user_id,
        "bill_id": bookmark_data.bill_id,
        "notes": bookmark_data.notes,
        "tags": bookmark_data.tags or [],
        "created_at": datetime.utcnow(),
    }

    bookmarks_db[bookmark_id] = bookmark

    return bookmark


@router.get("/bookmarks", response_model=List[Bookmark])
async def get_bookmarks(
    user_id: str = "mock-user",
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
    limit: int = Query(50, ge=1, le=100)
):
    """
    Get user's bookmarks.

    Returns all bookmarked bills with optional tag filtering.
    """
    user_bookmarks = [b for b in bookmarks_db.values() if b["user_id"] == user_id]

    # Filter by tags if provided
    if tags:
        tag_list = [t.strip() for t in tags.split(",")]
        user_bookmarks = [
            b for b in user_bookmarks
            if any(tag in b.get("tags", []) for tag in tag_list)
        ]

    # Sort by created_at descending
    user_bookmarks.sort(key=lambda x: x["created_at"], reverse=True)

    return user_bookmarks[:limit]


@router.delete("/bookmarks/{bill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bookmark(bill_id: str, user_id: str = "mock-user"):
    """
    Remove a bookmark.
    """
    bookmark = None
    bookmark_id = None

    for bid, b in bookmarks_db.items():
        if b["user_id"] == user_id and b["bill_id"] == bill_id:
            bookmark = b
            bookmark_id = bid
            break

    if not bookmark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookmark not found"
        )

    del bookmarks_db[bookmark_id]
    return None


# ============================================================================
# Collections Endpoints
# ============================================================================

@router.post("/collections", response_model=Collection, status_code=status.HTTP_201_CREATED)
async def create_collection(collection_data: CollectionCreate, user_id: str = "mock-user"):
    """
    Create a new bill collection.

    Collections allow users to organize bills into custom groups.
    """
    collection_id = str(uuid.uuid4())
    collection = {
        "id": collection_id,
        "user_id": user_id,
        "name": collection_data.name,
        "description": collection_data.description,
        "is_public": collection_data.is_public,
        "item_count": 0,
        "created_at": datetime.utcnow(),
    }

    collections_db[collection_id] = collection

    return collection


@router.get("/collections", response_model=List[Collection])
async def get_collections(
    user_id: str = "mock-user",
    include_public: bool = Query(False, description="Include public collections from other users")
):
    """
    Get user's collections.

    Optionally include public collections from other users.
    """
    # Get user's own collections
    user_collections = [c for c in collections_db.values() if c["user_id"] == user_id]

    # Include public collections from others if requested
    if include_public:
        public_collections = [
            c for c in collections_db.values()
            if c["user_id"] != user_id and c["is_public"]
        ]
        user_collections.extend(public_collections)

    # Update item counts
    for collection in user_collections:
        collection["item_count"] = len([
            item for item in collection_items_db.values()
            if item["collection_id"] == collection["id"]
        ])

    # Sort by created_at descending
    user_collections.sort(key=lambda x: x["created_at"], reverse=True)

    return user_collections


@router.post("/collections/{collection_id}/items", status_code=status.HTTP_201_CREATED)
async def add_to_collection(
    collection_id: str,
    item_data: CollectionItemCreate,
    user_id: str = "mock-user"
):
    """
    Add a bill to a collection.
    """
    # Check collection exists and user owns it
    collection = collections_db.get(collection_id)
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )

    if collection["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't own this collection"
        )

    # Check if already in collection
    existing = [
        item for item in collection_items_db.values()
        if item["collection_id"] == collection_id and item["bill_id"] == item_data.bill_id
    ]

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bill already in collection"
        )

    item_id = str(uuid.uuid4())
    item = {
        "id": item_id,
        "collection_id": collection_id,
        "bill_id": item_data.bill_id,
        "notes": item_data.notes,
        "added_at": datetime.utcnow(),
    }

    collection_items_db[item_id] = item

    return item


@router.delete("/collections/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_collection(collection_id: str, user_id: str = "mock-user"):
    """
    Delete a collection and all its items.
    """
    collection = collections_db.get(collection_id)
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )

    if collection["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't own this collection"
        )

    # Delete collection items
    items_to_delete = [
        item_id for item_id, item in collection_items_db.items()
        if item["collection_id"] == collection_id
    ]
    for item_id in items_to_delete:
        del collection_items_db[item_id]

    # Delete collection
    del collections_db[collection_id]

    return None


# ============================================================================
# Comments Endpoints
# ============================================================================

@router.post("/comments", response_model=Comment, status_code=status.HTTP_201_CREATED)
async def create_comment(comment_data: CommentCreate, user_id: str = "mock-user"):
    """
    Create a comment on a bill.

    Supports threaded comments via parent_id.
    """
    comment_id = str(uuid.uuid4())
    comment = {
        "id": comment_id,
        "user_id": user_id,
        "username": "mock_user",  # TODO: Get from user database
        "bill_id": comment_data.bill_id,
        "parent_id": comment_data.parent_id,
        "content": comment_data.content,
        "upvotes": 0,
        "downvotes": 0,
        "is_deleted": False,
        "is_flagged": False,
        "flag_count": 0,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    comments_db[comment_id] = comment

    # TODO: Send notification to parent comment author
    # if comment_data.parent_id:
    #     create_notification_for_reply(comment_data.parent_id, comment_id)

    return comment


@router.get("/comments", response_model=List[Comment])
async def get_comments(
    bill_id: str = Query(..., description="Bill ID"),
    sort: str = Query("top", description="Sort by: top, new, controversial"),
    limit: int = Query(50, ge=1, le=200)
):
    """
    Get comments for a bill.

    Supports different sorting algorithms.
    """
    bill_comments = [
        c for c in comments_db.values()
        if c["bill_id"] == bill_id and not c["is_deleted"]
    ]

    # Sort comments
    if sort == "top":
        bill_comments.sort(
            key=lambda x: x["upvotes"] - x["downvotes"],
            reverse=True
        )
    elif sort == "new":
        bill_comments.sort(
            key=lambda x: x["created_at"],
            reverse=True
        )
    elif sort == "controversial":
        bill_comments.sort(
            key=lambda x: min(x["upvotes"], x["downvotes"]),
            reverse=True
        )

    return bill_comments[:limit]


@router.post("/comments/{comment_id}/vote")
async def vote_comment(
    comment_id: str,
    vote_type: str = Query(..., description="upvote or downvote"),
    user_id: str = "mock-user"
):
    """
    Vote on a comment.

    Users can upvote or downvote comments.
    """
    if vote_type not in ["upvote", "downvote"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vote type must be 'upvote' or 'downvote'"
        )

    comment = comments_db.get(comment_id)
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )

    # Check if user already voted
    existing_vote = None
    vote_id = None
    for vid, v in votes_db.items():
        if v["user_id"] == user_id and v["comment_id"] == comment_id:
            existing_vote = v
            vote_id = vid
            break

    # Remove old vote if exists
    if existing_vote:
        old_type = existing_vote["vote_type"]
        if old_type == "upvote":
            comment["upvotes"] -= 1
        else:
            comment["downvotes"] -= 1

        # If same vote type, remove vote (toggle)
        if old_type == vote_type:
            del votes_db[vote_id]
            return {"message": "Vote removed", "upvotes": comment["upvotes"], "downvotes": comment["downvotes"]}

    # Add new vote
    vote_id = vote_id or str(uuid.uuid4())
    votes_db[vote_id] = {
        "id": vote_id,
        "user_id": user_id,
        "comment_id": comment_id,
        "vote_type": vote_type,
        "created_at": datetime.utcnow(),
    }

    if vote_type == "upvote":
        comment["upvotes"] += 1
    else:
        comment["downvotes"] += 1

    return {
        "message": "Vote recorded",
        "upvotes": comment["upvotes"],
        "downvotes": comment["downvotes"]
    }


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(comment_id: str, user_id: str = "mock-user"):
    """
    Delete a comment.

    Users can only delete their own comments.
    Admins can delete any comment.
    """
    comment = comments_db.get(comment_id)
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )

    # Check ownership (skip for now, TODO: add admin check)
    if comment["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own comments"
        )

    # Soft delete
    comment["is_deleted"] = True
    comment["deleted_at"] = datetime.utcnow()
    comment["content"] = "[deleted]"

    return None


# ============================================================================
# Notifications Endpoints
# ============================================================================

@router.get("/notifications", response_model=List[Notification])
async def get_notifications(
    user_id: str = "mock-user",
    unread_only: bool = Query(False, description="Only show unread"),
    limit: int = Query(50, ge=1, le=200)
):
    """
    Get user's notifications.

    Returns all notifications with option to filter unread.
    """
    user_notifications = [
        n for n in notifications_db.values()
        if n["user_id"] == user_id
    ]

    if unread_only:
        user_notifications = [n for n in user_notifications if not n["is_read"]]

    # Sort by created_at descending
    user_notifications.sort(key=lambda x: x["created_at"], reverse=True)

    return user_notifications[:limit]


@router.post("/notifications/{notification_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_notification_read(notification_id: str, user_id: str = "mock-user"):
    """
    Mark a notification as read.
    """
    notification = notifications_db.get(notification_id)
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )

    if notification["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not your notification"
        )

    notification["is_read"] = True
    notification["read_at"] = datetime.utcnow()

    return None


@router.post("/notifications/read-all", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_read(user_id: str = "mock-user"):
    """
    Mark all notifications as read.
    """
    for notification in notifications_db.values():
        if notification["user_id"] == user_id and not notification["is_read"]:
            notification["is_read"] = True
            notification["read_at"] = datetime.utcnow()

    return None


# ============================================================================
# Bill Watching Endpoints
# ============================================================================

@router.post("/watch/{bill_id}", status_code=status.HTTP_201_CREATED)
async def watch_bill(
    bill_id: str,
    notify_email: bool = Query(True),
    notify_in_app: bool = Query(True),
    webhook_url: Optional[str] = Query(None),
    user_id: str = "mock-user"
):
    """
    Watch a bill for updates.

    Get notified when bill status changes.
    """
    # Check if already watching
    existing = [
        w for w in bill_watches_db.values()
        if w["user_id"] == user_id and w["bill_id"] == bill_id
    ]

    if existing:
        # Update existing watch
        watch = existing[0]
        watch["notify_email"] = notify_email
        watch["notify_in_app"] = notify_in_app
        watch["webhook_url"] = webhook_url
        return watch

    watch_id = str(uuid.uuid4())
    watch = {
        "id": watch_id,
        "user_id": user_id,
        "bill_id": bill_id,
        "notify_email": notify_email,
        "notify_in_app": notify_in_app,
        "webhook_url": webhook_url,
        "created_at": datetime.utcnow(),
    }

    bill_watches_db[watch_id] = watch

    return watch


@router.delete("/watch/{bill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unwatch_bill(bill_id: str, user_id: str = "mock-user"):
    """
    Stop watching a bill.
    """
    watch = None
    watch_id = None

    for wid, w in bill_watches_db.items():
        if w["user_id"] == user_id and w["bill_id"] == bill_id:
            watch = w
            watch_id = wid
            break

    if not watch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not watching this bill"
        )

    del bill_watches_db[watch_id]
    return None


@router.get("/watch", response_model=List[dict])
async def get_watched_bills(user_id: str = "mock-user"):
    """
    Get all bills user is watching.
    """
    watches = [w for w in bill_watches_db.values() if w["user_id"] == user_id]

    # Sort by created_at descending
    watches.sort(key=lambda x: x["created_at"], reverse=True)

    return watches
