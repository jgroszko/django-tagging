"""
Tagging related views.
"""
from django.db.models import Count
from django.shortcuts import render_to_response
from django.http import Http404
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.views.generic.list_detail import object_list
from django.contrib.contenttypes.models import ContentType

from tagging.models import Tag, TaggedItem
from tagging.utils import get_tag, get_queryset_and_model

def tagged_object_list(request, queryset_or_model=None, tag=None,
        related_tags=False, related_tag_counts=True, **kwargs):
    """
    A thin wrapper around
    ``django.views.generic.list_detail.object_list`` which creates a
    ``QuerySet`` containing instances of the given queryset or model
    tagged with the given tag.

    In addition to the context variables set up by ``object_list``, a
    ``tag`` context variable will contain the ``Tag`` instance for the
    tag.

    If ``related_tags`` is ``True``, a ``related_tags`` context variable
    will contain tags related to the given tag for the given model.
    Additionally, if ``related_tag_counts`` is ``True``, each related
    tag will have a ``count`` attribute indicating the number of items
    which have it in addition to the given tag.
    """
    if queryset_or_model is None:
        try:
            queryset_or_model = kwargs.pop('queryset_or_model')
        except KeyError:
            raise AttributeError(_('tagged_object_list must be called with a queryset or a model.'))

    if tag is None:
        try:
            tag = kwargs.pop('tag')
        except KeyError:
            raise AttributeError(_('tagged_object_list must be called with a tag.'))

    tag_instance = get_tag(tag)
    if tag_instance is None:
        raise Http404(_('No Tag found matching "%s".') % tag)
    queryset = TaggedItem.objects.get_by_model(queryset_or_model, tag_instance)
    if not kwargs.has_key('extra_context'):
        kwargs['extra_context'] = {}
    kwargs['extra_context']['tag'] = tag_instance
    if related_tags:
        kwargs['extra_context']['related_tags'] = \
            Tag.objects.related_for_model(tag_instance, queryset_or_model,
                                          counts=related_tag_counts)
    return object_list(request, queryset, **kwargs)

def tags_for_object(request, model=None, order_by='?',
                    template_name=None, extra_context={}):
    """
    A view for listing all tags on a model. Tags are sorted by how many
    times they're used. Also grabs the first 5 objects in random order, or
    ordered by the order_by argument. Renders to template template_name.
    """
    ctype = ContentType.objects.get_for_model(model)

    ti = Tag.objects.filter(items__content_type=ctype).distinct().annotate(Count('items')).order_by('-items__count')

    tag_info = [{'tag': tag,
                 'count': tag.items__count,
                 'items': model.objects.filter(id__in=TaggedItem.objects.filter(content_type=ctype, tag=tag).values('object_id')).order_by(order_by)[:5]
                 }
                for tag in ti]

    return render_to_response(template_name, dict({
                'tag_info': tag_info,
                }, **extra_context),
                              context_instance=RequestContext(request))
