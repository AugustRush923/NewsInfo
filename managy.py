from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from info import create_app, db, models

app = create_app('development')

# Flask-script
manager = Manager(app)
# 数据库迁移
Migrate(app, db)
manager.add_command('db', MigrateCommand)


@manager.option('-u', '-username', dest="username")
@manager.option('-p', '-password', dest="password")
def createsuperuser(username, password):
    if not all([username, password]):
        print("请输入用户名或密码")
        return
    user = models.User()
    user.mobile = username
    user.nick_name = username
    user.password_hash = user.sha1_passowrd(password)
    user.is_admin = True

    try:
        db.session.add(user)
        db.session.commit()
        print("创建成功")
    except Exception as e:
        print(e)
        db.session.rollback()


if __name__ == '__main__':
    manager.run()
