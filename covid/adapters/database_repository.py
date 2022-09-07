from datetime import date
from typing import List

from sqlalchemy import desc, asc
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from sqlalchemy.orm import scoped_session
from flask import _app_ctx_stack

from covid.domain.model import User, Article, Comment, Tag
from covid.adapters.repository import AbstractRepository


class SessionContextManager:
    def __init__(self, session_factory):
        self.__session_factory = session_factory
        self.__session = scoped_session(self.__session_factory, scopefunc=_app_ctx_stack.__ident_func__)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.rollback()

    @property
    def session(self):
        return self.__session

    def commit(self):
        self.__session.commit()

    def rollback(self):
        self.__session.rollback()

    def reset_session(self):
        # this method can be used e.g. to allow Flask to start a new session for each http request,
        # via the 'before_request' callback
        self.close_current_session()
        self.__session = scoped_session(self.__session_factory, scopefunc=_app_ctx_stack.__ident_func__)

    def close_current_session(self):
        if not self.__session is None:
            self.__session.close()


class SqlAlchemyRepository(AbstractRepository):

    def __init__(self, session_factory):
        self._session_cm = SessionContextManager(session_factory)

    def close_session(self):
        self._session_cm.close_current_session()

    def reset_session(self):
        self._session_cm.reset_session()

    def add_user(self, user: User):
        with self._session_cm as scm:
            scm.session.add(user)
            scm.commit()

    def get_user(self, user_name: str) -> User:
        user = None
        try:
            user = self._session_cm.session.query(User).filter(User._User__user_name == user_name).one()
        except NoResultFound:
            # Ignore any exception and return None.
            pass

        return user

    def add_article(self, article: Article):
        with self._session_cm as scm:
            scm.session.add(article)
            scm.commit()

    def get_article(self, id: int) -> Article:
        article = None
        try:
            article = self._session_cm.session.query(Article).filter(Article._Article__id == id).one()
        except NoResultFound:
            # Ignore any exception and return None.
            pass

        return article

    def get_articles_by_date(self, target_date: date) -> List[Article]:
        if target_date is None:
            articles = self._session_cm.session.query(Article).all()
            return articles
        else:
            # Return articles matching target_date; return an empty list if there are no matches.
            articles = self._session_cm.session.query(Article).filter(Article._Article__date == target_date).all()
            return articles

    def get_number_of_articles(self):
        number_of_articles = self._session_cm.session.query(Article).count()
        return number_of_articles

    def get_first_article(self):
        article = self._session_cm.session.query(Article).first()
        return article

    def get_last_article(self):
        article = self._session_cm.session.query(Article).order_by(desc(Article._Article__id)).first()
        return article

    def get_articles_by_id(self, id_list: List[int]):
        articles = self._session_cm.session.query(Article).filter(Article._Article__id.in_(id_list)).all()
        return articles

    def get_article_ids_for_tag(self, tag_name: str):
        article_ids = []

        # Use native SQL to retrieve article ids, since there is no mapped class for the article_tags table.
        row = self._session_cm.session.execute('SELECT id FROM tags WHERE tag_name = :tag_name', {'tag_name': tag_name}).fetchone()

        if row is None:
            # No tag with the name tag_name - create an empty list.
            article_ids = list()
        else:
            tag_id = row[0]
            # Retrieve article ids of articles associated with the tag.
            article_ids = self._session_cm.session.execute(
                    'SELECT article_id FROM article_tags WHERE tag_id = :tag_id ORDER BY article_id ASC',
                    {'tag_id': tag_id}
            ).fetchall()
            article_ids = [id[0] for id in article_ids]

        return article_ids

    def get_date_of_previous_article(self, article: Article):
        result = None
        prev_article = self._session_cm.session.query(Article).filter(Article._Article__date < article.date).order_by(desc(Article._Article__date)).first()

        if prev_article is not None:
            result = prev_article.date

        return result

    def get_date_of_next_article(self, article: Article):
        result = None
        next_article = self._session_cm.session.query(Article).filter(Article._Article__date > article.date).order_by(asc(Article._Article__date)).first()

        if next_article is not None:
            result = next_article.date

        return result

    def get_tags(self) -> List[Tag]:
        tags = self._session_cm.session.query(Tag).all()
        return tags

    def add_tag(self, tag: Tag):
        with self._session_cm as scm:
            scm.session.add(tag)
            scm.commit()

    def get_comments(self) -> List[Comment]:
        comments = self._session_cm.session.query(Comment).all()
        return comments

    def add_comment(self, comment: Comment):
        super().add_comment(comment)
        with self._session_cm as scm:
            scm.session.add(comment)
            scm.commit()
