from app import db


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False, index=True)
    parent_id = db.Column(db.Integer, db.ForeignKey("categories.id"))
    image_path = db.Column(db.String(500))

    parent = db.relationship("Category", remote_side=[id], backref="children")
    products = db.relationship("Product", back_populates="category")

    def breadcrumb(self):
        trail = [self]
        current = self.parent
        while current:
            trail.insert(0, current)
            current = current.parent
        return trail

    @property
    def all_descendant_ids(self):
        ids = [self.id]
        for child in self.children:
            ids.extend(child.all_descendant_ids)
        return ids
