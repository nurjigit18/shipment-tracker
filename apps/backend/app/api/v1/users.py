from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from pydantic import BaseModel

from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...models.user import User, Role
from ...models.organization import Organization
from ...models.warehouse import Fulfillment
from ...core.config import settings
import bcrypt

router = APIRouter()


# Schemas
class UserListItem(BaseModel):
    id: int
    username: str
    role: str
    organization_name: str
    fulfillment_name: Optional[str] = None

    class Config:
        from_attributes = True


class UserCreateRequest(BaseModel):
    username: str
    password: str
    role_name: str
    organization_id: int
    fulfillment_id: Optional[int] = None


class UserCreateResponse(BaseModel):
    id: int
    username: str
    role: str
    organization_name: str

    class Config:
        from_attributes = True


@router.get("/", response_model=List[UserListItem])
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List users based on role:
    - Admin: See all users across all organizations
    - Owner: See all users in their organization
    - Others: Access denied

    Returns:
        List of users with their details

    Raises:
        HTTPException 403: If user is not admin or owner
    """
    # Check if user is admin or owner
    if current_user.role.name not in ["admin", "owner"]:
        raise HTTPException(
            status_code=403,
            detail="Only admin and owner can view users"
        )

    # Build query
    query = select(User).options(
        selectinload(User.role),
        selectinload(User.organization),
        selectinload(User.fulfillment)
    )

    # Filter by organization for owner role
    if current_user.role.name == "owner":
        query = query.where(User.organization_id == current_user.organization_id)
        # Don't show admin users to owners
        query = query.join(Role).where(Role.name != "admin")

    # Admin sees all users (no additional filter)

    # Order by username
    query = query.order_by(User.username)

    # Execute query
    result = await db.execute(query)
    users = result.scalars().all()

    # Format response
    return [
        UserListItem(
            id=u.id,
            username=u.username,
            role=u.role.name,
            organization_name=u.organization.name if u.organization else "Нет организации",
            fulfillment_name=u.fulfillment.name if u.fulfillment else None
        )
        for u in users
    ]


@router.post("/", response_model=UserCreateResponse, status_code=201)
async def create_user(
    user_data: UserCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new user.

    Access:
    - Admin: Can create users in any organization
    - Owner: Can only create users in their organization

    Args:
        user_data: User creation data
        db: Database session
        current_user: Authenticated user

    Returns:
        Created user data

    Raises:
        HTTPException 403: If user is not admin or owner
        HTTPException 400: If username already exists or invalid data
    """
    # Check if user is admin or owner
    if current_user.role.name not in ["admin", "owner"]:
        raise HTTPException(
            status_code=403,
            detail="Only admin and owner can create users"
        )

    # Owner can only create users in their organization
    if current_user.role.name == "owner":
        if user_data.organization_id != current_user.organization_id:
            raise HTTPException(
                status_code=403,
                detail="Owner can only create users in their organization"
            )

    # Check if username already exists
    existing_user = await db.execute(
        select(User).where(User.username == user_data.username)
    )
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )

    # Get role
    role_result = await db.execute(
        select(Role).where(Role.name == user_data.role_name)
    )
    role = role_result.scalar_one_or_none()
    if not role:
        raise HTTPException(
            status_code=400,
            detail=f"Role '{user_data.role_name}' not found"
        )

    # Verify organization exists
    org_result = await db.execute(
        select(Organization).where(Organization.id == user_data.organization_id)
    )
    organization = org_result.scalar_one_or_none()
    if not organization:
        raise HTTPException(
            status_code=400,
            detail="Organization not found"
        )

    # If fulfillment_id provided, verify it exists
    if user_data.fulfillment_id:
        ff_result = await db.execute(
            select(Fulfillment).where(Fulfillment.id == user_data.fulfillment_id)
        )
        fulfillment = ff_result.scalar_one_or_none()
        if not fulfillment:
            raise HTTPException(
                status_code=400,
                detail="Fulfillment not found"
            )

    # Hash password using bcrypt
    password_bytes = user_data.password.encode('utf-8')
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')

    # Create user
    new_user = User(
        username=user_data.username,
        password_hash=password_hash,
        role_id=role.id,
        organization_id=user_data.organization_id,
        fulfillment_id=user_data.fulfillment_id
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # Load relationships
    await db.execute(
        select(User)
        .options(
            selectinload(User.role),
            selectinload(User.organization)
        )
        .where(User.id == new_user.id)
    )
    await db.refresh(new_user)

    return UserCreateResponse(
        id=new_user.id,
        username=new_user.username,
        role=new_user.role.name,
        organization_name=new_user.organization.name
    )


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Remove or delete a user based on role.

    Access and behavior:
    - Owner: Removes user from their organization (sets organization_id to NULL)
             User still exists in database but loses org access
             Can only remove users from their own organization
    - Admin: Deletes user completely from database
             Can delete any user (permanent deletion)

    Args:
        user_id: User ID to remove/delete
        db: Database session
        current_user: Authenticated user

    Returns:
        204 No Content on success

    Raises:
        HTTPException 403: If user is not admin or owner, or owner trying to remove user from another org
        HTTPException 404: If user not found
        HTTPException 400: If trying to remove/delete yourself, or owner trying to remove user without org
    """
    # Check if user is admin or owner
    if current_user.role.name not in ["admin", "owner"]:
        raise HTTPException(
            status_code=403,
            detail="Only admin and owner can remove/delete users"
        )

    # Get user to remove/delete
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user_to_modify = result.scalar_one_or_none()

    if not user_to_modify:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # Prevent self-removal/deletion
    if user_to_modify.id == current_user.id:
        if current_user.role.name == "owner":
            raise HTTPException(
                status_code=400,
                detail="Cannot remove yourself from the organization"
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete yourself"
            )

    # OWNER: Remove user from organization
    if current_user.role.name == "owner":
        # Owner can only remove users from their organization
        if user_to_modify.organization_id != current_user.organization_id:
            raise HTTPException(
                status_code=403,
                detail="Owner can only remove users from their organization"
            )

        # Check if user already has no organization
        if user_to_modify.organization_id is None:
            raise HTTPException(
                status_code=400,
                detail="User is not in any organization"
            )

        # Remove from organization (set organization_id to NULL)
        user_to_modify.organization_id = None
        await db.commit()

    # ADMIN: Delete user completely
    elif current_user.role.name == "admin":
        # Admin deletes the user permanently
        await db.delete(user_to_modify)
        await db.commit()

    return None


class UserSearchResult(BaseModel):
    id: int
    username: str
    role: str
    organization_name: Optional[str]
    fulfillment_name: Optional[str] = None

    class Config:
        from_attributes = True


@router.get("/search", response_model=List[UserSearchResult])
async def search_users(
    username: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Search users by username (admin and owner only).

    Args:
        username: Username to search for (partial match, case-insensitive)
        db: Database session
        current_user: Authenticated user

    Returns:
        List of matching users (max 10)

    Raises:
        HTTPException 403: If user is not admin or owner
    """
    # Validate access
    if current_user.role.name not in ["admin", "owner"]:
        raise HTTPException(status_code=403, detail="Access denied")

    # Search by username (case-insensitive partial match)
    query = select(User).options(
        selectinload(User.role),
        selectinload(User.organization),
        selectinload(User.fulfillment)
    ).where(User.username.ilike(f"%{username}%"))

    # Owner: exclude admin users from search
    if current_user.role.name == "owner":
        query = query.join(Role).where(Role.name != "admin")

    query = query.order_by(User.username).limit(10)

    result = await db.execute(query)
    users = result.scalars().all()

    return [
        UserSearchResult(
            id=u.id,
            username=u.username,
            role=u.role.name,
            organization_name=u.organization.name if u.organization else "Нет организации",
            fulfillment_name=u.fulfillment.name if u.fulfillment else None
        )
        for u in users
    ]


class AddExistingUserRequest(BaseModel):
    user_id: int


class AddExistingUserResponse(BaseModel):
    id: int
    username: str
    role: str
    organization_name: str
    message: str

    class Config:
        from_attributes = True


@router.post("/add-existing", response_model=AddExistingUserResponse)
async def add_existing_user(
    request: AddExistingUserRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Add existing user to owner's organization (owner only).

    Only users without an organization (organization_id = NULL) can be added.
    Users from other organizations cannot be added.

    Args:
        request: Contains user_id of user to add
        db: Database session
        current_user: Authenticated user (must be owner)

    Returns:
        Added user details with success message

    Raises:
        HTTPException 403: If user is not owner, or trying to add admin user
        HTTPException 404: If user not found
        HTTPException 400: If validation fails (self-add, already in org, or from another org)
    """
    # Validate access (owner only)
    if current_user.role.name != "owner":
        raise HTTPException(
            status_code=403,
            detail="Only owners can add existing users to organization"
        )

    # Get user to add
    result = await db.execute(
        select(User).options(
            selectinload(User.role),
            selectinload(User.organization)
        ).where(User.id == request.user_id)
    )
    user_to_add = result.scalar_one_or_none()

    if not user_to_add:
        raise HTTPException(status_code=404, detail="User not found")

    # Validation: Cannot add self
    if user_to_add.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot add yourself")

    # Validation: Cannot add admin users
    if user_to_add.role.name == "admin":
        raise HTTPException(
            status_code=403,
            detail="Cannot add admin users to organization"
        )

    # Validation: Check if already in owner's organization
    if user_to_add.organization_id == current_user.organization_id:
        raise HTTPException(
            status_code=400,
            detail="User is already in your organization"
        )

    # Validation: User must not belong to another organization
    if user_to_add.organization_id is not None:
        raise HTTPException(
            status_code=400,
            detail="Cannot add user from another organization. User must not have an organization."
        )

    # Reassign user to owner's organization
    user_to_add.organization_id = current_user.organization_id

    await db.commit()
    await db.refresh(user_to_add)

    # Reload with new organization
    result = await db.execute(
        select(User).options(
            selectinload(User.role),
            selectinload(User.organization)
        ).where(User.id == user_to_add.id)
    )
    await db.refresh(user_to_add)

    return AddExistingUserResponse(
        id=user_to_add.id,
        username=user_to_add.username,
        role=user_to_add.role.name,
        organization_name=user_to_add.organization.name,
        message="User added to organization"
    )
