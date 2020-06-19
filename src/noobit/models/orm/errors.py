from tortoise import fields, Model


class ErrorLog(Model):

    json = fields.JSONField()
    stack = fields.TextField()