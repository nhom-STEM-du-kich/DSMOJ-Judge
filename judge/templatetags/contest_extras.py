from django import template
register = template.Library()

@register.filter
def get_score(scores_dict, problem_id):
    return scores_dict.get(problem_id, 0.0)