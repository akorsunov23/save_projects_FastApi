from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import declarative_base, relationship

engine = create_engine('sqlite:///database.db')
async_engine = create_async_engine('sqlite+aiosqlite:///database.db')

Base = declarative_base()


class User(Base):
    """Модель, описывающая пользователя."""

    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    password = Column(String, nullable=False)
    projects = relationship('Project', back_populates='user')


class Project(Base):
    """Модель, описывающая проект пользователя."""

    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship('User', back_populates='projects')
    images = relationship('Image', back_populates='project')


class Image(Base):
    """Модель, описывающая изображения добавленные в проект пользователя."""

    __tablename__ = 'images'

    id = Column(Integer, primary_key=True, autoincrement=True)
    image_url = Column(String)
    project_id = Column(Integer, ForeignKey('projects.id'))
    project = relationship('Project', back_populates='images')


Base.metadata.create_all(bind=engine)
