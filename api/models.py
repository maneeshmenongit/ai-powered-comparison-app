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

    # Relationship to trips
    trips = relationship(
        'Trip',
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

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    restaurant_id = Column(String(255), nullable=False, index=True)
    restaurant_data = Column(JSONB, nullable=False)  # Store full restaurant object as JSON
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship to user
    user = relationship('User', back_populates='saved_restaurants')

    def to_dict(self):
        """Convert saved restaurant to dictionary."""
        return {
            'id': str(self.id),  # Convert UUID to string for JSON
            'user_id': str(self.user_id),  # Convert UUID to string for JSON
            'restaurant_id': self.restaurant_id,
            'restaurant_data': self.restaurant_data,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f"<SavedRestaurant(id={self.id}, user_id={self.user_id}, restaurant_id={self.restaurant_id})>"


class Trip(Base):
    """Trip model - stores user's trip plans (registered users only)."""
    __tablename__ = 'trips'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship to user
    user = relationship('User', back_populates='trips')

    # Relationship to trip items
    items = relationship(
        'TripItem',
        back_populates='trip',
        cascade='all, delete-orphan',
        order_by='TripItem.item_order'
    )

    def to_dict(self):
        """Convert trip to dictionary."""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'name': self.name,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'items': [item.to_dict() for item in self.items] if self.items else []
        }

    def __repr__(self):
        return f"<Trip(id={self.id}, user_id={self.user_id}, name={self.name})>"


class TripItem(Base):
    """TripItem model - stores items within a trip (restaurants, rides, activities)."""
    __tablename__ = 'trip_items'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trip_id = Column(UUID(as_uuid=True), ForeignKey('trips.id', ondelete='CASCADE'), nullable=False, index=True)
    item_type = Column(String(50), nullable=False)  # 'restaurant', 'ride', 'activity'
    item_data = Column(JSONB, nullable=False)  # Store full item object as JSON
    item_order = Column(Integer, nullable=False, default=0)  # Order in the trip timeline
    scheduled_time = Column(DateTime, nullable=True)  # When this item is scheduled
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship to trip
    trip = relationship('Trip', back_populates='items')

    def to_dict(self):
        """Convert trip item to dictionary."""
        return {
            'id': str(self.id),
            'trip_id': str(self.trip_id),
            'item_type': self.item_type,
            'item_data': self.item_data,
            'item_order': self.item_order,
            'scheduled_time': self.scheduled_time.isoformat() if self.scheduled_time else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f"<TripItem(id={self.id}, trip_id={self.trip_id}, type={self.item_type})>"
