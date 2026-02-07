from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Word(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    english = db.Column(db.String(100), nullable=False, unique=True)
    chinese = db.Column(db.String(200), nullable=False)
    grade = db.Column(db.String(20))  # 七年级、八年级、九年级
    unit = db.Column(db.String(20))   # 单元
    difficulty = db.Column(db.Integer, default=1)  # 1-5


class UserWord(db.Model):
    """用户单词掌握情况"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    word_id = db.Column(db.Integer, db.ForeignKey('word.id'), nullable=False)
    mastery_level = db.Column(db.Integer, default=1)  # 掌握等级1-5
    error_count = db.Column(db.Integer, default=0)  # 错误次数
    last_reviewed_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_new = db.Column(db.Boolean, default=True)  # 是否新词

    word = db.relationship('Word', backref='user_words')


class DailyTask(db.Model):
    """每日任务"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    task_date = db.Column(db.Date, nullable=False)
    word_ids = db.Column(db.Text)  # JSON格式存储单词ID顺序
    current_index = db.Column(db.Integer, default=0)  # 当前做到第几个
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)

    # 错误单词队列（追尾）
    error_queue = db.Column(db.Text)  # JSON格式：[word_id1, word_id2, ...]


class ChallengeProgress(db.Model):
    """30天挑战进度"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    completed_days = db.Column(db.Integer, default=0)
    reward_claimed = db.Column(db.Boolean, default=False)
    total_reward = db.Column(db.Integer, default=0)  # 累计奖励金额（分）
