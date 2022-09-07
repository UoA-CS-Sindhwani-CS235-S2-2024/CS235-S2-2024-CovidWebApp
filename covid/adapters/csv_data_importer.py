import csv
from pathlib import Path
from datetime import date, datetime

from werkzeug.security import generate_password_hash

from covid.adapters.repository import AbstractRepository
from covid.domain.model import Article, Tag, User, make_tag_association, make_comment, ModelException


def read_csv_file(filename: str):
    with open(filename, encoding='utf-8-sig') as infile:
        reader = csv.reader(infile)

        # Read first line of the the CSV file.
        headers = next(reader)

        # Read remaining rows from the CSV file.
        for row in reader:
            # Strip any leading/trailing white space from data read.
            row = [item.strip() for item in row]
            yield row


def load_articles_and_tags(data_path: Path, repo: AbstractRepository, database_mode: bool):
    tags = dict()

    articles_filename = str(data_path / "news_articles.csv")
    for data_row in read_csv_file(articles_filename):

        article_key = int(data_row[0])
        number_of_tags = len(data_row) - 6
        article_tags = data_row[-number_of_tags:]

        # Add any new tags; associate the current article with tags.
        for tag in article_tags:
            if tag not in tags.keys():
                tags[tag] = list()
            tags[tag].append(article_key)
        del data_row[-number_of_tags:]

        # Create Article object.
        article = Article(
            date=date.fromisoformat(data_row[1]),
            title=data_row[2],
            first_paragraph=data_row[3],
            hyperlink=data_row[4],
            image_hyperlink=data_row[5],
            id=article_key
        )

        # Add the Article to the repository.
        repo.add_article(article)

    # Create Tag objects, associate them with Articles and add them to the repository.
    for tag_name in tags.keys():
        tag = Tag(tag_name)
        for article_id in tags[tag_name]:
            article = repo.get_article(article_id)
            if database_mode is True:
                # the ORM takes care of the association between articles and tags
                article.add_tag(tag)
            else:
                make_tag_association(article, tag)
        repo.add_tag(tag)


def load_users(data_path: Path, repo: AbstractRepository):
    users = dict()

    users_filename = str(Path(data_path) / "users.csv")
    for data_row in read_csv_file(users_filename):
        user = User(
            user_name=data_row[1],
            password=generate_password_hash(data_row[2])
        )
        repo.add_user(user)
        users[data_row[0]] = user
    return users


def load_comments(data_path: Path, repo: AbstractRepository, users):
    comments_filename = str(Path(data_path) / "comments.csv")
    for data_row in read_csv_file(comments_filename):
        comment = make_comment(
            comment_text=data_row[3],
            user=users[data_row[1]],
            article=repo.get_article(int(data_row[2])),
            timestamp=datetime.fromisoformat(data_row[4])
        )
        repo.add_comment(comment)