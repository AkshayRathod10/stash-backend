class ReadReplicaRouter:
    READ_DB = 'replica'
    WRITE_DB = 'default'

    def db_for_read(self, model, **hints):
        return self.READ_DB

    def db_for_write(self, model, **hints):
        return self.WRITE_DB

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return db == self.WRITE_DB