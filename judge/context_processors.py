from django.utils import timezone
from .models import Contest
def contest_status(request):
    """
    Bơm dữ liệu Contest vào mọi Template để Banner luôn hoạt động.
    """
    now = timezone.now()
    user = request.user
    active_contest = None
    
    # 1. Tìm Contest mà user đang tham gia và đang diễn ra
    if user.is_authenticated:
        active_contest = user.contests_joined.filter(
            start_time__lte=now, 
            end_time__gte=now
        ).first()

    # 2. Lấy trạng thái Focus từ Session (Mặc định là True)
    show_contest_mode = request.session.get('is_focused', True)

    return {
        'active_contest': active_contest,
        'show_contest_mode': show_contest_mode,
    }