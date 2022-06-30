import uuid as uuid_pkg


class ContentId:
    content_id: uuid_pkg.UUID

    def __init__(self, content_id: uuid_pkg.UUID):
        self.content_id = content_id

    def to_string(self):
        return f"ContentId{{contentId={self.content_id}}}"

    def __str__(self):
        return self.to_string()

    def __eq__(self, other):
        if not isinstance(other, ContentId):
            return False
        return self.content_id is not None and str(self.content_id) == other.content_id
