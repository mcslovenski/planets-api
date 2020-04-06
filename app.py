from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from flask_mail import Mail, Message
import os

# configs
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'planets.db')
app.config['JWT_SECRET_KEY'] = # JWT_SECRET_KEY secret here
app.config['MAIL_SERVER']='smtp.mailtrap.io'
app.config['MAIL_PORT'] = 2525
app.config['MAIL_USERNAME'] = # MAIL_USERNAME secret here
app.config['MAIL_PASSWORD'] = # MAIL_PASSWORD secret here
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

db = SQLAlchemy(app)
marsh = Marshmallow(app)
jwt = JWTManager(app)
mail = Mail(app)


# scripts
@app.cli.command('db_create')
def db_create():
    db.create_all()
    print("db created!")


@app.cli.command('db_drop')
def db_drop():
    db.drop_all()
    print("database dropped")


@app.cli.command('db_seed')
def db_seed():
    mercury = Planet(
        name="Mercury",
        type="Class D",
        home_star="Sol",
        mass=3.258e23,
        radius=1516,
        distance=35.98e6
    )
    venus = Planet(
        name="Venus",
        type="Class K",
        home_star="Sol",
        mass=4.867e24,
        radius=3760,
        distance=67.24e6
    )
    earth = Planet(
        name="Earth",
        type="Class M",
        home_star="Sol",
        mass=5.972e24,
        radius=3959,
        distance=92.96e6
    )

    db.session.add(mercury)
    db.session.add(venus)
    db.session.add(earth)

    test_user = User(
        first_name="William",
        last_name="Herschel",
        email="test@test.com",
        password="P@ssw0rd"
    )

    db.session.add(test_user)

    db.session.commit()
    print("Database seeded!")


# endpoints
# registration, login, and forgotten password

@app.route('/register', methods=['POST'])
def register():
    email = request.form['email']
    test = User.query.filter_by(email=email).first()
    if test:
        return jsonify(message="an account with that email address already exists"), 409
    else:
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        password = request.form['password']
        new_user = User(first_name=first_name, last_name=last_name, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        return jsonify(message="User created successfully"), 201


@app.route('/login', methods=['POST'])
def login():
    if request.is_json:
        email = request.json['email']
        password = request.json['password']
    else:
        email = request.form['email']
        password = request.form['password']

    test = User.query.filter_by(email=email, password=password).first()
    if test:
        access_token = create_access_token(identity=email)
        return jsonify(message="Login succeeded", access_token=access_token), 200
    else:
        return jsonify(message="Login unsuccessful"), 401


@app.route('/retrieve-password/<string:email>', methods=['GET'])
def retrive_password(email: str):
    user = User.query.filter_by(email=email).first()
    if user:
        msg = Message(
            "your planets API password is " + user.password,
            sender="admin@planets-api.com",
            recipients=[email]
        )
        mail.send(msg)
        return jsonify(message="Password sent to " + email)
    else:
        return jsonify(message="There is no user associated with that email address"), 401


# data interface routes

@app.route('/planets', methods=['GET'])
def planets():
    planets_list = Planet.query.all()
    result = planets_schema.dump(planets_list)
    return jsonify(result)


@app.route('/planet-details/<int:id>', methods=['GET'])
def planet_details(id: int):
    planet = Planet.query.filter_by(id=id).first()
    if planet:
        result = planet_schema.dump(planet)
        return jsonify(result)
    else:
        return jsonify(message="There is no planet with that ID"), 404


@app.route('/add-planet', methods=['POST'])
@jwt_required
def add_planet():
    name = request.form['name']
    test = Planet.query.filter_by(name=name).first()
    if test:
        return jsonify(message="Sorry, that planet is already in the database"), 409
    else:
        type = request.form['type']
        home_star = request.form['home_star']
        mass = request.form['mass']
        radius = request.form['radius']
        distance = request.form['distance']
        new_planet = Planet(name=name, type=type, home_star=home_star, mass=mass, radius=radius, distance=distance)
        db.session.add(new_planet)
        db.session.commit()
        return jsonify(message="your planet has been added to the database!"), 200


@app.route('/update-planet', methods=['PUT'])
@jwt_required
def update_planet():
    id = int(request.form['id'])
    planet = Planet.query.filter_by(id=id).first()
    if planet:
        planet.name = request.form['name']
        planet.type = request.form['type']
        planet.home_star = request.form['home_star']
        planet.mass = float(request.form['mass'])
        planet.radius = float(request.form['radius'])
        planet.distance = float(request.form['distance'])
        db.session.commit()
        return jsonify(message=f"planet {id} updated"), 202
    else:
        return jsonify(message=f"Sorry, there is no planet with id {id}"), 404


@app.route('/remove-planet/<int:id>', methods=['DELETE'])
@jwt_required
def remove_planet(id: int):
    planet = Planet.query.filter_by(id=id).first()
    if planet:
        db.session.delete(planet)
        db.session.commit()
        return jsonify(message=f"Planet with id {id} successfully deleted"), 202
    else:
        return jsonify(message=f"Sorry, there is no planet with id {id}"), 404


# database schemas

class User(db.Model):
    __tablename__ = 'Users'
    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)


class Planet(db.Model):
    __tablename__ = 'Planets'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    type = Column(String)
    home_star = Column(String)
    mass = Column(Float)
    radius = Column(Float)
    distance = Column(Float)


# marshmallow schemas
class UserSchema(marsh.Schema):
    class Meta:
        fields = ('id', 'first_name', 'last_name', 'email', 'password')

user_schema = UserSchema()
users_schema = UserSchema(many=True)


class PlanetSchema(marsh.Schema):
    class Meta:
        fields = ('id', 'name', 'type', 'home_star', 'mass', 'radius', 'distance')

planet_schema = PlanetSchema()
planets_schema = PlanetSchema(many=True)


if __name__ == '__main__':
    app.debug = True
    app.run()
