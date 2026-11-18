from app import create_app
from app.models.employee import Employee
from app.models.user import User

app = create_app()
with app.app_context():
    emp1 = Employee.query.filter_by(staff_number='FGN/EDU/2018/00125').first()
    print('emp1 passport_photo_path:', emp1.passport_photo_path)
    print('emp1 passport_url:', emp1.passport_url)
    u = User.query.filter_by(username='adebayo.olumide').first()
    print('u avatar_path:', u.avatar_path)
    print('u avatar_url:', u.avatar_url)
