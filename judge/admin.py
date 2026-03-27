from django.contrib import admin

# Register your models here.
from .models import Problem, Category, Submission, Profile, Contest, Group, Blog, JudgeNode
from markdownx.admin import MarkdownxModelAdmin
admin.site.register(Category)
@admin.action(description='Đặt lại các bài tập đã chọn thành Pending')
def reset_to_pending(modeladmin, request, queryset):
    # Cập nhật hàng loạt trường status thành 'P' (hoặc giá trị Pending trong ChoiceField của ông)
    updated = queryset.update(status='PD') # Giả sử field là status
    
    # Thông báo cho Admin biết đã "hồi sinh" bao nhiêu bài
    modeladmin.message_user(request, f"Đã reset {updated} bài nộp về trạng thái chờ chấm.")

class SubmissionAdmin(admin.ModelAdmin):
    # Những cột nào sẽ hiện ra ở danh sách
    list_display = ('id', 'user', 'problem_code', 'status', 'created_at')
    
    # Bộ lọc bên phải (Cực kỳ hữu ích để lọc xem ai vừa bị WA bài Quỳnh)
    list_filter = ('status', 'problem_code','contest', 'created_at')
    
    # Ô tìm kiếm (Tìm theo Username hoặc Mã bài tập)
    search_fields = ('user__username', 'problem_code')
    
    # Cho phép sửa nhanh trạng thái ngay tại danh sách
    list_editable = ('status',)
    
    # Phân trang (Tránh load 1 triệu submission làm lag server)
    list_per_page = 20
    actions = [reset_to_pending]
admin.site.register(Submission, SubmissionAdmin)
from django.utils.safestring import mark_safe
class MarkdownxKaTeXMixin:
    # Media giữ nguyên như cũ...
    class Media:
        css = {
            'all': ('https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css',)
        }
        js = (
            'https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js',
            'https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js',
        )

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        response = super().render_change_form(request, context, add, change, form_url, obj)
        response.render() 
        
        script = """
                <script>
                    (function() {
                        let renderTimeout;

                        function bootKaTeX() {
                            // Dùng Debounce để tránh lag khi gõ nhanh
                            clearTimeout(renderTimeout);
                            renderTimeout = setTimeout(function() {
                                var previews = document.querySelectorAll('.markdownx-preview');
                                if (previews.length > 0 && typeof renderMathInElement === 'function') {
                                    previews.forEach(function(el) {
                                        try {
                                            renderMathInElement(el, {
                                                delimiters: [
                                                    {left: "$$", right: "$$", display: true},
                                                    {left: "$", right: "$", display: false}
                                                ],
                                                // Chiêu thức báo lỗi: Không crash, chỉ đổi màu đỏ chỗ lỗi
                                                throwOnError: false,
                                                errorColor: '#ff0000',
                                                strict: 'warn'
                                            });
                                        } catch (err) {
                                            console.error("KaTeX Error:", err);
                                            el.innerHTML += '<div style="color:red; border:1px dashed red; padding:5px; margin-top:10px;">' +
                                                            '⚠️ LaTeX Syntax Error! Check your formulas.</div>';
                                        }
                                    });
                                }
                            }, 300); // Đợi 300ms sau khi ngừng gõ mới render
                        }

                        // Lắng nghe sự kiện update của Markdownx (Chuẩn nhất)
                        document.addEventListener('markdownx.update', bootKaTeX);

                        // Khởi tạo lần đầu
                        window.addEventListener('load', bootKaTeX);
                        
                        // Observer thông minh: Chỉ theo dõi nội dung của Preview
                        var observer = new MutationObserver(function(mutations) {
                            for (let mutation of mutations) {
                                if (mutation.type === 'childList') {
                                    bootKaTeX();
                                    break; 
                                }
                            }
                        });
                        
                        // Đợi element preview xuất hiện rồi mới observe
                        var checkExist = setInterval(function() {
                        var target = document.querySelector('.markdownx-preview');
                        if (target) {
                            observer.observe(target, { childList: true, characterData: true });
                            clearInterval(checkExist);
                        }
                        }, 500);
                    })();
                </script>
                """
        response.content = response.content.replace(b'</body>', script.encode('utf-8') + b'</body>')
        return response
# Giờ thì dùng nó cho cả Problem và Profile
class ProblemAdmin(MarkdownxKaTeXMixin, MarkdownxModelAdmin):
    pass

class ProfileAdmin(MarkdownxKaTeXMixin, MarkdownxModelAdmin):
    pass

admin.site.register(Problem, ProblemAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(Contest)
admin.site.register(Group)
admin.site.register(Blog)
class JudgeNodeAdmin(admin.ModelAdmin):
    # Những trường hiện ở danh sách ngoài
    list_display = ('name', 'ip_address', 'api_key', 'is_online', 'last_seen')
    
    # Ép Django hiện UUID trong trang chi tiết (vì editable=False)
    readonly_fields = ('api_key', 'last_seen')
    
    # Cho phép lọc theo trạng thái online cho dễ quản lý
    list_filter = ('is_online',)
admin.site.register(JudgeNode, JudgeNodeAdmin)