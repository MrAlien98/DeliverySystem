from flask import Flask, redirect, url_for, render_template, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
import sqlite3
import cx_Oracle
import os


app=Flask(__name__)

app.secret_key = "thisissupposedtobesecret"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.sqlite3'
''' app.config['SQLALCHEMY_DATABASE_URI']= 'oracle://P09551_1_16:P09551_1_16_20201@200.3.193.24:1522/ESTUD' '''
'''conn = cx_Oracle.connect('P09551_1_16/P09551_1_16_20201@//200.3.193.24:1522/ESTUD')'''
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db=SQLAlchemy(app)

#Tabla users en la base de datos
class Users(db.Model):
	__tablename__='users'
	_id=db.Column('id', db.Integer, primary_key=True)
	name=db.Column('name', db.String(100))
	address=db.Column('address', db.String(100))
	neighborhood=db.Column('neighborhood', db.String(100))
	city=db.Column('city', db.String(100))
	phone=db.Column('phone', db.String(100))
	document=db.Column('document', db.String(100))
	passwoord=db.Column('passwoord', db.String(100))
	rol=db.Column('rol', db.String(100))

	def __init__(self, name, address, neighborhood, city, phone, document, passwoord, rol):
		self.name=name
		self.address=address
		self.neighborhood=neighborhood
		self.city=city
		self.phone=phone
		self.document=document
		self.passwoord=passwoord
		self.rol=rol


#Tabla orders en la base de datos
class Orders(db.Model):
	__tablename__='orders'
	_id=db.Column('id', db.Integer, primary_key=True)
	senderLoc=db.Column('senderLoc', db.String(10))
	destLoc=db.Column('destLoc', db.String(10))
	state=db.Column('state', db.String(70))
	description=db.Column('description', db.String(300))
	senderId=db.Column('senderId', db.Integer, db.ForeignKey('users.id'))
	user=db.relationship('Users', backref='remitente')

	def __init__(self, senderLoc, destLoc, state, description, senderId):
		self.senderLoc=senderLoc
		self.destLoc=destLoc
		self.state=state
		self.description=description
		self.senderId=senderId
		

@app.route("/")
def home():
	return render_template("banner.html")


@app.route("/login/", methods=["POST", "GET"])
def login():
	if request.method == "POST":
		req_us = request.form["IDF"]
		req_pw = request.form["pwd"]
		if req_us == "admin" and req_pw == "admin":
			user=request.form["IDF"]
			session["user"]=user
			return redirect(url_for("dashboard", user=user))
		else:
			found_user=Users.query.filter_by(document=req_us).first()
			if found_user:
				if found_user.passwoord == req_pw:
					session["user"]=found_user.name
					session["doc"]=found_user.document
					return redirect(url_for("dashboard", user=found_user.name))
				else:
					flash("Usuario y/o contraseña invalida", "warning")
					return render_template("login.html")
			else:
				flash("No hay usuarios registrados con la identificacion suministrada", "warning")
				return render_template("login.html")

	else:
		if "user" in session:
			userName=session.get("user", None)
			return redirect(url_for("dashboard", user=userName))

		return render_template("login.html")


@app.route("/signup/", methods=["POST", "GET"])
def signup():
	if request.method == "POST":
		#campos del usuario a registrar
		usrs_name=request.form["name"]
		usrs_addr=request.form["address"]
		usrs_neig=request.form["neighborhood"]
		usrs_city=request.form["city"]
		usrs_phon=request.form["phone"]
		usrs_doc=request.form["id"]
		usrs_pwd=request.form["pass"]
		usrs_pwd2=request.form["pass2"]
		usrs_rol=request.form["rol"]
		#busqueda de usuarios por el numero de documento en la base de datos
		found_user=Users.query.filter_by(document=usrs_doc).first()
		#busqueda de usuarios por el numero de telefono en la base de datos
		found_user2=Users.query.filter_by(document=usrs_phon).first()
		#Si encuentra un usuario existente con el mismo numero de documento
		if found_user:
			flash("Ya hay una cuenta registrada con el documento suministrado", "warning")
			return render_template("signUp.html")
		#Si encuentra un usuario existente con el mismo numero de telefono
		elif found_user2:
			flash("Ya hay una cuenta registrada con el telefono suministrado", "warning")
			return render_template("signUp.html")
		#Si las contraseñas ingresadas por el usuario no coinciden
		elif usrs_pwd != usrs_pwd2:
			flash("Las contraseñas deben coincidir", "warning")
			return render_template("signUp.html")
		else:
			#Creacion del nuevo usuario
			usrs_new=Users(usrs_name, usrs_addr, usrs_neig, usrs_city, usrs_phon, usrs_doc, usrs_pwd, usrs_rol)
			#Adicion del nuevo usuario a la tabla de usuarios
			db.session.add(usrs_new)
			#Actualizacion en la base de datos
			db.session.commit()
			#Agregar usuario en la sesion actual para logearlo
			session["user"]=usrs_name
			session["doc"]=usrs_doc
			return redirect(url_for("dashboard", user=usrs_name))
	else:
		return render_template("signUp.html")


@app.route("/logout/")
def logout():
	session.pop("user", None)
	flash("Salida exitosa")
	return redirect("/")


@app.route("/dashboard/", methods=["POST", "GET"])
def dashboard():
	if "user" in session:
		userName=session.get("user", None)
		return render_template("userInterface.html", user=userName)
	else:
		flash("Debe iniciar sesion para acceder a la pagina", "warning")
		return redirect(url_for("login"))


@app.route("/order_request/", methods=["POST", "GET"])
def order_request():
	if "user" in session:
		if request.method=="POST":
			#campos del remitente
			r_name=request.form["Rname"]
			r_address=request.form["Radress"]
			r_city=request.form["Rcity"]
			r_loc="{}, {}".format(r_city, r_address)
			r_phone=request.form["Rphone"]
			#Descripcion del pedido
			o_description="lol"
			#campos del destinatario
			d_name=request.form["Dname"]
			d_address=request.form["Dadress"]
			d_city=request.form["Dcity"]
			d_loc="{}, {}".format(d_city, d_address)
			d_phone=request.form["Dphone"]
			#query para tener el id del usuario actual
			actual_doc=session.get("doc", None)
			actual_user=Users.query.filter_by(document=actual_doc).first()
			#creacion de la nueva orden/pedido
			order_new=Orders(r_loc, d_loc, "waiting", o_description, actual_user._id)
			#Adicion de la nueva orden a la tabla de orders
			db.session.add(order_new)
			#Actualizacion en la base de datos
			db.session.commit()
			flash("Orden efectuada correctamente", "success")
			return redirect(url_for("dashboard"))
		else:
			return render_template("orderRequest.html")
	else:
		flash("Debe iniciar sesion para acceder a la pagina", "warning")
		return redirect(url_for("login"))


@app.route("/watch_orders/", methods=["GET"])
def watch_orders():
	actual_doc=session.get("doc", None)
	actual_user=Users.query.filter_by(document=actual_doc).first()
	s_id=actual_user._id
	orders_list=Orders.query.filter_by(senderId=s_id)
	#print(orders_list)
	if orders_list:
		return render_template("orders.html", content=orders_list)
	else:
		flash("Usted no ha creado ningun pedido aún")
		return redirect(url_for("dashboard"))


@app.route("/history/")
def history():
	flash("Historia de la empresa")
	return render_template("historia.html")


if __name__ == "__main__":
	db.create_all()
	app.run(debug=True)

		
 