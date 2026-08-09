"""Who can see what, and who can change it.

Runs under Django's test runner against a throwaway database, so it needs
neither the stack nor GeoServer:

    python tools/wpsclient/manage.py test wpsclient

The scoping rules are one module (wpsclient.scope) precisely so they can be
tested here rather than inferred from 60-odd views, and the last test checks the
views really do route through it.
"""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import NoReverseMatch, get_resolver, reverse
from django.urls.resolvers import URLPattern, URLResolver

from . import scope
from .models import (ElementProvenance, ElementWCS, Job, ServerElement,
                     ServerWCS, ServerWPS)


class ScopeRulesTests(TestCase):
    """The rules themselves, without going through a view."""

    def setUp(self):
        self.alice = User.objects.create_user("alice", password="alice-pw")
        self.bob = User.objects.create_user("bob", password="bob-pw")
        self.admin = User.objects.create_user("root", password="root-pw",
                                              is_staff=True, is_superuser=True)
        self.server = ServerWCS.objects.create(title="s", url="http://s/wcs")
        self.element = ElementWCS.objects.create(server=self.server,
                                                 identifier="x")

    def test_an_owned_row_is_visible_only_to_its_owner(self):
        scope.claim(self.element, self.alice)
        self.assertIn(self.element.serverelement_ptr,
                      scope.visible_elements(self.alice))
        self.assertNotIn(self.element.serverelement_ptr,
                         scope.visible_elements(self.bob))

    def test_public_is_visible_to_everyone_logged_in(self):
        scope.claim(self.element, self.alice, is_public=True)
        self.assertIn(self.element.serverelement_ptr,
                      scope.visible_elements(self.bob))

    def test_an_unowned_row_is_admin_only(self):
        """Rows that predate ownership. Admin-only was the chosen policy, and it
        has to hold without anything special-casing "no ownership row"."""
        self.assertEqual(list(scope.visible_elements(self.alice)), [])
        self.assertIn(self.element.serverelement_ptr,
                      scope.visible_elements(self.admin))

    def test_admin_sees_everything(self):
        scope.claim(self.element, self.alice)
        self.assertIn(self.element.serverelement_ptr,
                      scope.visible_elements(self.admin))

    def test_a_public_job_publishes_the_outputs_it_produced(self):
        """The rule that is derived rather than copied: an output is public
        because the job that made it is, through ElementProvenance."""
        wps = ServerWPS.objects.create(title="w", url="http://w/wps")
        job = Job.objects.create(server=wps, identifier="carbon")
        scope.claim(job, self.alice)
        ElementProvenance.objects.create(
            element=self.element.serverelement_ptr, job=job)
        scope.claim(self.element, self.alice)

        # Private job: bob sees neither.
        self.assertNotIn(job, scope.visible_jobs(self.bob))
        self.assertNotIn(self.element.serverelement_ptr,
                         scope.visible_elements(self.bob))

        job.ownership.is_public = True
        job.ownership.save()

        # Public job: bob sees the job *and* its output, without the element
        # itself ever being toggled.
        self.assertIn(job, scope.visible_jobs(self.bob))
        self.assertIn(self.element.serverelement_ptr,
                      scope.visible_elements(self.bob))
        self.assertFalse(self.element.ownership.is_public)

    def test_seeing_a_public_row_is_not_permission_to_change_it(self):
        scope.claim(self.element, self.alice, is_public=True)
        self.assertTrue(scope.may_modify(self.alice, self.element))
        self.assertFalse(scope.may_modify(self.bob, self.element))
        self.assertTrue(scope.may_modify(self.admin, self.element))

    def test_claiming_twice_does_not_transfer_ownership(self):
        scope.claim(self.element, self.alice)
        scope.claim(self.element, self.bob)
        self.assertEqual(self.element.ownership.user, self.alice)

    def test_anonymous_sees_nothing(self):
        from django.contrib.auth.models import AnonymousUser
        scope.claim(self.element, self.alice, is_public=True)
        self.assertEqual(list(scope.visible_elements(AnonymousUser())), [])


class LoginRequiredTests(TestCase):
    """Every URL the dashboard serves needs a login.

    Enumerated from the urlconf rather than listed by hand: a view added later
    is covered the day it is added, which is the whole point of putting
    LoginRequiredMiddleware in front rather than decorating each view. The same
    check catches an accidental @login_not_required.
    """

    #: Paths that must stay reachable to a signed-out visitor. Anything not
    #: here has to redirect to the login page.
    PUBLIC = {"/accounts/login/"}

    def _urls(self):
        """One concrete URL per named route, with placeholder arguments.

        Walks the urlconf rather than reverse_dict, whose values are an
        internal 4-tuple; the pattern objects give the named groups directly.
        """
        samples = {"server_type": "WCS", "server_pk": "1", "job_pk": "1",
                   "element_id": "x", "process_id": "carbon", "args": "e30",
                   "title": "t", "url": "http://example.invalid/x"}

        def walk(resolver):
            for entry in resolver.url_patterns:
                if isinstance(entry, URLResolver):
                    yield from walk(entry)
                    continue
                if not isinstance(entry, URLPattern) or not entry.name:
                    continue
                params = list(entry.pattern.regex.groupindex)
                if any(p not in samples for p in params):
                    continue
                try:
                    yield entry.name, reverse(
                        entry.name, kwargs={p: samples[p] for p in params})
                except NoReverseMatch:
                    continue

        yield from walk(get_resolver())

    def test_every_view_requires_a_login(self):
        unprotected = []
        for name, url in self._urls():
            if url in self.PUBLIC or url.startswith("/admin/") \
                    or url.startswith("/accounts/"):
                continue
            response = self.client.get(url)
            # 302 to the login page is the pass. A 200 means the view served a
            # signed-out visitor; anything else at least did not serve data.
            if response.status_code == 200:
                unprotected.append("%s (%s)" % (name, url))
        self.assertEqual(unprotected, [],
                         "views served without a login: %s" % unprotected)

    def test_the_check_above_can_actually_fail(self):
        """Guard against a vacuous pass: if _urls() yielded nothing, or every
        request errored, the test above would pass having checked nothing."""
        self.assertGreater(len(list(self._urls())), 10)

    def test_login_page_is_reachable_signed_out(self):
        self.assertEqual(self.client.get("/accounts/login/").status_code, 200)


