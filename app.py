import os
import csv
from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Word, UserWord, DailyTask, ChallengeProgress
from utils.word_selector import create_daily_task, get_next_word, check_answer
from utils.progress import update_challenge_progress, get_user_statistics

# 获取绝对路径
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(BASE_DIR, "instance", "app.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)


@app.before_request
def create_tables():
    if not os.path.exists('instance'):
        os.makedirs('instance')
    db.create_all()


# ============ 认证相关 ============

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # 获取当前用户信息
    user = User.query.get(session['user_id'])
    stats = get_user_statistics(session['user_id'])

    # 检查今天是否有任务
    from datetime import date
    today = date.today()
    task = DailyTask.query.filter_by(
        user_id=session['user_id'],
        task_date=today
    ).first()

    if not task:
        task = create_daily_task(session['user_id'])

    return render_template('index.html', stats=stats, task=task, current_user=user)


# ============ 用户注册 ============
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        # 验证输入
        if not username or not password:
            flash('用户名和密码不能为空', 'error')
        elif len(username) < 3 or len(username) > 20:
            flash('用户名长度必须在3-20个字符之间', 'error')
        elif len(password) < 6:
            flash('密码至少6个字符', 'error')
        elif password != confirm_password:
            flash('两次输入的密码不一致', 'error')
        else:
            # 检查用户名是否已存在
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash('该用户名已被注册，请选择其他用户名', 'error')
            else:
                # 创建新用户
                new_user = User(
                    username=username,
                    password_hash=generate_password_hash(password)
                )
                db.session.add(new_user)
                db.session.commit()
                flash('注册成功！请登录', 'success')
                return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            return redirect(url_for('index'))
        else:
            flash('用户名或密码错误', 'error')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ============ 任务相关 ============

@app.route('/task')
def task():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    from datetime import date
    today = date.today()
    task = DailyTask.query.filter_by(
        user_id=session['user_id'],
        task_date=today
    ).first()

    if not task:
        task = create_daily_task(session['user_id'])

    if task.completed:
        return redirect(url_for('complete'))

    word, is_review = get_next_word(task)

    if not word:
        # 任务完成
        task.completed = True
        task.completed_at = datetime.now()
        db.session.commit()

        # 更新挑战进度
        update_challenge_progress(session['user_id'])

        return redirect(url_for('complete'))

    # 显示进度
    word_ids = __import__('json').loads(task.word_ids)
    total_words = len(word_ids)
    progress_text = f"{task.current_index}/{total_words}"

    return render_template('task.html', task=task, word=word, is_review=is_review, progress=progress_text)


@app.route('/answer', methods=['POST'])
def answer():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    import json
    from datetime import date, datetime

    today = date.today()
    task = DailyTask.query.filter_by(
        user_id=session['user_id'],
        task_date=today
    ).first()

    if not task:
        return redirect(url_for('task'))

    word_id = int(request.form['word_id'])
    user_input = request.form['answer']
    is_review = request.form.get('is_review') == 'True'

    # 检查答案
    correct, correct_answer = check_answer(session['user_id'], word_id, user_input)

    if correct:
        # 答对了
        if not is_review:
            # 主任务队列，移动到下一个
            task.current_index += 1
        else:
            # 错误队列，移出队列
            error_queue = json.loads(task.error_queue) if task.error_queue else []
            error_queue.pop(0)
            task.error_queue = json.dumps(error_queue)
    else:
        # 答错了
        if not is_review:
            # 主任务队列，先移动到下一个（错词留到后面）
            task.current_index += 1

        # 加到错误队列尾部
        error_queue = json.loads(task.error_queue) if task.error_queue else []
        error_queue.append(word_id)
        task.error_queue = json.dumps(error_queue)

    db.session.commit()

    return render_template('answer.html',
                          correct=correct,
                          user_input=user_input,
                          correct_answer=correct_answer,
                          word_id=word_id)


@app.route('/complete')
def complete():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    stats = get_user_statistics(session['user_id'])

    return render_template('complete.html', stats=stats)


# ============ 单词导入 ============

@app.route('/import')
def import_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    word_count = Word.query.count()
    return render_template('import.html', word_count=word_count)


@app.route('/import', methods=['POST'])
def import_words():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    csv_text = request.form['csv_text']
    lines = csv_text.strip().split('\n')

    imported = 0
    skipped = 0

    for line in lines:
        if not line.strip():
            continue

        # 格式：英文,中文,年级,单元
        parts = line.split(',')

        if len(parts) >= 2:
            english = parts[0].strip()
            chinese = parts[1].strip()
            grade = parts[2].strip() if len(parts) > 2 else None
            unit = parts[3].strip() if len(parts) > 3 else None

            # 检查是否已存在
            existing = Word.query.filter_by(english=english).first()

            if not existing:
                word = Word(
                    english=english,
                    chinese=chinese,
                    grade=grade,
                    unit=unit
                )
                db.session.add(word)
                imported += 1
            else:
                skipped += 1

    db.session.commit()

    flash(f'成功导入 {imported} 个单词，跳过 {skipped} 个重复单词', 'success')

    return redirect(url_for('import_page'))


# ============ 初始化 ============

def auto_import_words():
    """自动导入人教版七八九年级单词表"""
    if Word.query.count() == 0:
        import csv
        word_files = [
            'pep_words_grade7.csv',
            'pep_words_grade8.csv',
            'pep_words_grade9.csv'
        ]

        for filename in word_files:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    next(reader, None)  # 跳过标题行
                    count = 0
                    for row in reader:
                        if len(row) >= 2:
                            english = row[0].strip()
                            chinese = row[1].strip()
                            grade = row[2].strip() if len(row) > 2 else None
                            unit = row[3].strip() if len(row) > 3 else None

                            # 检查是否已存在
                            existing = Word.query.filter_by(english=english).first()
                            if not existing:
                                word = Word(
                                    english=english,
                                    chinese=chinese,
                                    grade=grade,
                                    unit=unit
                                )
                                db.session.add(word)
                                count += 1

                    db.session.commit()
                    print(f"✅ 已导入 {filename}: {count} 个单词")
            except FileNotFoundError:
                print(f"⚠️  文件不存在: {filename}")
            except Exception as e:
                print(f"❌ 导入 {filename} 失败: {e}")

        total = Word.query.count()
        return f"✅ 单词导入完成！词库共有 {total} 个单词"
    else:
        return "词库已有单词，跳过自动导入"


@app.route('/init')
def init_admin():
    """初始化管理员账户并自动导入单词"""
    result_messages = []

    # 创建管理员账户
    if User.query.count() == 0:
        user = User(
            username='admin',
            password_hash=generate_password_hash('admin123')
        )
        db.session.add(user)
        db.session.commit()
        result_messages.append('✅ 管理员账户创建成功<br>用户名: admin<br>密码: admin123<br>请登录后立即修改密码！')
    else:
        result_messages.append('⚠️ 管理员账户已存在')

    # 自动导入单词
    import_result = auto_import_words()
    result_messages.append(f'<br>{import_result}')

    return '<br>'.join(result_messages)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
