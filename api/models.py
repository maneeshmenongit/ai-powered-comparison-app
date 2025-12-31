"""api/models.py

SQLAlchemy models for user favorites feature.
"""

from datetime import datetime
import uuid
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB, UUID
from api.database import Base
import bcrypt


class User(Base):
    """User model - supports both guest (device_id) and authenticated users."""
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(String(255), unique=True, nullable=True, index=True)  # For guest users
    username = Column(String(80), unique=True, nullable=True, index=True)  # For authenticated users
    email = Column(String(120), unique=True, nullable=True, index=True)  # For authenticated users
    password_hash = Column(String(255), nullable=True)  # For authenticated users
    is_guest = Column(Boolean, default=False, nullable=False)
    is_premium = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship to saved restaurants
    saved_restaurants = relationship(
        'SavedRestaurant',
        back_populates='user',
        cascade='all, delete-orphan'
    )

    def set_password(self, password):
        """Hash and set the user's password."""
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')

    def check_password(self, password):
        """Check if the provided password matches the stored hash."""
        if not self.password_hash:
            return False
        password_bytes = password.encode('utf-8')
        hash_bytes = self.password_hash.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hash_bytes)

    def to_dict(self):
        """Convert user to dictionary."""
        return {
            'id': str(self.id),  # Convert UUID to string for JSON
            'device_id': self.device_id,
            'username': self.username,
            'email': self.email,
            'is_guest': self.is_guest,
            'is_premium': self.is_premium,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        identifier = self.username or self.device_id
        return f"<User(id={self.id}, identifier={identifier}, is_guest={self.is_guest})>"


class SavedRestaurant(Base):
    """SavedRestaurant model - stores user's saved restaurants."""
    __tablename__ = 'saved_restaurants'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    restaurant_id = Column(String(255), nullable=False, index=True)
    restaurant_data = Column(JSONB, nullable=False)  # Store full restaurant object as JSON
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship to user
    user = relationship('User', back_populates='saved_restaurants')

    def to_dict(self):
        """Convert saved restaurant to dictionary."""
        return {
            'id': self.id,
            'user_id': str(self.user_id),  # Convert UUID to string for JSON
            'restaurant_id': self.restaurant_id,
            'restaurant_data': self.restaurant_data,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f"<SavedRestaurant(id={self.id}, user_id={self.user_id}, restaurant_id={self.restaurant_id})>"
