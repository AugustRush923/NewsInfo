from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from info import create_app, db

# Flask-script
manager = Manager(create_app)
# 数据库迁移
Migrate(create_app, db)
manager.add_command('db', MigrateCommand)

app = create_app('development')

@app.route('/index')
def index():
    return 'index'


if __name__ == '__main__':
    manager.run()
