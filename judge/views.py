from django.shortcuts import render, redirect, get_object_or_404
from django.template import loader
from .models import Problem, Submission,Profile, Contest, Blog
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models.functions import TruncDate
from django.db.models import Count
from django.utils import timezone
# Create your views here.

def problem(request, problem_code):
# 1. Lấy bài tập (nếu không có thì 404 luôn)
    problem = get_object_or_404(Problem, problem_code=problem_code)
    now = timezone.now()
    user = request.user
    
    # 1. Lấy Contest mà User đang tham gia
    active_contest = None
    if user.is_authenticated:
        active_contest = user.contests_joined.filter(
            start_time__lte=now, 
            end_time__gte=now
        ).first()

    # 2. Lấy trạng thái Focus từ Session
    show_contest_mode = request.session.get('is_focused', True)

    # 3. ĐỒNG BỘ: Nếu đang Focus vào Contest, check xem bài này có trong Contest đó không
    if active_contest and show_contest_mode:
        if not active_contest.problem.filter(id=problem.id).exists():
            # Nếu bài này không có trong contest, đẩy về trang danh sách contest
            messages.warning(request, "Bài này không nằm trong cuộc thi hiện tại!")
            return redirect('problems_list')

    context = {
        'problem': problem,
        'active_contest': active_contest,
        'show_contest_mode': show_contest_mode,
    }
    return render(request, 'problem.html', context)
    
    return render(request, 'problem.html', context)
def problems(request):
    now = timezone.now()
    user = request.user
    
    # Check xem có đang tham gia contest nào không
    active_contest = user.contests_joined.filter(start_time__lte=now, end_time__gte=now).first()
    
    # Lấy trạng thái từ Session (mặc định là True nếu đang trong contest)
    is_focused = request.session.get('is_focused', True)

    if active_contest and is_focused:
        # Chế độ "In Contest": Chỉ hiện đề thi
        problems = active_contest.problem.all()
        show_contest_mode = True
    else:
        # Chế độ "Out Contest" hoặc không có contest: Hiện kho đề chung
        problems = Problem.objects.filter(is_for_contest = False)
        show_contest_mode = False

    return render(request, 'problems.html', {
        'problems': problems,
        'active_contest': active_contest,
        'show_contest_mode': show_contest_mode,
        'is_focused': is_focused
    })
@login_required
def toggle_focus(request):
    # Đảo ngược trạng thái Focus trong Session
    current_status = request.session.get('is_focused', True)
    request.session['is_focused'] = not current_status
    return redirect('problems_list')
def submit_code(request, problem_code):
    if request.method == "POST":
        # Bốc dữ liệu từ HTML thuần
        code_str = request.POST.get("code")
        lang = request.POST.get("lang")
        
        # Lưu vào Database với trạng thái Pending
        new_sub = Submission.objects.create(
            problem_code=problem_code,
            user=request.user,
            code=code_str,
            language=lang,
            status="PD"
        )
        
        # Đẩy thí sinh sang trang danh sách để ngồi hóng
        return redirect(f"/submissions/{new_sub.id}")
    
    # Nếu là GET thì chỉ hiện cái form lên thôi
    problem = Problem.objects.get(problem_code=problem_code)
    return render(request, "submit.html", {"problem": problem})
def get_task(request):
    # 1. Tìm bài đang đợi (Pending) sớm nhất
    task = Submission.objects.filter(status="PD").order_by("created_at").first()
    
    # 2. Kiểm tra sinh mạng của task trước khi làm thịt
    if not task:
        return JsonResponse({"status": "empty"})

    try:
        # 3. Bốc dữ liệu bài toán tương ứng
        problem = Problem.objects.get(problem_code=task.problem_code)
        
        # 4. Đánh dấu đang chấm (JG - Judging) để tránh tranh chấp giữa các Worker
        task.status = "JG"
        task.save()
        
        # 5. Trả về payload High-Fidelity cho Worker
        return JsonResponse({
            "status": "success",
            "id": task.id,
            "code": task.code,
            "lang": task.language,
            "testcases": problem.test_cases, # JSON thần thánh
            "time_limit": problem.time_limit,
            "test_view": problem.show_test,  # Trả về cho thằng Judge quyết định hiển thị
        })
        
    except Problem.DoesNotExist:
        # Nếu bài nộp trỏ về một Problem không tồn tại (Lỗi rác DB)
        task.status = "ER" # Đánh dấu Error luôn cho rảnh nợ
        task.save()
        return JsonResponse({"status": "error", "msg": f"Problem {task.problem_code} not found"})
            
    return JsonResponse({"status": "empty"}) # Hết việc rồi, nghỉ tí đi
