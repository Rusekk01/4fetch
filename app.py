from flask import Flask, render_template, url_for, request, redirect, blueprints, flash, abort, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_bootstrap import Bootstrap
from forms import LoginForm, RegisterForm
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, current_user, login_required, logout_user, UserMixin

app = Flask(__name__)
app.config["SECRET_KEY"] = '571ebf8e13ca209536c29be68d435c00'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:112233@localhost/4fetch'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

bootstrap = Bootstrap(app)
db = SQLAlchemy(app)


class User(UserMixin, db.Model):
    __tablename__ = 'User'
    idUser = db.Column(db.Integer(), primary_key=True, nullable=False)
    Name = db.Column(db.Text(), nullable=False)
    LastName = db.Column(db.Text(), nullable=False)
    Role = db.Column(db.Text(), db.CheckConstraint('''"Role" = 'User'::text OR "Role" = 'Admin'::text'''),
                     nullable=False)
    Email = db.Column(db.Text(), nullable=False)
    Username = db.Column(db.Text(), unique=True, nullable=False)
    Password = db.Column(db.Text(), nullable=False)
    orders = db.relationship('Order', backref='user', cascade='all,delete-orphan')  # связь с Order

    def __init__(self, name, lastname, role, email, username, password):
        self.Name = name
        self.LastName = lastname
        self.Role = role
        self.Email = email
        self.Username = username
        self.Password = password


class Cloth(db.Model):
    __tablename__ = 'Cloth'
    idCloth = db.Column(db.Integer(), primary_key=True, nullable=False)
    Name = db.Column(db.Text(), nullable=False)
    Image = db.Column(db.Text(), nullable=False)
    Description = db.Column(db.Text(), nullable=False)
    Price = db.Column(db.Integer(), db.CheckConstraint('''"Price" >= 0'''), nullable=False)
    Gender = db.Column(db.Text(), db.CheckConstraint('''"Gender" = 'f'::text or "Gender" = 'm'::text'''),
                       nullable=False)
    Status = db.Column(db.Text(),
                       db.CheckConstraint('''"Status" = 'available'::text or "Status" = 'not available'::text'''),
                       default='available')
    Colour = db.Column(db.Text(), nullable=False)
    orderitems = db.relationship('OrderItem', backref='cloth', cascade='all,delete-orphan')  # связь с OrderItem

    def __init__(self, name, image, description, price, gender, colour):
        self.Name = name
        self.Image = image
        self.Description = description
        self.Price = price
        self.Gender = gender
        self.Colour = colour


class Order(db.Model):
    __tablename__ = 'Order'
    idOrder = db.Column(db.Integer(), primary_key=True, nullable=False)
    idUser = db.Column(db.Integer(), db.ForeignKey('User.idUser'), nullable=False)  # внешний ключ с User
    TotalPrice = db.Column(db.Integer(), db.CheckConstraint('''"TotalPrice" >= 0'''), nullable=False)
    Status = db.Column(db.Text(), nullable=False)
    Address = db.Column(db.Text(), nullable=False)
    Reciever = db.Column(db.Text(), nullable=False)
    orderitems = db.relationship('OrderItem', backref='order', cascade='all,delete-orphan')  # связь с OrderItem

    def __init__(self, iduser, totalprice, status, address, reciever):
        self.idUser = iduser
        self.TotalPrice = totalprice
        self.Status = status
        self.Address = address
        self.Reciever = reciever


class OrderItem(db.Model):
    RowId = db.Column(db.Integer(), primary_key=True, nullable=False)
    idOrder = db.Column(db.Integer(), db.ForeignKey('Order.idOrder'), nullable=False)  # внешний ключ с Order
    idCloth = db.Column(db.Integer(), db.ForeignKey('Cloth.idCloth'), nullable=False)  # внешний ключ с Cloth
    Size = db.Column(db.Integer(), nullable=False)
    Number = db.Column(db.Integer(), db.CheckConstraint('''"Number" >= 0'''), nullable=False)

    def __init__(self, idorder, idcloth, size, number):
        self.idOrder = idorder
        self.idCloth = idcloth
        self.Size = size
        self.Number = number


# db.create_all()
# db.drop_all()

# u1 = User('LEXA', 'Pivlov', 'User', 'hehpavlov2@gmail.com', 'Y2', '322')
# o1 = Order('2', '15', 'доставлено', 'дом пушкина улица колотушкина', 'алексей павлов')
# u2 = User('Alexey', 'Pavlov', 'Admin', 'hehpavlov1@gmail.com', 'Y1', '222')
# o2 = OrderItem('4', '5', '10', 'R', '3')
# o3 = OrderItem('4', '6', '10', 'R', '3')
# o4 = OrderItem('4', '7', '10', 'R', '3')
# db.session.add_all([o2, o3, o4])
# AAA = User.query.filter_by(id=4).first()
# BBB = Cloth.query.filter_by(idCloth=6).first()
# db.session.delete(AAA)
# db.session.commit()

