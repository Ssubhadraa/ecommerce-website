from alembic import op
import sqlalchemy as sa


revision = "a1b2c3d4e5f6"
down_revision = "bcf63ba1ec91"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "wishlist_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("added_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "product_id", name="uq_wishlist_user_product"),
    )
    with op.batch_alter_table("wishlist_items", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_wishlist_items_user_id"), ["user_id"], unique=False)


def downgrade():
    with op.batch_alter_table("wishlist_items", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_wishlist_items_user_id"))

    op.drop_table("wishlist_items")
