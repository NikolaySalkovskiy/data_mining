from sqlalchemy.ext.declarative import declarative_base
import datetime as dt
from sqlalchemy.orm import relationship
from sqlalchemy import (
    Column,
    INTEGER,
    String,
    ForeignKey,
    DATETIME,
    BOOLEAN,
    Table
)

Base = declarative_base()

tag_post = Table(
    'tag_post',
    Base.metadata,
    Column('post_id', INTEGER, ForeignKey('post.id')),
    Column('tag_id', INTEGER, ForeignKey('tag.id'))
)


class Post(Base):
    __tablename__ = 'post'
    id = Column(INTEGER, primary_key=True, unique=True, nullable=False)
    url = Column(String(2048), nullable=False, unique=True)
    title = Column(String, nullable=False, unique=False)
    author_id = Column(INTEGER, ForeignKey('Author.id'), nullable=False)
    author = relationship('Author', backref='posts')
    tags = relationship('Tag', secondary=tag_post, backref='posts')


class Author(Base):
    __tablename__ = 'Author'
    id = Column(INTEGER, primary_key=True, autoincrement=True)
    url = Column(String(2048), nullable=False, unique=True)
    name = Column(String(250), nullable=False, unique=False)
    gb_id = Column(INTEGER, nullable=True, unique=True)


class Tag(Base):
    __tablename__ = 'tag'
    id = Column(INTEGER, primary_key=True, autoincrement=True)
    url = Column(String(2048), nullable=False, unique=True)
    name = Column(String(150), nullable=False)


class Comment(Base):
    __tablename__ = 'comment'
    id = Column(INTEGER, primary_key=True)
    parent_id = Column(INTEGER, ForeignKey("comment.id"), nullable=True)
    body = Column(String)
    created_at = Column(DATETIME, nullable=False)
    hidden = Column(BOOLEAN)
    author_id = Column(INTEGER, ForeignKey('Author.id'))
    author = relationship("Author", backref="comments")
    post_id = Column(INTEGER, ForeignKey('post.id'))
    post = relationship('Post', backref='comments')

    def __init__(self, **kwargs):
        self.id = kwargs["id"]
        self.parent_id = kwargs["parent_id"]
        self.body = kwargs["body"]
        self.created_at = dt.datetime.fromisoformat(kwargs["created_at"])
        self.hidden = kwargs["hidden"]
