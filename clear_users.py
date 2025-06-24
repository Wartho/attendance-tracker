from flask.cli import with_appcontext
import click
from app import db
from app.models import User

@click.command('clear-users')
@with_appcontext
def clear_users():
    """Clear all users from the database."""
    # Delete all users
    User.query.delete()
    db.session.commit()
    click.echo('All users have been cleared from the database.')

if __name__ == '__main__':
    clear_users() 