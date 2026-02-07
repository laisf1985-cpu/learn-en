from datetime import date, timedelta
from models import db, DailyTask, ChallengeProgress


def update_challenge_progress(user_id):
    """
    更新30天挑战进度
    """
    # 获取当前挑战
    challenge = ChallengeProgress.query.filter_by(user_id=user_id).order_by(
        ChallengeProgress.start_date.desc()
    ).first()

    if not challenge:
        # 创建新挑战
        challenge = ChallengeProgress(
            user_id=user_id,
            start_date=date.today(),
            completed_days=0,
            total_reward=0
        )
        db.session.add(challenge)
        db.session.commit()

    # 统计已完成的任务天数
    start_date = challenge.start_date
    days_completed = DailyTask.query.filter(
        DailyTask.user_id == user_id,
        DailyTask.task_date >= start_date,
        DailyTask.completed == True
    ).count()

    # 更新进度
    challenge.completed_days = days_completed

    # 检查是否完成30天
    if days_completed >= 30 and not challenge.reward_claimed:
        challenge.reward_claimed = True
        challenge.total_reward = 200 * 100  # 200元 = 20000分
        db.session.commit()

    db.session.commit()
    return challenge


def get_user_statistics(user_id):
    """
    获取用户统计信息
    """
    # 当前挑战
    current_challenge = ChallengeProgress.query.filter_by(
        user_id=user_id
    ).order_by(ChallengeProgress.start_date.desc()).first()

    # 累计奖励（所有已完成挑战）
    total_reward = db.session.query(
        db.func.sum(ChallengeProgress.total_reward)
    ).filter(
        ChallengeProgress.user_id == user_id,
        ChallengeProgress.reward_claimed == True
    ).scalar() or 0

    # 已完成挑战数
    completed_challenges = ChallengeProgress.query.filter(
        ChallengeProgress.user_id == user_id,
        ChallengeProgress.reward_claimed == True
    ).count()

    # 总学习天数
    total_days = DailyTask.query.filter(
        DailyTask.user_id == user_id,
        DailyTask.completed == True
    ).count()

    # 30天内连续打卡天数
    if current_challenge:
        current_days = current_challenge.completed_days
        remaining_days = max(0, 30 - current_days)
        challenge_start_date = current_challenge.start_date
    else:
        current_days = 0
        remaining_days = 30
        challenge_start_date = None

    return {
        'total_reward': total_reward / 100,  # 转换为元
        'completed_challenges': completed_challenges,
        'total_days': total_days,
        'current_days': current_days,
        'remaining_days': remaining_days,
        'challenge_start_date': challenge_start_date
    }
