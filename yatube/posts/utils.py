from django.core.paginator import Paginator


def paginate(request, queryset, posts_per_page):
    """Паджинатор.
    """
    paginator = Paginator(queryset, posts_per_page)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
