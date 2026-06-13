from flask_mail import Mail, Message
from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "giftmaliatso@gmail.com"
import os

app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = "giftmaliatso@gmail.com"

mail = Mail(app)

app.secret_key = "FaithAliveSecret2026"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///charity.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


UPLOAD_FOLDER = "static/uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

db = SQLAlchemy(app)

class Donation(db.Model):
    __tablename__ = "donations"

    id = db.Column(db.Integer, primary_key=True)
    donor_name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    amount = db.Column(db.Numeric(10,2))
    payment_method = db.Column(db.String(50))



    project_id = db.Column(
        db.Integer,
        db.ForeignKey("projects.id")
    )

    project = db.relationship(
        "Project",
        backref="donations"
    )

class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    goal_amount = db.Column(db.Numeric(12,2))

    raised_amount = db.Column(
        db.Numeric(12,2),
        default=0
    )

    image = db.Column(db.String(255))

class Admin(db.Model):
    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50))
    password = db.Column(db.String(255))


@app.route("/")
def home():

    projects = Project.query.limit(3).all()

    total_projects = Project.query.count()

    total_donations = db.session.query(
        db.func.sum(Donation.amount)
    ).scalar() or 0

    return render_template(
        "home.html",
        projects=projects,
        total_projects=total_projects,
        total_donations=total_donations
    )

@app.route("/donate", methods=["GET", "POST"])
def donate():

    if request.method == "POST":

        donation = Donation(
            donor_name=request.form["name"],
            email=request.form["email"],
            amount=request.form["amount"],
            payment_method="Manual",
            project_id=request.form["project_id"]
        )

        project = db.session.get(
            Project,
            int(request.form["project_id"])
        )

        if project:
            project.raised_amount = (
                float(project.raised_amount or 0)
                + float(request.form["amount"])
            )

        db.session.add(donation)
        db.session.commit()

        try:
            msg = Message(
                subject="Thank You For Your Donation ❤️",
                recipients=[request.form["email"]]
            )

            msg.html = f"""
            <h2>Thank You For Your Donation ❤️</h2>

            <p>Dear {request.form['name']},</p>

            <p>
            Thank you for donating
            <strong>KES {request.form['amount']}</strong>.
            </p>

            <p>
            Your generosity helps us support communities,
            provide education, healthcare and food assistance.
            </p>

            <p>
            <b>Helping Hearts Charity</b>
            </p>
            """

            mail.send(msg)

        except Exception as e:
            print("Email Error:", e)

        return render_template(
            "thank_you.html",
            amount=request.form["amount"]
        )

    projects = Project.query.all()

    return render_template(
        "donate.html",
        projects=projects
    )
    
@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/projects")
def projects():

    projects = Project.query.all()

    return render_template(
        "projects.html",
        projects=projects
    )
@app.route("/admin")
def admin():

    if "admin" not in session:
        return redirect("/login")

    donations = Donation.query.all()

    total_donations = sum(
        float(d.amount)
        for d in donations
    )

    return render_template(
        "admin.html",
        donations=donations,
        total=total_donations
    )


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        admin = Admin.query.filter_by(
            username=username,
            password=password
        ).first()

        if admin:
            session["admin"] = username
            return redirect("/admin")

        return "Invalid username or password"

    return render_template("login.html")

@app.route("/logout")
def logout():

    session.pop("admin", None)

    return redirect("/login")

@app.route("/add-project", methods=["GET", "POST"])
def add_project():

    if "admin" not in session:
        return redirect("/login")

    if request.method == "POST":

        image = request.files["image"]

        filename = ""

        if image and image.filename:
            filename = secure_filename(image.filename)

            image.save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    filename
                )
            )

        project = Project(
            title=request.form["title"],
            description=request.form["description"],
            goal_amount=request.form["goal_amount"],
            raised_amount=0,
            image=filename
        )

        db.session.add(project)
        db.session.commit()

        return redirect("/projects")

    return render_template("add_project.html")

@app.route("/edit-project/<int:id>", methods=["GET", "POST"])
def edit_project(id):

    if "admin" not in session:
        return redirect("/login")

    project = Project.query.get_or_404(id)

    if request.method == "POST":

        project.title = request.form["title"]
        project.description = request.form["description"]
        project.goal_amount = request.form["goal_amount"]

        db.session.commit()

        return redirect("/projects")

    return render_template(
        "edit_project.html",
        project=project
    )
@app.route("/delete-project/<int:id>")
def delete_project(id):

    if "admin" not in session:
        return redirect("/login")

    project = Project.query.get_or_404(id)

    db.session.delete(project)
    db.session.commit()

    return redirect("/projects")
@app.route("/test-email")
def test_email():

    msg = Message(
        subject="Test Email",
        recipients=["your_other_email@example.com"]
    )

    msg.body = "This is a test email from Helping Hearts Charity."

    mail.send(msg)

    return "Email Sent!"

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
