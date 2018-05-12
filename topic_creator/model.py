"""
SQLAlchemy example

Define some tables using the sqlalchemy declarative ORM.
Insert some data to the tables.
Create a 1-n relationship.
Create an n-n relationship.
"""
import hashlib
from sqlalchemy import create_engine
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy import ForeignKey, Table
from sqlalchemy.sql import func
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import IntegrityError

def hash(value):
    md5 = hashlib.md5()
    md5.update(value)
    return md5.hexdigest()

class UsernameTaken(Exception):
    pass

Base = declarative_base()

vote_table = Table(
    "user_topic",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("user.id")),
    Column("topic_id", Integer, ForeignKey("topic.id")),
)

class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    email = Column(String)
    passwd = Column(String)
    topics = relationship("Topic", back_populates="author")
    voted_on = relationship("Topic", back_populates="voted_by", secondary=vote_table)

    def __init__(self, username, email='', passwd=''):
        self.username = username
        self.email = email
        self.passwd = hash(passwd)

    def __repr__(self):
        return "<User(id={self.id}, " \
               "username='{self.username}', " \
               "email='{self.email}', " \
               "passwd='{self.passwd}')>".format(self=self)

    @classmethod
    def create(cls, session, username):
        try:
            user = cls(username)
            session.add(user)
            session.commit()
            return user
        except IntegrityError as e:
            session.rollback()
            if "UNIQUE constraint failed: user.username" in e.message:
                raise UsernameTaken()
            else:
                raise e

    @classmethod
    def get_by_id(cls, session, id_):
        return session.query(cls).filter_by(id=id_).one()

    @classmethod
    def get_by_username(cls, session, username):
        return session.query(cls).filter_by(username=username).first()

class Topic(Base):
    __tablename__ = "topic"
    id = Column(Integer, primary_key=True)
    description = Column(String)
    post_date = Column(DateTime, default=func.now())
    author_id = Column(Integer, ForeignKey("user.id"))
    author = relationship("User", back_populates="topics")
    votes = Column(Integer, default=0)
    voted_by = relationship("User", back_populates="voted_on", secondary=vote_table)

    def __init__(self, description):
        self.description = description

    def __repr__(self):
        return "<Topic(id={self.id}, " \
               "author_id={self.author_id}, " \
               "votes={self.votes}, " \
               "post_date='{self.post_date}', " \
               "description='{self.description}')>".format(self=self)

    def upvote(self, session, user):
        if user not in self.voted_by:
            self.votes += 1
            self.voted_by.append(user)
            session.commit()

    @classmethod
    def get_by_id(cls, session, id_):
        return session.query(cls).filter_by(id=id_).one()

    @classmethod
    def create(cls, session, user, description):
        topic = cls(description)
        topic.author = user
        session.add(topic)
        session.commit()
        return topic


engine = create_engine("sqlite:///topics.db", echo=False)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
