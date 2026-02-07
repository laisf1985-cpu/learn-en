import json
import random
from datetime import datetime, date, timedelta
from models import db, Word, UserWord, DailyTask


def select_daily_words(user_id):
    """
    为用户选择每日单词：5个新词 + 20个老词
    新用户会直接从词库随机选择25个单词
    """
    # 1. 统计用户已学单词数
    learned_count = db.session.query(UserWord).filter(UserWord.user_id == user_id).count()

    if learned_count == 0:
        # 新用户：直接从词库随机选择25个单词
        total_words = db.session.query(Word.id).order_by(db.func.random()).limit(25).all()
        word_ids = [w[0] for w in total_words]

        # 创建用户单词记录（标记为已学习但不熟练）
        for word_id in word_ids:
            user_word = UserWord(
                user_id=user_id,
                word_id=word_id,
                mastery_level=1,
                error_count=0,
                is_new=False,
                last_reviewed_at=datetime.utcnow()
            )
            db.session.add(user_word)
        db.session.commit()

        return word_ids

    else:
        # 老用户：按原逻辑选择
        # 1. 选择5个新词（从未学过的单词）
        new_words = db.session.query(Word.id).filter(
            ~Word.id.in_(
                db.session.query(UserWord.word_id).filter(UserWord.user_id == user_id)
            )
        ).order_by(Word.id).limit(5).all()

        new_word_ids = [w[0] for w in new_words]

        # 2. 选择20个老词（从已学单词中选择）
        # 优先级：错误次数多 > 最后复习时间早
        old_words_query = db.session.query(
            UserWord.word_id,
            UserWord.error_count,
            UserWord.last_reviewed_at
        ).filter(
            UserWord.user_id == user_id,
            UserWord.is_new == False
        ).order_by(
            UserWord.error_count.desc(),  # 错误多的优先
            UserWord.last_reviewed_at.asc()  # 久没复习的优先
        ).limit(20).all()

        old_word_ids = [w[0] for w in old_words_query]

        # 3. 如果老词不足20个，补充一些之前学过的单词
        if len(old_word_ids) < 20:
            additional = db.session.query(UserWord.word_id).filter(
                UserWord.user_id == user_id,
                UserWord.is_new == False,
                ~UserWord.word_id.in_(old_word_ids)
            ).limit(20 - len(old_word_ids)).all()
            old_word_ids.extend([w[0] for w in additional])

        # 4. 组合并打乱老词顺序
        word_ids = new_word_ids + old_word_ids
        random.shuffle(old_word_ids)

        # 5. 返回：5新词 + 20打乱的老词
        final_order = new_word_ids + old_word_ids

        return final_order


def create_daily_task(user_id, task_date=None):
    """
    创建每日任务
    """
    if task_date is None:
        task_date = date.today()

    # 检查是否已有今日任务
    existing = DailyTask.query.filter_by(
        user_id=user_id,
        task_date=task_date
    ).first()

    if existing:
        return existing

    # 选择单词
    word_ids = select_daily_words(user_id)

    # 创建任务
    task = DailyTask(
        user_id=user_id,
        task_date=task_date,
        word_ids=json.dumps(word_ids),
        current_index=0,
        completed=False,
        error_queue=json.dumps([])
    )

    db.session.add(task)
    db.session.commit()

    return task


def get_next_word(task):
    """
    获取下一个要答的单词
    """
    # 先检查错误队列
    error_queue = json.loads(task.error_queue) if task.error_queue else []

    if error_queue:
        # 返回错误队列的第一个单词
        word_id = error_queue[0]
        word = Word.query.get(word_id)
        return word, True  # True表示是复习词
    else:
        # 检查主任务队列
        word_ids = json.loads(task.word_ids)

        if task.current_index >= len(word_ids):
            return None, False  # 任务完成

        word_id = word_ids[task.current_index]
        word = Word.query.get(word_id)
        return word, False


def check_answer(user_id, word_id, user_input):
    """
    检查答案是否正确
    返回：(是否正确, 正确答案)
    """
    word = Word.query.get(word_id)
    correct = word.english.lower().strip() == user_input.lower().strip()

    # 获取或创建用户单词记录
    user_word = UserWord.query.filter_by(
        user_id=user_id,
        word_id=word_id
    ).first()

    if user_word:
        if correct:
            user_word.mastery_level = min(5, user_word.mastery_level + 1)
        else:
            user_word.error_count += 1
        user_word.last_reviewed_at = datetime.utcnow()
        db.session.commit()

    return correct, word.english
