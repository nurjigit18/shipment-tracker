from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from ..core.database import Base


class Role(Base):
    """
    Existing roles table - DO NOT MODIFY STRUCTURE
    Maps to existing table in Railway PostgreSQL database.
    """

    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)  # supplier, ff, driver, admin

    # Relationships
    users = relationship("User", back_populates="role")


class User(Base):
    """
    Users table with multi-tenant organization support.
    Maps to existing table in Railway PostgreSQL database.

    Note: Both 'password' and 'password_hash' columns exist.
    We use 'password_hash' for authentication (bcrypt hashes).
    The 'password' column is legacy/redundant.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)  # Used for authentication
    password = Column(String)  # Legacy column - not used
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    organization_id = Column(
        Integer, ForeignKey("organizations.id"), nullable=False, index=True
    )

    # Relationships
    role = relationship("Role", back_populates="users")
    organization = relationship("Organization", back_populates="users")
    logs = relationship("UserLog", back_populates="user", cascade="all, delete-orphan")
    status_changes = relationship(
        "ShipmentStatusHistory",
        back_populates="changed_by_user",
        cascade="all, delete-orphan",
    )
    suppliers = relationship("UserSupplier", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', org_id={self.organization_id})>"