@app.route('/')
@app.route('/home')
def index():  # put application's code here
    items = Cloth.query.all()
    if 'loggedIn' in session:
        if session['loggedIn']:
            return render_template('index.html', session=session, items=items)  # Подгрузить новую шапку
    else:
        session['loggedIn'] = False
        session.modified = True
    return render_template("index.html", items=items)


@app.route('/search')
def search():
    query = request.args['query']
    search = "%{}%".format(query)
    items = Cloth.query.filter(Cloth.Name.like(search)).all()
    return render_template('index.html', items=items, search=True, query=query)


@app.route('/about')
def about():  # put application's code here
    return render_template("about.html")


@app.route("/cabinet/<int:id>", methods=['POST', 'GET'])
def cabinet(id):  # put application's code here
    user = User.query.filter_by(idUser=id).first()
    return render_template("cabinet.html", session=session, user=user)


@app.route("/register", methods=['POST', 'GET'])
def register():  # put application's code here
    if request.method == "POST":
        session['loggedIn'] = False
        session.modified = True
        Name = request.form['name']
        LastName = request.form['last-name']
        Email = request.form['email']
        Username = request.form['username']
        Password = request.form['password']
        Role = 'User'
        if User.query.filter_by(Username=Username).first() is not None:
            flash("Такой никнейм уже занят, попробуйте другой")
            return redirect('/register')
        user = User(name=Name, lastname=LastName, role=Role, email=Email, username=Username, password=Password)
        try:
            db.session.add(user)
            db.session.commit()
            session['loggedIn'] = True
            session['userID'] = user.idUser
            if user.Role == 'Admin':
                session['isAdmin'] = True
            session.modified = True
            return redirect('/')
        except:
            return "Error"
    else:
        return render_template("register.html")


@app.route("/login", methods=['POST', 'GET'])
def login():  # put application's code here
    if request.method == 'POST':
        Username = request.form['username']
        Password = request.form['password']
        get_data = User.query.filter_by(Username=Username).first()
        if User.query.filter_by(Username=Username).first() is not None:
            if Username == get_data.Username and Password == get_data.Password:
                print('Logged In!!!')
                session['loggedIn'] = True
                session['userID'] = get_data.idUser
                print(session['userID'])
                if get_data.Role == 'Admin':
                    session['isAdmin'] = True
                session.modified = True
                return redirect('/')
        flash('Вы ввели неверный логин или пароль, попробуйте ещё раз')
        return redirect('/login')
    else:
        if 'loggedIn' in session:
            if session['loggedIn']:
                return redirect('/')
        else:
            session['loggedIn'] = False
            session.modified = True
    return render_template("login.html")


@app.route('/order/<int:id>', methods=['POST', 'GET'])
def order(id):  # put application's code here
    user = User.query.filter_by(idUser=id).first()
    orders = user.orders
    get_data = Order.query.filter_by(Status='создается').first()
    orderitems = Order.orderitems

    return render_template("order.html", User=user, Orders=orders, OrderItems=orderitems)


@app.route("/create", methods=['POST', 'GET'])
def create():  # put application's code here
    if request.method == "POST":
        Name = request.form['item-name']
        Image = request.form['image']
        Description = request.form['description']
        print(Description)
        Price = request.form.get('price', type=int)
        Gender = request.form['gender']
        Colour = request.form['colour']

        Item = Cloth(name=Name, image=Image, description=Description, price=Price, gender=Gender, colour=Colour)

        try:
            db.session.add(Item)
            db.session.commit()
            return redirect('/')
        except:
            return "Error"
    else:
        return render_template("create.html")


@app.route('/item/<int:id>', methods=['GET'])
def itempage(id):  # put application's code here
    item = Cloth.query.get(id)
    return render_template("item_page.html", Cloth=item)


@app.route("/logout")
def logout():  # put application's code here
    session['loggedIn'] = False
    session['isAdmin'] = False
    session.modified = True
    return redirect("/")


@app.route("/delete/<int:id>", methods=['POST', 'GET'])
def delete(id):  # put application's code here
    item = Cloth.query.get(id)
    item.Status = 'not available'
    db.session.add(item)
    db.session.commit()
    return redirect('/item/' + str(id))


@app.route("/delete_item/<int:id>", methods=['POST', 'GET'])
def delete_item(id):  # put application's code here
    item = Cloth.query.get(id)
    db.session.delete(item)
    db.session.commit()
    return redirect('/')


