from .base_entity_model import BaseModel, store


class UploadedImage(BaseModel):
    table = "uploaded_image"
    fields = [
        "id",
        "user_id",
        "image",
        "letters",
        "create_time",
        "update_time"
    ]

    def gets_by_user_id(self, user_id, page, page_size):
        sql = "select id from {} where user_id=%s limit %s %s"
        res = store.execute(sql, self.table, user_id, page_size, page * page_size)
        return [r[0] for r in res] if res else []

    def to_dict(self):
        data = self.to_base_dict()
        return data


class User(BaseModel):
    table = "user"

    fields = [
        "id",
        "username",
        "password",
        "salt",
        "create_time",
        "update_time"
    ]
