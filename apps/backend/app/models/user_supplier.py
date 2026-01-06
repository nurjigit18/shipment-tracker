from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..core.database import Base


class UserSupplier(Base):
    """
    Many-to-many relationship between users and suppliers.
    Allows managers to be assigned to multiple suppliers.
    """

    __tablename__ = "user_suppliers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="suppliers")
    supplier = relationship("Supplier", back_populates="users")

    # Ensure one user can't be assigned to same supplier twice
    __table_args__ = (
        UniqueConstraint("user_id", "supplier_id", name="uq_user_supplier"),
    )

    def __repr__(self):
        return f"<UserSupplier(user_id={self.user_id}, supplier_id={self.supplier_id})>"
