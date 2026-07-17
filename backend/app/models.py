from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.sql import func

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    last_login = db.Column(db.DateTime(timezone=True))

    # Relationships
    clients = db.relationship("Client", back_populates="user", cascade="all, delete-orphan")
    projects = db.relationship("Project", back_populates="user", cascade="all, delete-orphan")
    payments = db.relationship("Payment", back_populates="user", cascade="all, delete-orphan")
    team_members = db.relationship("Team", back_populates="user", cascade="all, delete-orphan")
    time_logs = db.relationship("TimeLog", back_populates="user", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }


class Client(db.Model):
    __tablename__ = "clients"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    name = db.Column(db.String(100), nullable=False)
    industry = db.Column(db.String(100))
    contract_value = db.Column(db.Numeric(12, 2))
    payment_terms = db.Column(db.Integer)
    historical_payment_delay = db.Column(db.Integer)
    engagement_score = db.Column(db.Numeric(3, 2))

    # Relationships
    user = db.relationship("User", back_populates="clients")
    projects = db.relationship("Project", back_populates="client", cascade="all, delete-orphan")
    payments = db.relationship("Payment", back_populates="client", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "industry": self.industry,
            "contract_value": float(self.contract_value) if self.contract_value else None,
            "payment_terms": self.payment_terms,
            "historical_payment_delay": self.historical_payment_delay,
            "engagement_score": float(self.engagement_score) if self.engagement_score else None,
        }


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False)

    name = db.Column(db.String(100), nullable=False)
    budget = db.Column(db.Numeric(12, 2))
    hours_estimated = db.Column(db.Numeric(8, 2))
    hours_logged = db.Column(db.Numeric(8, 2))
    deadline = db.Column(db.Date)
    status = db.Column(db.String(50))
    margin = db.Column(db.Numeric(5, 2))

    # Relationships
    user = db.relationship("User", back_populates="projects")
    client = db.relationship("Client", back_populates="projects")
    time_logs = db.relationship("TimeLog", back_populates="project", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "client_id": self.client_id,
            "name": self.name,
            "budget": float(self.budget) if self.budget else None,
            "hours_estimated": float(self.hours_estimated) if self.hours_estimated else None,
            "hours_logged": float(self.hours_logged) if self.hours_logged else None,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "status": self.status,
            "margin": float(self.margin) if self.margin else None,
        }


class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False)

    invoice_date = db.Column(db.Date)
    due_date = db.Column(db.Date)
    paid_date = db.Column(db.Date)
    amount = db.Column(db.Numeric(12, 2))

    # Relationships
    user = db.relationship("User", back_populates="payments")
    client = db.relationship("Client", back_populates="payments")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "client_id": self.client_id,
            "invoice_date": self.invoice_date.isoformat() if self.invoice_date else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "paid_date": self.paid_date.isoformat() if self.paid_date else None,
            "amount": float(self.amount) if self.amount else None,
        }


class Team(db.Model):
    __tablename__ = "team"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100))
    hourly_rate = db.Column(db.Numeric(8, 2))
    capacity = db.Column(db.Integer)
    skills = db.Column(ARRAY(db.Text))

    # Relationships
    user = db.relationship("User", back_populates="team_members")
    time_logs = db.relationship("TimeLog", back_populates="team_member", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "role": self.role,
            "hourly_rate": float(self.hourly_rate) if self.hourly_rate else None,
            "capacity": self.capacity,
            "skills": self.skills,
        }


class TimeLog(db.Model):
    __tablename__ = "time_logs"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    team_member_id = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)

    log_date = db.Column(db.Date)
    hours_logged = db.Column(db.Numeric(4, 2))
    task_status = db.Column(db.String(50))

    # Relationships
    user = db.relationship("User", back_populates="time_logs")
    team_member = db.relationship("Team", back_populates="time_logs")
    project = db.relationship("Project", back_populates="time_logs")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "team_member_id": self.team_member_id,
            "project_id": self.project_id,
            "log_date": self.log_date.isoformat() if self.log_date else None,
            "hours_logged": float(self.hours_logged) if self.hours_logged else None,
            "task_status": self.task_status,
        }