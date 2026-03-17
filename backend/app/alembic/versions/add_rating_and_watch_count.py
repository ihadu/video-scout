"""
Add rating and watch_count fields
"""

from sqlalchemy import Column, Integer, DateTime, func

from app.core.database import Base


def upgrade():
    # Add rating column to favorites table
    op.add_column('favorites', Column('rating', Integer, default=0, nullable=True))
    
    # Add watch_count and last_watched_at to videos table
    op.add_column('videos', Column('watch_count', Integer, default=0, nullable=False))
    op.add_column('videos', Column('last_watched_at', DateTime(timezone=True), nullable=True))


def downgrade():
    # Remove columns
    op.drop_column('videos', 'last_watched_at')
    op.drop_column('videos', 'watch_count')
    op.drop_column('favorites', 'rating')