@csrf_exempt # Cho phép máy ngoài gửi POST vào mà không cần token web
def update_result(request, sub_id):
    if request.method == "POST":
        sub = Submission.objects.get(id=sub_id)
        
        # Đọc dữ liệu JSON từ thân Request
        data = json.loads(request.body)
        
        sub.status = data.get("status") # AC, WA, TLE, CE...
        sub.result_log = data.get("log") # Lưu nhật ký "mất dạy" của thí sinh
        sub.score = data.get("score")
        sub.save()
        if sub.status == "AC":
            user_submission = Profile.objects.get(user =sub.user)
            problem = Problem.objects.get(problem_code=sub.problem_code)
            if problem not in user_submission.solved_problems.all():
                user_submission.solved_problems.add(problem)
                user_submission.rating += problem.difficulty
                user_submission.save()
        return JsonResponse({"status": "success", "msg": "Success, bruv!"})
def submissions(request):
    submissions = Submission.objects.all().order_by('created_at').reverse()
    template = loader.get_template("submissions.html")
    context ={
        "submissions": submissions,
    }
    return render(request, "submissions.html", context)
def submission(request,id):
    submission = Submission.objects.get(id=id)
    template = loader.get_template("submissions.html")
    context ={
        "submission": submission,
    }
    return render(request, "submission.html", context)
def profile(request, username):
    user_profile = Profile.objects.get(user__username=username)
    user_solved = user_profile.solved_problems.count()
    user_activity = Submission.objects.filter(user=user_profile.user, status='AC') \
        .annotate(date=TruncDate('created_at')) \
        .values('date') \
        .annotate(count=Count('id')) \
        .values_list('date', 'count')
    heatmap_json = json.dumps([[str(d), c] for d, c in user_activity])
    is_owner = (request.user == user_profile.user)
    context = {
        "user": user_profile.user,
        "is_owner": is_owner,
        "solved_problems": user_solved,
        "heatmap": heatmap_json
    }
    return render(request, "profile.html", context)
@login_required
def profile_update(request):
    if request.method == 'POST':
        # Lấy dữ liệu từ Form gửi lên
        bio = request.POST.get('bio')
        avatar = request.FILES.get('avatar')
        
        # Cập nhật vào Profile của user đang đăng nhập
        profile = request.user.profile
        profile.bio = bio
        if avatar:
            profile.avatar = avatar
        
        profile.save()
        messages.success(request, 'Profile đã "AC", mượt như Resampling 192kHz!')
        return redirect('profile', username=request.user.username)
    
    return redirect('profile', username=request.user.username)
@login_required
def user_delete(request):
    if request.method == 'POST':
        user = request.user
        # Đại ca có thể lưu log cuối cùng vào Sony a6700 trước khi tiễn bả
        user.delete() 
        messages.warning(request, 'Tài khoản đã bị "Aliasing" hoàn toàn. Hẹn gặp lại ở kiếp sau!')
        return redirect('home') # Quay về trang chủ
    
    return redirect('profile', username=request.user.username)
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import render, redirect
from django.contrib import messages

def change_password(request):
    if request.method == 'POST':
        # Nạp user hiện tại và dữ liệu POST vào form
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # QUAN TRỌNG: Cập nhật lại Session để bả không bị văng ra (Logout)
            update_session_auth_hash(request, user)  
            messages.success(request, 'Mật khẩu đã đổi! Sóng sạch như 32-bit Float!')
            return redirect('profile', username=request.user.username)
        else:
            messages.error(request, 'Lỗi rồi! Mật khẩu cũ sai hoặc mật khẩu mới quá lỏ!')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'change_password.html', {'form': form})
def ranks(request):
    users = Profile.objects.order_by('rating').reverse()
    context={
        "users": users
    }
    return render(request, 'ranks.html', context)
def contests(request):
    now = timezone.now()
    # Contest đang chạy
    active_contests = Contest.objects.filter(start_time__lte=now, end_time__gte=now)
    # Contest sắp tới
    upcoming_contests = Contest.objects.filter(start_time__gt=now).order_by('start_time')
    # Contest đã xong
    past_contests = Contest.objects.filter(end_time__lt=now).order_by('-end_time')
    
    return render(request, 'contest_list.html', {
        'active': active_contests,
        'upcoming': upcoming_contests,
        'past': past_contests
    })
def contest_detail(request, contest_id):
    contest = Contest.objects.get(id=contest_id)
    user = request.user
    problems = contest.problem.all()

    # Nếu user đã đăng nhập, ta đi tìm điểm cao nhất của họ cho từng bài
    if user.is_authenticated:
        for p in problems:
            subs = Submission.objects.filter(user=user, contest=contest, problem_code=p.problem_code)
            print(f"DEBUG: Problem {p.problem_code} has {subs.count()} submissions in this contest")
            
            best_sub = subs.order_by('-score').first()

            # Bơm dữ liệu vào object p để template dùng
            if best_sub:
                p.user_score = best_sub.score
                p.user_status = "AC" if best_sub.status == "AC" else "WA"
            else:
                p.user_score = 0
                p.user_status = None

    return render(request, 'contest_detail.html', {
        'contest': contest,
        'problems': problems, # Danh sách đã được "nhồi" điểm
    })
