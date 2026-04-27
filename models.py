from typing import Optional, List
from datetime import datetime
from uuid import uuid4

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash


db = SQLAlchemy()


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    fullname: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean(), default=False)

    reservations: Mapped[List["Reservation"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )

    orders: Mapped[List["Order"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = uuid4().hex

    def set_password(self, raw_password: str):
        self.password_hash = generate_password_hash(raw_password)

   
    @property
    def password(self):
        raise AttributeError("Не можна читати пароль")

    @password.setter
    def password(self, raw_password: str):
        self.password_hash = generate_password_hash(raw_password)

    def verify_password(self, raw_password: str):
        return check_password_hash(self.password_hash, raw_password)

    def get_id(self):
        return self.id


class Menu(db.Model):
    __tablename__ = "menu"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000))
    weight: Mapped[Optional[float]] = mapped_column(nullable=True)
    ingredients: Mapped[Optional[str]] = mapped_column(String(500))
    price: Mapped[float] = mapped_column(nullable=False)
    active: Mapped[bool] = mapped_column(Boolean(), default=True)
    picture: Mapped[Optional[str]] = mapped_column(String(500))
    category: Mapped[str] = mapped_column(String(50))

    order_items: Mapped[List["OrderItem"]] = relationship(
        back_populates="menu_item",
        cascade="all, delete-orphan"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = uuid4().hex


class Reservation(db.Model):
    __tablename__ = "reservations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    time_start: Mapped[datetime] = mapped_column(DateTime(), nullable=False)
    table: Mapped[Optional[str]] = mapped_column(String(100))

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    user: Mapped["User"] = relationship(back_populates="reservations")

    orders: Mapped[List["Order"]] = relationship(
        back_populates="reservation",
        cascade="all, delete-orphan"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = uuid4().hex


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    menu_id: Mapped[str] = mapped_column(ForeignKey("menu.id", ondelete="CASCADE"))
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    quantity: Mapped[int] = mapped_column(default=1)

    menu_item: Mapped["Menu"] = relationship(back_populates="order_items")
    order: Mapped["Order"] = relationship(back_populates="order_items")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = uuid4().hex


class Order(db.Model):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    order_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    reservation_id: Mapped[str] = mapped_column(ForeignKey("reservations.id", ondelete="CASCADE"), nullable=True)

    order_items: Mapped[List["OrderItem"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan"
    )

    user: Mapped["User"] = relationship(back_populates="orders")
    reservation: Mapped["Reservation"] = relationship(back_populates="orders")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = uuid4().hex