from datetime import date
from typing import List

from bisect import bisect, bisect_left, insort_left

from covid.adapters.repository import AbstractRepository, RepositoryException
from covid.domain.model import Article, Tag, User, Comment


class MemoryRepository(AbstractRepository):
    # Articles ordered by date, not id. id is assumed unique.

    def __init__(self):
        self.__articles = list()
        self.__articles_index = dict()
        self.__tags = list()
        self.__users = list()
        self.__comments = list()

    def add_user(self, user: User):
        self.__users.append(user)

    def get_user(self, user_name) -> User:
        return next((user for user in self.__users if user.user_name == user_name), None)

    def add_article(self, article: Article):
        insort_left(self.__articles, article)
        self.__articles_index[article.id] = article

    def get_article(self, id: int) -> Article:
        article = None

        try:
            article = self.__articles_index[id]
        except KeyError:
            pass  # Ignore exception and return None.

        return article

    def get_articles_by_date(self, target_date: date) -> List[Article]:
        target_article = Article(
            date=target_date,
            title=None,
            first_paragraph=None,
            hyperlink=None,
            image_hyperlink=None
        )
        matching_articles = list()

        try:
            index = self.article_index(target_article)
            for article in self.__articles[index:None]:
                if article.date == target_date:
                    matching_articles.append(article)
                else:
                    break
        except ValueError:
            # No articles for specified date. Simply return an empty list.
            pass

        return matching_articles

    def get_number_of_articles(self):
        return len(self.__articles)

    def get_first_article(self):
        article = None

        if len(self.__articles) > 0:
            article = self.__articles[0]
        return article

    def get_last_article(self):
        article = None

        if len(self.__articles) > 0:
            article = self.__articles[-1]
        return article

    def get_articles_by_id(self, id_list):
        # Strip out any ids in id_list that don't represent Article ids in the repository.
        existing_ids = [id for id in id_list if id in self.__articles_index]

        # Fetch the Articles.
        articles = [self.__articles_index[id] for id in existing_ids]
        return articles

    def get_article_ids_for_tag(self, tag_name: str):
        # Linear search, to find the first occurrence of a Tag with the name tag_name.
        tag = next((tag for tag in self.__tags if tag.tag_name == tag_name), None)

        # Retrieve the ids of articles associated with the Tag.
        if tag is not None:
            article_ids = [article.id for article in tag.tagged_articles]
        else:
            # No Tag with name tag_name, so return an empty list.
            article_ids = list()

        return article_ids

    def get_date_of_previous_article(self, article: Article):
        previous_date = None

        try:
            index = self.article_index(article)
            for stored_article in reversed(self.__articles[0:index]):
                if stored_article.date < article.date:
                    previous_date = stored_article.date
                    break
        except ValueError:
            # No earlier articles, so return None.
            pass

        return previous_date

    def get_date_of_next_article(self, article: Article):
        next_date = None

        try:
            index = self.article_index(article)
            for stored_article in self.__articles[index + 1:len(self.__articles)]:
                if stored_article.date > article.date:
                    next_date = stored_article.date
                    break
        except ValueError:
            # No subsequent articles, so return None.
            pass

        return next_date

    def add_tag(self, tag: Tag):
        self.__tags.append(tag)

    def get_tags(self) -> List[Tag]:
        return self.__tags

    def add_comment(self, comment: Comment):
        # call parent class first, add_comment relies on implementation of code common to all derived classes
        super().add_comment(comment)
        self.__comments.append(comment)

    def get_comments(self):
        return self.__comments

    # Helper method to return article index.
    def article_index(self, article: Article):
        index = bisect_left(self.__articles, article)
        if index != len(self.__articles) and self.__articles[index].date == article.date:
            return index
        raise ValueError
