import os

from sqlalchemy import create_engine, Column, Integer, String, Text, Float, ForeignKey, DateTime, func, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from typing import Optional
from pydantic import BaseModel

# DATABASE_USER = os.environ.get('DATABASE_USER')
# DATABASE_PASSWORD = os.environ.get('DATABASE_PASSWORD')
# DATABASE_HOST = os.environ.get('DATABASE_HOST')
# DATABASE = os.environ.get('DATABASE')
DATABASE_HOST = 'localhost'
DATABASE_USER = 'forsit'
DATABASE_PASSWORD = 'forsit1'
DATABASE = 'forsit'

DATABASE_URL = f"mysql+mysqlconnector://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}/{DATABASE}"
engine = create_engine(DATABASE_URL)

Base = declarative_base()


class Category(Base):
    __tablename__ = "category"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cat_name = Column(String(200), nullable=False)
    cat_description = Column(Text, nullable=True)

    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "product"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_name = Column(String(200), nullable=False)
    sku = Column(String(200), nullable=False, unique=True)
    price = Column(Float, nullable=False)
    category_id = Column(Integer, ForeignKey("category.id"), nullable=False)

    category = relationship("Category", back_populates="products")
    inventory = relationship("Inventory", back_populates="product")
    sales = relationship("Sale", back_populates="product")
    inventory_status = relationship("InventoryStatus", back_populates="product")


class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("product.id"), nullable=False)
    stock = Column(Integer, nullable=False, default=0)

    product = relationship("Product", back_populates="inventory")


class InventoryStatus(Base):
    __tablename__ = "inventory_status"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("product.id"), nullable=False)
    operation = Column(String(200), nullable=False)
    pieces = Column(Integer, nullable=False)
    operation_date = Column(DateTime, nullable=False, server_default=func.now())

    product = relationship("Product", back_populates="inventory_status")


class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("product.id"), nullable=False)
    price_per_piece = Column(Float, nullable=False)
    pieces = Column(Integer, nullable=False)
    sale_time = Column(DateTime, nullable=False, server_default=func.now())

    product = relationship("Product", back_populates="sales")


# Create tables in the database
Base.metadata.create_all(bind=engine)

# Create a Session class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