def register_contest(request, contest_id):
    if request.method == 'POST':
        contest = get_object_or_404(Contest, id=contest_id)
        
        if timezone.now() > contest.end_time:
            messages.error(request, "Hết giờ đăng ký rồi đại ca!")
            return redirect('contest_list')

        # Thêm User vào danh sách participants
        if request.user not in contest.participants.all():
            contest.participants.add(request.user)
            messages.success(request, "Đã ghi danh! Xách phím lên và thi thôi.")
        else:
            messages.info(request, "Đại ca có tên trong danh sách rồi, đừng lo!")

    return redirect('contest_detail', contest_id=contest_id)
@login_required
def register_contest(request, contest_id):
    if request.method == 'POST':
        # Dùng get() để chắc chắn lấy đúng Object instance
        contest = Contest.objects.get(id=contest_id) 
        
        # Thử dùng .add() và ép save (cho chắc kèo)
        contest.participants.add(request.user)
        contest.save() # Ép Database ghi đè lên đĩa
        
        # Kiểm tra lại ngay lập tức
        count = contest.participants.all().count()
        print(f"DEBUG: Sau khi add, Contest có {count} người.")
        
        return redirect('contest_detail', contest_id=contest_id)
@login_required # Chỉ cho phép anh em đã login nộp bài
def submit_code_contest(request, problem_code, contest_id):
    # Lấy Contest và Problem một cách an toàn (tránh lỗi 500 nếu ID bậy)
    contest = get_object_or_404(Contest, id=contest_id)
    problem = get_object_or_404(Problem, problem_code=problem_code)

    if request.method == "POST":
        # Bốc dữ liệu từ HTML
        code_str = request.POST.get("code")
        lang = request.POST.get("lang")
        
        # Lưu vào Database với đầy đủ "chứng minh thư"
        new_sub = Submission.objects.create(       # Nên dùng trực tiếp instance của Problem
            problem_code=problem_code, # Để tra cứu nhanh nếu cần
            user=request.user,
            code=code_str,
            language=lang,
            status="PD",              # Pending - Đang đợi thầy Toàn chấm
            contest=contest,          # GHIM VÀO ĐÂY!
            score=0.0                 # Khởi tạo điểm OI là 0
        )
        
        # Đẩy sang trang chi tiết submission để hóng kết quả
        return redirect(f"/submissions/{new_sub.id}/")
    
    # Nếu là GET: Hiện form nộp bài kèm thông tin bài tập
    context = {
        "problem": problem,
        "contest": contest,
    }
    return render(request, "submit.html", context)
# Logic rút gọn để lấy Leaderboard hệ OI
def contest_leaderboard(request, contest_id):
    # Dùng prefetch_related để tối ưu ManyToMany và Submissions
    contest = get_object_or_404(
        Contest.objects.prefetch_related('problem', 'submission_set__user'), 
        id=contest_id
    )
    
    # Lấy danh sách bài tập (ManyToMany)
    problems = contest.problem.all()
    
    # Lấy toàn bộ submission của contest này
    submissions = contest.submission_set.all().order_by('created_at')
    
    board_data = {}
    
    for sub in submissions:
        user_id = sub.user.id
        username = sub.user.username
        
        if user_id not in board_data:
            board_data[user_id] = {
                'username': username,
                'scores': {p.id: 0.0 for p in problems},
                'total_score': 0.0,
                'last_update': sub.created_at
            }
        
        # Logic OI: Cập nhật nếu điểm cao hơn điểm cũ của bài đó
        current_best = board_data[user_id]['scores'].get(sub.problem_code, 0.0)
        if sub.score > current_best:
            diff = sub.score - current_best
            board_data[user_id]['scores'][sub.problem_code] = float(sub.score)
            board_data[user_id]['total_score'] += float(diff)
            board_data[user_id]['last_update'] = sub.created_at

    # Sắp xếp theo hệ OI: Điểm cao trước -> Thời gian đạt điểm đó sớm hơn xếp trên
    sorted_board = sorted(
        board_data.values(),
        key=lambda x: (-x['total_score'], x['last_update'])
    )

    return render(request, 'leaderboard.html', {
        'contest': contest,
        'problems': problems,
        'leaderboard': sorted_board
    })
def home_view(request):
    # 1. Lấy danh sách bài viết đã xuất bản
    blog_posts = Blog.objects.filter(is_published=True)[:5] # Lấy 5 bài mới nhất
    
    # 2. Kiểm tra xem có Contest nào đang chạy không (cho Sidebar)
    # Logic: Tìm contest có start_time <= now <= end_time
    from django.utils import timezone
    now = timezone.now()
    active_contest = Contest.objects.filter(
        start_time__lte=now, 
        end_time__gte=now
    ).first()

    context = {
        'blog_posts': blog_posts,
        'active_contest': active_contest,
        'user': request.user,
    }
    
    return render(request, 'home.html', context)