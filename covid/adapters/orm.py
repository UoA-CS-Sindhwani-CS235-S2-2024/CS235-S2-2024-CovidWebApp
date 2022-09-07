from sqlalchemy import (
    Table, MetaData, Column, Integer, String, Date, DateTime,
    ForeignKey
)
from sqlalchemy.orm import mapper, relationship, synonym

from covid.domain import model

# global variable giving access to the MetaData (schema) information of the database
metadata = MetaData()

users_table = Table(
    'users', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('user_name', String(255), unique=True, nullable=False),
    Column('password', String(255), nullable=False)
)

comments_table = Table(
    'comments', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('user_id', ForeignKey('users.id')),
    Column('article_id', ForeignKey('articles.id')),
    Column('comment', String(1024), nullable=False),
    Column('timestamp', DateTime, nullable=False)
)

articles_table = Table(
    'articles', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('date', Date, nullable=False),
    Column('title', String(255), nullable=False),
    Column('first_paragraph', String(1024), nullable=False),
    Column('hyperlink', String(255), nullable=False),
    Column('image_hyperlink', String(255), nullable=False)
)

tags_table = Table(
    'tags', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('tag_name', String(64), nullable=False)
)

article_tags_table = Table(
    'article_tags', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('article_id', ForeignKey('articles.id')),
    Column('tag_id', ForeignKey('tags.id'))
)

def map_model_to_tables():
    mapper(model.User, users_table, properties={
        '_User__user_name': users_table.c.user_name,
        '_User__password': users_table.c.password,
        '_User__comments': relationship(model.Comment, backref='_Comment__user')
    })
    mapper(model.Comment, comments_table, properties={
        '_Comment__comment': comments_table.c.comment,
        '_Comment__timestamp': comments_table.c.timestamp
    })
    mapper(model.Article, articles_table, properties={
        '_Article__id': articles_table.c.id,
        '_Article__date': articles_table.c.date,
        '_Article__title': articles_table.c.title,
        '_Article__first_paragraph': articles_table.c.first_paragraph,
        '_Article__hyperlink': articles_table.c.hyperlink,
        '_Article__image_hyperlink': articles_table.c.image_hyperlink,
        '_Article__comments': relationship(model.Comment, backref='_Comment__article'),
        '_Article__tags': relationship(model.Tag, secondary=article_tags_table,
                                       back_populates='_Tag__tagged_articles')
    })
    mapper(model.Tag, tags_table, properties={
        '_Tag__tag_name': tags_table.c.tag_name,
        '_Tag__tagged_articles': relationship(
            model.Article,
            secondary=article_tags_table,
            back_populates="_Article__tags"
        )
    })