class VisibilityToggleTests(TestCase):
    """The UI control: POST-only, and owner-or-admin."""

    def setUp(self):
        self.alice = User.objects.create_user("alice", password="alice-pw")
        self.bob = User.objects.create_user("bob", password="bob-pw")
        self.server = ServerWCS.objects.create(title="s", url="http://s/wcs")
        self.element = ElementWCS.objects.create(server=self.server,
                                                 identifier="x")
        scope.claim(self.server, self.alice)
        scope.claim(self.element, self.alice)
        self.url = reverse("element_visibility",
                           kwargs={"server_type": "WCS",
                                   "server_pk": self.server.pk,
                                   "element_id": "x"})

    def test_owner_can_publish_and_unpublish(self):
        self.client.login(username="alice", password="alice-pw")
        self.client.post(self.url)
        self.element.refresh_from_db()
        self.assertTrue(self.element.ownership.is_public)

        self.client.post(self.url)
        self.element.ownership.refresh_from_db()
        self.assertFalse(self.element.ownership.is_public)

    def test_get_does_not_toggle(self):
        """A link, a prefetch or a crawler must not change what is published."""
        self.client.login(username="alice", password="alice-pw")
        self.client.get(self.url)
        self.element.refresh_from_db()
        self.assertFalse(self.element.ownership.is_public)

    def test_a_stranger_cannot_publish_someone_elses_element(self):
        self.client.login(username="bob", password="bob-pw")
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 404)
        self.element.refresh_from_db()
        self.assertFalse(self.element.ownership.is_public)

    def test_a_reader_of_a_public_element_still_cannot_toggle_it(self):
        self.element.ownership.is_public = True
        self.element.ownership.save()
        self.client.login(username="bob", password="bob-pw")
        self.assertEqual(self.client.post(self.url).status_code, 404)
        self.element.ownership.refresh_from_db()
        self.assertTrue(self.element.ownership.is_public)


class ViewScopingTests(TestCase):
    """The lists really are filtered, not just the helpers."""

    def setUp(self):
        self.alice = User.objects.create_user("alice", password="alice-pw")
        self.bob = User.objects.create_user("bob", password="bob-pw")
        self.wps = ServerWPS.objects.create(title="alice-server",
                                            url="http://w/wps")
        scope.claim(self.wps, self.alice)
        self.job = Job.objects.create(server=self.wps, identifier="carbon")
        scope.claim(self.job, self.alice)

    def test_dashboard_hides_another_users_servers_and_jobs(self):
        self.client.login(username="bob", password="bob-pw")
        body = self.client.get(reverse("dashboard")).content.decode()
        self.assertNotIn("alice-server", body)

    def test_dashboard_shows_your_own(self):
        self.client.login(username="alice", password="alice-pw")
        body = self.client.get(reverse("dashboard")).content.decode()
        self.assertIn("alice-server", body)

    def test_job_detail_is_404_for_a_stranger(self):
        self.client.login(username="bob", password="bob-pw")
        response = self.client.get(reverse("job_detail",
                                           kwargs={"job_pk": self.job.pk}))
        self.assertEqual(response.status_code, 404)

    def test_publishing_a_source_does_not_publish_what_is_registered_on_it(self):
        """A shared endpoint is not the same claim as shared data."""
        from .models import ElementWPS
        element = ElementWPS.objects.create(server=self.wps, identifier="carbon")
        scope.claim(element, self.alice)

        self.client.login(username="alice", password="alice-pw")
        self.client.post(reverse("server_visibility",
                                 kwargs={"server_type": "WPS",
                                         "server_pk": self.wps.pk}))
        self.wps.refresh_from_db()
        self.assertTrue(self.wps.ownership.is_public)

        # bob can now reach the source, but not the data registered on it.
        self.assertIn(self.wps.server_ptr, scope.visible_servers(self.bob))
        self.assertNotIn(element.serverelement_ptr,
                         scope.visible_elements(self.bob))

    def test_a_public_job_is_readable_but_not_runnable_by_a_stranger(self):
        self.job.ownership.is_public = True
        self.job.ownership.save()
        self.client.login(username="bob", password="bob-pw")

        self.assertEqual(
            self.client.get(reverse("job_detail",
                                    kwargs={"job_pk": self.job.pk})).status_code,
            200)
        # Readable is not runnable: job_run would submit someone else's work.
        self.assertEqual(
            self.client.get(reverse("job_run",
                                    kwargs={"job_pk": self.job.pk})).status_code,
            404)
