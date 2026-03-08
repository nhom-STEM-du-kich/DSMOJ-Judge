from django.contrib import admin

# Register your models here.
from .models import Problem, Category, Submission, Profile, Contest, Group, Blog
from markdownx.admin import MarkdownxModelAdmin
admin.site.register(Category)
admin.site.register(Submission)
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
                function bootKaTeX() {
                    console.log("KaTeX Booting..."); // Đại ca nhấn F12 để xem dòng này
                    var previews = document.querySelectorAll('.markdownx-preview');
                    if (previews.length > 0 && typeof renderMathInElement === 'function') {
                        previews.forEach(function(el) {
                            renderMathInElement(el, {
                                delimiters: [
                                    {left: "$$", right: "$$", display: true},
                                    {left: "$", right: "$", display: false}
                                ],
                                throwOnError: false
                            });
                        });
                        console.log("KaTeX Rendered!");
                    }
                }

                // Lắng nghe sự kiện update của Markdownx
                document.addEventListener('markdownx.update', function() {
                    setTimeout(bootKaTeX, 200); 
                });

                // Đợi toàn bộ trang và script nạp xong
                window.addEventListener('load', function() {
                    setTimeout(bootKaTeX, 500);
                });
                
                // Chiêu cuối: Quan sát sự thay đổi của DOM (nếu AJAX render lại)
                var observer = new MutationObserver(function(mutations) {
                    bootKaTeX();
                });
                
                var target = document.querySelector('.markdownx');
                if (target) {
                    observer.observe(target, { childList: true, subtree: true });
                }
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