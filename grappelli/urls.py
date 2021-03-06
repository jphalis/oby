from django.conf.urls import patterns, url

from .views.related import RelatedLookup, M2MLookup, AutocompleteLookup
from .views.switch import switch_user


urlpatterns = patterns(
    '',

    # FOREIGNKEY & GENERIC LOOKUP
    url(r'^lookup/related/$', RelatedLookup.as_view(), name="grp_related_lookup"),
    url(r'^lookup/m2m/$', M2MLookup.as_view(), name="grp_m2m_lookup"),
    url(r'^lookup/autocomplete/$', AutocompleteLookup.as_view(), name="grp_autocomplete_lookup"),

    # SWITCH USER
    url(r'^switch/user/(?P<object_id>\d+)/$', switch_user, name="grp_switch_user"),
)