@app.route("/restore/<int:id>", methods=['POST', 'GET'])
def restore(id):  # put application's code here
    item = Cloth.query.get(id)
    item.Status = 'available'
    db.session.add(item)
    db.session.commit()
    return redirect('/item/' + str(id))


@app.route("/delete_order/<int:id>", methods=['POST', 'GET'])
def delete_order(id):  # put application's code here
    item = Order.query.get(id)
    db.session.delete(item)
    db.session.commit()
    user = User.query.filter_by(idUser=session['userID']).first()
    orders = user.orders
    if session["isAdmin"]:
        return redirect('/all_orders')
    else:
        return redirect('/order/' + str(session['userID']))


@app.route("/delete_item_from_order/<int:id>", methods=['POST', 'GET'])
def delete_item_from_order(id):  # put application's code here
    item = OrderItem.query.filter_by(RowId=id).first()
    print(id)
    order1 = item.order.orderitems
    if len(order1) == 1:
        id1 = item.order.idOrder
        item = Order.query.get(id1)
        db.session.delete(item)
        db.session.commit()
        user = User.query.filter_by(idUser=session['userID']).first()
        orders = user.orders
        if session["isAdmin"]:
            return redirect('/all_orders')
        else:
            return redirect('/order/' + str(session['userID']))
    else:
        item.order.TotalPrice -= item.cloth.Price * item.Number
        db.session.add(item.order)
        db.session.delete(item)
        db.session.commit()
        user = User.query.filter_by(idUser=session['userID']).first()
        orders = user.orders
        if session["isAdmin"]:
            return redirect('/all_orders')
        else:
            return redirect('/order/' + str(session['userID']))


@app.route("/pay/<int:id>", methods=['POST', 'GET'])
def pay(id):  # put application's code here
    if request.method == "POST":
        order1 = Order.query.filter_by(idUser=session['userID'], Status='создается').first()
        Address1 = request.form['address']
        Receiver1 = request.form['receiver']
        user = User.query.filter_by(idUser=session['userID']).first()
        orders = user.orders
        try:
            order1.Address = Address1
            order1.Reciever = Receiver1
            order1.Status = 'Создан'
            db.session.add(order1)
            db.session.commit()
            return redirect('/order/' + str(session['userID']))
        except:
            return redirect('/order/' + str(session['userID']))
    else:
        return render_template("pay_page.html")


@app.route("/all_orders", methods=['POST', 'GET'])
def all_orders():
    orders1 = Order.query.all()
    return render_template("all_orders.html", Orders=orders1)


@app.route("/change_status/<int:id>", methods=['POST', 'GET'])
def change_status(id):
    if request.method == "POST":
        order1 = Order.query.filter_by(idOrder=id).first()
        Address1 = request.form['address']
        Receiver1 = request.form['receiver']
        Status1 = request.form['status']
        print()
        if Address1 != '':
            order1.Address = Address1
        if Receiver1 != '':
            order1.Reciever = Receiver1
        if Status1 != '':
            order1.Status = Status1
        db.session.add(order1)
        db.session.commit()
        return redirect('/all_orders')
    else:
        order1 = Order.query.filter_by(idUser=session['userID']).first()
        return render_template("change_status.html", Order=order1)


@app.route("/all_users")
def all_users():
    users = User.query.all()
    return render_template("all_users.html", Users=users)


@app.route("/add_to_order/<int:id>", methods=['POST', 'GET'])
def add_to_order(id):  # put application's code here
    id_order = Order.query.filter_by(Status='создается', idUser=session['userID']).first()
    if id_order is None:
        order1 = Order(session['userID'], '0', 'создается', 'Неизвестно', 'Неизвестный')
        db.session.add(order1)
        db.session.commit()
        id_order = Order.query.filter_by(Status='создается', idUser=session['userID']).first()
    if request.method == "POST":
        valuesize = request.form["valuesize"]
        value1 = request.form["value1"]
    else:
        value1 = 1
        valuesize = 1
    o1 = OrderItem(id_order.idOrder, id, valuesize, value1)
    cloth1 = Cloth.query.filter_by(idCloth=id).first()
    id_order.TotalPrice += cloth1.Price * int(value1)
    db.session.add(o1)
    db.session.add(id_order)
    db.session.commit()
    return redirect('/')


@app.route("/delete_user/<int:id>", methods=['POST', 'GET'])
def delete_user(id):  # put application's code here
    user = User.query.get(id)
    db.session.delete(user)
    db.session.commit()
    return redirect('/all_users')


@app.route("/upgrade_people/<int:id>", methods=['POST', 'GET'])
def upgrade_people(id):  # put application's code here
    user = User.query.get(id)
    user.Role = 'Admin'
    db.session.add(user)
    db.session.commit()
    return redirect('/all_users')


if __name__ == '__main__':
    app.run(debug=True)
