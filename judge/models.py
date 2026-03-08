from django.db import models
from markdownx.models import MarkdownxField
# Create your models here.
from django.utils.text import slugify
from django.contrib.auth.models import User
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='profile_pics')
    bio = MarkdownxField(blank = True)
    rating = models.IntegerField(default=1500)  # Điểm Elo như Codeforces
    solved_problems = models.ManyToManyField('Problem', blank=True)
    github_url = models.URLField(max_length=200, blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True) # Ví dụ: "Drama", "Logic", "NĐ-147"
    slug = models.SlugField(unique=True) # Để lọc URL: /problems/category/drama/
    description = models.TextField(blank=True) # Mô tả ngắn về loại bài này

    def __str__(self):
        return self.name
    class Meta:
        verbose_name = "Category" # Tên hiện khi ở trang chỉnh sửa (số ít)
        verbose_name_plural = "Categories" # Tên hiện ở menu chính (số nhiều) - FIX CÁI "CATEGORYS"
        ordering = ['name'] # Tự động sắp xếp theo bảng chữ cái cho nó ngăn nắp
class Problem(models.Model):
    title = models.CharField(max_length=200)
    description = MarkdownxField()
    time_limit = models.FloatField(default=1.0) # Giây
    memory_limit = models.IntegerField(default=256000) # KB
    test_cases = models.JSONField(null=True,blank=True)
    difficulty = models.IntegerField(default=800)
    problem_code = models.CharField(max_length=200, default="")
    categories = models.ManyToManyField(Category, related_name="problems")
    show_test = models.BooleanField(default=True)
    is_for_contest = models.BooleanField(default=False)
    def __str__(self):
        return self.title
class Group(models.Model):
    name = models.CharField(max_length=200)
    description = MarkdownxField()
    user = models.ManyToManyField(Profile)
class Contest(models.Model):
    title = models.TextField()
    description = MarkdownxField()
    problem = models.ManyToManyField(Problem)
    start_time=models.DateTimeField()
    end_time = models.DateTimeField()
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='contests', null=True, blank=True)
    participants = models.ManyToManyField(User, related_name='contests_joined', blank=True)

class Submission(models.Model):
    STATUS_CHOICES = [
        ('PD', 'Pending'),
        ('JG', 'Judging'),
        ('AC', 'Accepted'),
        ('WA', 'Wrong Answer'),
        ('TLE', 'Time Limit Exceeded'),
        ('CE', 'Compile Error'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    problem_code = models.TextField(null=True)
    code = models.TextField(null=True)
    language = models.CharField(max_length=10, choices=[('py', 'Python'), ('cpp', 'C++'), ('asm', "Assembly (NASM)")])
    status = models.CharField(max_length=3, choices=STATUS_CHOICES, default='PD')
    result_log = models.TextField(blank=True, null=True) # Lưu cái "Actual Output" nếu cần soi
    created_at = models.DateTimeField(auto_now_add=True)
    contest = models.ForeignKey(Contest, on_delete=models.SET_NULL, null=True, blank=True)
    score = models.IntegerField(blank=True, null = True)
class Blog(models.Model):
    title = models.CharField(max_length=200, verbose_name="Tiêu đề")
    slug = models.SlugField(unique=True, blank=True, verbose_name="Slug (URL)")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Tác giả")
    
    # Dùng để hiện ở trang chủ
    summary = models.TextField(max_length=500, help_text="Tóm tắt ngắn gọn bài viết")
    
    # Nội dung chính (hỗ trợ Markdown)
    content = models.TextField(verbose_name="Nội dung bài viết")
    
    # Thumbnail cho blog (nếu đại ca muốn dùng Sony a6700 chụp rồi up lên)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Trạng thái bài viết
    is_published = models.BooleanField(default=False, verbose_name="Công khai")

    class Meta:
        ordering = ['-created_at'] # Bài mới nhất lên đầu
        verbose_name = "Bài viết Blog"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title