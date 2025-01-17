"""Tests for plone.api.group."""

from borg.localrole.interfaces import ILocalRoleProvider
from plone import api
from plone.api.tests.base import INTEGRATION_TESTING
from Products.CMFCore.utils import getToolByName
from unittest import mock
from zope.component import adapter
from zope.component import getGlobalSiteManager
from zope.component import provideAdapter
from zope.interface import implementer
from zope.interface import Interface

import unittest


class TestPloneApiGroup(unittest.TestCase):
    """Unit tests for group manipulation using plone.api."""

    layer = INTEGRATION_TESTING

    def setUp(self):
        """Shared test environment set-up, ran before every test."""
        self.portal = self.layer['portal']
        self.group_tool = getToolByName(self.portal, 'portal_groups')
        self.portal_membership = getToolByName(
            self.portal, 'portal_membership',
        )

    def test_create_constraints(self):
        """Test the constraints for creating a group."""
        from plone.api.exc import MissingParameterError
        with self.assertRaises(MissingParameterError):
            api.group.create()

    def test_create(self):
        """Test adding of a group, groupname is mandatory."""

        spam_group = api.group.create(groupname='spam')
        self.assertEqual(spam_group, self.group_tool.getGroupById('spam'))

    def test_create_with_title_and_desc(self):
        """Test adding of a group with title and description."""

        bacon_group = api.group.create(
            groupname='bacon',
            title='Bacon',
            description='Hmm bacon good!',
        )

        self.assertEqual(
            bacon_group,
            self.group_tool.getGroupById('bacon'),
        )
        self.assertEqual(
            bacon_group.getGroupTitleOrName(),
            'Bacon',
        )
        self.assertEqual(
            bacon_group.getProperty('description'),
            'Hmm bacon good!',
        )

    def test_create_with_roles_and_groups(self):
        """Test adding of a group with roles and groups."""

        ham_group = api.group.create(
            groupname='ham',
            roles=['Editor'],
            groups=['Reviewer'],
        )
        group = self.group_tool.getGroupById('ham')
        self.assertEqual(ham_group, group)
        self.assertIn('Editor', ham_group.getRoles())
        self.assertIn('Reviewer', ham_group.getMemberIds())

    def test_get_constraints(self):
        """Test the constraints for geting a group."""
        from plone.api.exc import MissingParameterError
        with self.assertRaises(MissingParameterError):
            api.group.get()

    def test_get_no_groupname(self):
        """Test getting a group without passing a groupname."""
        from plone.api.exc import MissingParameterError
        with self.assertRaises(MissingParameterError):
            api.group.create()

    def test_get(self):
        """Test getting a group."""
        from plone.api.exc import MissingParameterError

        # This should fail because the groupname is mandatory
        with self.assertRaises(MissingParameterError):
            api.group.create()

        # Create a group and retrieve it
        api.group.create(groupname='bacon')
        bacon = api.group.get(groupname='bacon')

        self.assertEqual(
            bacon,
            self.group_tool.getGroupById('bacon'),
        )

    def test_get_all_groups(self):
        """Test getting all groups."""

        groups = api.group.get_groups()
        self.assertEqual(len(groups), 4)

    def test_get_groups_constraints(self):
        """Test that exception is raised if wrong arguments are given."""

        # username and user are mutually exclusive
        from plone.api.exc import InvalidParameterError
        with self.assertRaises(InvalidParameterError):
            api.group.get_groups(
                username='chuck',
                user=mock.Mock(),
            )

    def test_get_groups_user(self):
        """Test retrieving of groups that the user is member of."""
        user = self.portal_membership.getAuthenticatedMember()

        api.group.create(groupname='staff')
        api.group.add_user(groupname='staff', user=user)

        groups = [g.id for g in api.group.get_groups(user=user)]
        self.assertIn('AuthenticatedUsers', groups)
        self.assertIn('staff', groups)

    def test_get_groups_username(self):
        """Test retrieving of groups that the user is member of."""
        user = self.portal_membership.getAuthenticatedMember()
        username = user.getUserName()

        api.group.create(groupname='staff')
        api.group.add_user(groupname='staff', user=user)

        groups = [g.id for g in api.group.get_groups(username=username)]
        self.assertIn('AuthenticatedUsers', groups)
        self.assertIn('staff', groups)

    def test_get_groups_nonexistant_user(self):
        """Test retrieving of groups for a user that does not exist."""
        from plone.api.exc import UserNotFoundError
        with self.assertRaises(UserNotFoundError):
            api.group.get_groups(username='theurbanspaceman')

    def test_get_groups_anonymous(self):
        from AccessControl.users import nobody

        # In test the anonymous user is aq wrapped in /plone/acl_users
        # > self.portal.acl_users in api.user.get_current().aq_chain
        # >>> True
        # In practice is is aq wrapped in /acl_users
        # > self.context.acl_users in api.user.get_current().aq_chain
        # >>> False
        # We'll force the user into /acl_users, which has no portal_groups.
        user = nobody.__of__(api.portal.get().__parent__.acl_users)
        groups = api.group.get_groups(user=user)
        self.assertEqual(groups, [])  # should be empty

    def test_delete_constraints(self):
        """Test deleting a group without passing parameters."""
        from plone.api.exc import MissingParameterError
        with self.assertRaises(MissingParameterError):
            api.group.delete()

    def test_delete_groupname_and_group(self):
        """Test deleting a group passing both groupname and group."""
        from plone.api.exc import InvalidParameterError
        with self.assertRaises(InvalidParameterError):
            api.group.delete(
                groupname='bacon',
                group=mock.Mock(),
            )

    def test_delete_group_groupname(self):
        """Test deleting a group by groupname."""

        bacon = api.group.create(groupname='bacon')
        self.assertEqual(bacon, api.group.get('bacon'))

        api.group.delete(groupname='bacon')
        self.assertIsNone(api.group.get('bacon'))

    def test_delete_group_group(self):
        """Test deleting a group by group object."""

        group = api.group.create(groupname='bacon')
        self.assertEqual(group, api.group.get('bacon'))

        api.group.delete(group=group)
        self.assertIsNone(api.group.get('bacon'))

    def test_add_user_constraints(self):
        """Test the constraints when a user is added to a group."""
        from plone.api.exc import InvalidParameterError
        with self.assertRaises(InvalidParameterError):
            api.group.add_user(
                groupname='staff',
                group=mock.Mock(),
            )

    def test_add_user_username_and_user(self):
        """Test adding a user to a group passing both username and user."""
        from plone.api.exc import InvalidParameterError
        with self.assertRaises(InvalidParameterError):
            api.group.add_user(
                groupname='staff',
                username='staff',
                user=mock.Mock(),
            )

    def test_add_user_with_nonexistant_group(self):
        """Test adding a user to a group that does not exist."""

        self.assertRaises(
            KeyError,
            api.group.add_user,
            user=mock.Mock(),
            groupname='staff',
        )

    def test_add_user_with_nonexistant_user(self):
        """Test adding a user that does not exist to a group."""
        from plone.api.exc import UserNotFoundError
        with self.assertRaises(UserNotFoundError):
            api.group.add_user(username='jane', groupname='staff')

    def test_add_user_username(self):
        """Test adding a user to a group by username."""
        group = api.group.create(groupname='staff')
        api.user.create(email='bob@plone.org', username='bob')

        api.group.add_user(groupname='staff', username='bob')

        self.assertIn(
            'staff',
            [g.id for g in api.group.get_groups(username='bob')],
        )

        self.assertIn('bob', group.getMemberIds())

    def test_add_user_user(self):
        """Test adding a user to a group by user object."""

        group = api.group.create(groupname='staff')
        user = api.user.create(email='jane@plone.org', username='jane')

        api.group.add_user(group=group, user=user)

        self.assertIn(
            'staff',
            [g.id for g in api.group.get_groups(username='jane')],
        )

        self.assertIn('jane', group.getMemberIds())

    def test_remove_user_constraints(self):
        """Test the constraints when a user is removed from a group."""
        from plone.api.exc import InvalidParameterError
        from plone.api.exc import MissingParameterError

        # Arguments ``groupname`` and ``group`` are mutually exclusive.
        with self.assertRaises(InvalidParameterError):
            api.group.remove_user(
                username='jane',
                groupname='staff',
                group=mock.Mock(),
            )
        # Arguments ``username`` and ``user`` are mutually exclusive.
        with self.assertRaises(InvalidParameterError):
            api.group.remove_user(
                groupname='staff',
                username='jane',
                user=mock.Mock(),
            )
        # At least one of ``username`` and ``user`` must be provided
        with self.assertRaises(MissingParameterError):
            api.group.remove_user(groupname='staff')
        # At least one of ``groupname`` and ``group`` must be provided
        with self.assertRaises(MissingParameterError):
            api.group.remove_user(username='jane')

    def test_remove_user(self):
        """Test removing a user from a group."""

        api.group.create(groupname='staff')
        api.user.create(email='jane@plone.org', username='jane')
        api.user.create(email='bob@plone.org', username='bob')
        api.group.add_user(groupname='staff', username='jane')
        api.group.add_user(groupname='staff', username='bob')

        # Delete user by username from group
        api.group.remove_user(groupname='staff', username='bob')

        group = api.group.get(groupname='staff')
        user = api.user.get(username='jane')

        # Delete user by user object from group
        api.group.remove_user(group=group, user=user)

        self.assertNotIn('staff', api.group.get_groups(username='bob'))
        self.assertNotIn('staff', api.group.get_groups(username='jane'))

        self.assertNotIn('bob', group.getMemberIds())
        self.assertNotIn('jane', group.getMemberIds())

    def test_remove_user_with_nonexistant_user(self):
        """Test removing a user from a group when the user does not exist"""
        from plone.api.exc import UserNotFoundError
        api.group.create(groupname='staff')
        group = api.group.get(groupname='staff')
        with self.assertRaises(UserNotFoundError):
            api.group.remove_user(group=group, username='iamnothere')

    def test_grant_roles(self):
        """Test grant roles."""
        from plone.api.exc import InvalidParameterError
        from plone.api.exc import MissingParameterError
        group = api.group.create(groupname='foo')

        # You can't grant Anonymous
        with self.assertRaises(ValueError):
            api.group.grant_roles(
                groupname='foo',
                roles=['Anonymous'],
            )

        # You can't grant Authenticated
        with self.assertRaises(ValueError):
            api.group.grant_roles(
                groupname='foo',
                roles=['Authenticated'],
            )

        # Roles are required
        with self.assertRaises(MissingParameterError):
            api.group.grant_roles(groupname='foo')

        # Groupname and group are mutually exclusive
        with self.assertRaises(InvalidParameterError):
            api.group.grant_roles(
                groupname='foo',
                group=group,
                roles=['Reviewer'],
            )

        api.group.grant_roles(groupname='foo', roles=['Editor'])
        self.assertIn('Editor', api.group.get_roles(groupname='foo'))
        self.assertIn('Editor', api.group.get_roles(group=group))

        api.group.grant_roles(groupname='foo', roles=('Contributor',))
        self.assertIn('Contributor', api.group.get_roles(groupname='foo'))
        self.assertIn('Contributor', api.group.get_roles(group=group))

        api.group.grant_roles(groupname='foo', roles=['Reader', 'Reader'])
        ROLES = {'Editor', 'Contributor', 'Reader', 'Authenticated'}
        self.assertEqual(ROLES, set(api.group.get_roles(groupname='foo')))
        self.assertEqual(ROLES, set(api.group.get_roles(group=group)))

    def test_revoke_roles(self):
        """Test revoke roles."""
        from plone.api.exc import InvalidParameterError
        from plone.api.exc import MissingParameterError
        group = api.group.create(groupname='bar')

        # You can't revoke Anonymous
        with self.assertRaises(ValueError):
            api.group.revoke_roles(
                groupname='bar',
                roles=['Anonymous'],
            )

        # You can't revoke Authenticated
        with self.assertRaises(ValueError):
            api.group.revoke_roles(
                groupname='bar',
                roles=['Authenticated'],
            )

        # Roles are required
        with self.assertRaises(MissingParameterError):
            api.group.revoke_roles(groupname='foo')

        # Groupname and group are mutually exclusive
        with self.assertRaises(InvalidParameterError):
            api.group.revoke_roles(
                groupname='foo',
                group=group,
                roles=['Reviewer'],
            )

        api.group.grant_roles(groupname='bar', roles=['Reviewer', 'Editor'])

        api.group.revoke_roles(groupname='bar', roles=['Reviewer'])
        self.assertNotIn('Reviewer', api.group.get_roles(groupname='bar'))
        self.assertNotIn('Reviewer', api.group.get_roles(group=group))
        self.assertIn('Editor', api.group.get_roles(groupname='bar'))
        self.assertIn('Editor', api.group.get_roles(group=group))

        api.group.revoke_roles(groupname='bar', roles=['Editor'])
        ROLES = {'Authenticated'}
        self.assertEqual(ROLES, set(api.group.get_roles(groupname='bar')))
        self.assertEqual(ROLES, set(api.group.get_roles(group=group)))

    def test_grant_roles_in_context(self):
        """Test grant roles."""

        group = api.group.create(groupname='foo')

        portal = api.portal.get()
        folder = api.content.create(
            container=portal,
            type='Folder',
            id='folder_one',
            title='Folder One',
        )
        document = api.content.create(
            container=folder,
            type='Document',
            id='document_one',
            title='Document One',
        )

        api.group.grant_roles(groupname='foo', roles=['Editor'], obj=folder)
        self.assertIn(
            'Editor',
            api.group.get_roles(groupname='foo', obj=folder),
        )
        self.assertIn('Editor', api.group.get_roles(group=group, obj=folder))
        self.assertIn(
            'Editor',
            api.group.get_roles(groupname='foo', obj=document),
        )
        self.assertIn('Editor', api.group.get_roles(group=group, obj=document))

        api.group.grant_roles(
            groupname='foo',
            roles=('Contributor',),
            obj=folder,
        )
        self.assertIn(
            'Contributor',
            api.group.get_roles(groupname='foo', obj=folder),
        )
        self.assertIn(
            'Contributor',
            api.group.get_roles(group=group, obj=folder),
        )
        self.assertIn(
            'Contributor',
            api.group.get_roles(groupname='foo', obj=document),
        )
        self.assertIn(
            'Contributor',
            api.group.get_roles(group=group, obj=document),
        )

        ROLES = {'Editor', 'Contributor', 'Authenticated'}
        self.assertEqual(
            ROLES,
            set(api.group.get_roles(groupname='foo', obj=folder)),
        )
        self.assertEqual(
            ROLES,
            set(api.group.get_roles(group=group, obj=folder)),
        )
        self.assertEqual(
            ROLES,
            set(api.group.get_roles(groupname='foo', obj=document)),
        )
        self.assertEqual(
            ROLES,
            set(api.group.get_roles(group=group, obj=document)),
        )
        ROLES = {'Editor', 'Contributor'}
        self.assertEqual(
            ROLES,
            set(
                api.group.get_roles(
                    groupname='foo',
                    obj=folder,
                    inherit=False,
                ),
            ),
        )
        self.assertEqual(
            ROLES,
            set(api.group.get_roles(group=group, obj=folder, inherit=False)),
        )
        self.assertEqual(
            set(),
            set(
                api.group.get_roles(
                    groupname='foo',
                    obj=document,
                    inherit=False,
                ),
            ),
        )
        self.assertEqual(
            set(),
            set(api.group.get_roles(group=group, obj=document, inherit=False)),
        )

    def test_local_roles_without_inheritance(self):
        """Test granting and getting local_roles."""
        api.group.create(groupname='foo')

        portal = api.portal.get()
        folder = api.content.create(
            container=portal,
            type='Folder',
            id='folder_one',
            title='Folder One',
        )
        document = api.content.create(
            container=folder,
            type='Document',
            id='document_one',
            title='Document One',
        )
        self.assertEqual(
            ['Authenticated'],
            api.group.get_roles(groupname='foo'),
        )
        # Add the editor-role as global role
        api.group.grant_roles(groupname='foo', roles=['Editor'])
        self.assertCountEqual(
            ['Authenticated', 'Editor'],
            api.group.get_roles(groupname='foo'),
        )
        # local_roles plus global_roles
        self.assertCountEqual(
            ['Authenticated', 'Editor'],
            api.group.get_roles(groupname='foo', obj=folder),
        )
        # only local_roles
        self.assertEqual(
            [],
            api.group.get_roles(groupname='foo', obj=folder, inherit=False),
        )

        # The Contributor-role is added
        api.group.grant_roles(
            groupname='foo', roles=['Contributor'], obj=folder,
        )
        self.assertCountEqual(
            ['Contributor'],
            api.group.get_roles(groupname='foo', obj=folder, inherit=False),
        )
        # local_roles plus global_roles
        self.assertEqual(
            {'Authenticated', 'Editor', 'Contributor'},
            set(api.group.get_roles(groupname='foo', obj=document)),
        )
        # no only-local roles
        self.assertEqual(
            set(),
            set(
                api.group.get_roles(
                    groupname='foo',
                    obj=document,
                    inherit=False,
                ),
            ),
        )
        api.group.grant_roles(
            groupname='foo', roles=['Contributor'], obj=document,
        )
        # one only-local role
        self.assertEqual(
            {'Contributor'},
            set(
                api.group.get_roles(
                    groupname='foo',
                    obj=document,
                    inherit=False,
                ),
            ),

        )

        # The Editor-role is added even though it is already a global role
        api.group.grant_roles(groupname='foo', roles=['Editor'], obj=folder)
        self.assertEqual(
            {'Contributor', 'Editor'},
            set(
                api.group.get_roles(
                    groupname='foo',
                    obj=folder,
                    inherit=False,
                ),
            ),
        )

    def test_local_roles_disregard_adapter(self):
        """Test that borg.localrole-adpaters are not copied when granting
        local roles."""
        portal = api.portal.get()
        folder = api.content.create(
            container=portal,
            type='Folder',
            id='folder_one',
            title='Folder One',
        )
        api.group.create(groupname='foo')

        self.assertEqual(
            api.group.get_roles(groupname='foo', obj=folder),
            ['Authenticated'],
        )
        self.assertEqual(
            api.group.get_roles(groupname='foo', obj=folder, inherit=False),
            [],
        )

        # throw in a adapter granting the reviewer-roles
        @adapter(Interface)
        @implementer(ILocalRoleProvider)
        class LocalRoleProvider:

            def __init__(self, context):
                self.context = context

            def getRoles(self, principal_id):
                return ('Reviewer',)

        provideAdapter(LocalRoleProvider)

        # the adapter-role is added for get_role
        self.assertCountEqual(
            api.group.get_roles(groupname='foo', obj=folder),
            ['Authenticated', 'Reviewer'],
        )

        self.assertCountEqual(
            api.group.get_roles(groupname='foo', obj=folder, inherit=False),
            ['Reviewer'],
        )

        # Assign a local role
        api.group.grant_roles(
            groupname='foo', roles=['Contributor'], obj=folder,
        )
        self.assertCountEqual(
            api.group.get_roles(groupname='foo', obj=folder),
            ['Authenticated', 'Contributor', 'Reviewer'],
        )

        # The adapter role in in the local roles but not persistent
        self.assertCountEqual(
            api.group.get_roles(groupname='foo', obj=folder, inherit=False),
            ['Contributor', 'Reviewer'],
        )
        local_roles = getattr(folder, '__ac_local_roles__', {})
        self.assertCountEqual(
            local_roles.get('foo'),
            ['Contributor'],
        )
        # cleanup
        gsm = getGlobalSiteManager()
        gsm.unregisterAdapter(
            factory=LocalRoleProvider, provided=ILocalRoleProvider,
        )

    def test_revoke_roles_in_context(self):
        """Test revoke roles."""

        group = api.group.create(groupname='ploneboat')

        portal = api.portal.get()
        folder = api.content.create(
            container=portal,
            type='Folder',
            id='folder_one',
            title='Folder One',
        )
        document = api.content.create(
            container=folder,
            type='Document',
            id='document_one',
            title='Document One',
        )
        api.group.grant_roles(
            groupname='ploneboat',
            roles=['Reviewer', 'Editor'],
            obj=folder,
        )

        api.group.revoke_roles(
            groupname='ploneboat',
            roles=['Reviewer'],
            obj=folder,
        )
        self.assertIn(
            'Editor',
            api.group.get_roles(groupname='ploneboat', obj=folder),
        )
        self.assertIn('Editor', api.group.get_roles(group=group, obj=folder))
        self.assertIn(
            'Editor',
            api.group.get_roles(groupname='ploneboat', obj=document),
        )
        self.assertIn('Editor', api.group.get_roles(group=group, obj=document))
        self.assertNotIn(
            'Reviewer',
            api.group.get_roles(groupname='ploneboat', obj=folder),
        )
        self.assertNotIn(
            'Reviewer',
            api.group.get_roles(group=group, obj=folder),
        )
        self.assertNotIn(
            'Reviewer',
            api.group.get_roles(groupname='ploneboat', obj=document),
        )
        self.assertNotIn(
            'Reviewer',
            api.group.get_roles(group=group, obj=document),
        )

        api.group.revoke_roles(
            groupname='ploneboat',
            roles=['Editor'],
            obj=folder,
        )
        self.assertNotIn(
            'Editor',
            api.group.get_roles(groupname='ploneboat', obj=folder),
        )
        self.assertNotIn(
            'Editor',
            api.group.get_roles(group=group, obj=folder),
        )
        self.assertNotIn(
            'Editor',
            api.group.get_roles(groupname='ploneboat', obj=document),
        )
        self.assertNotIn(
            'Editor',
            api.group.get_roles(group=group, obj=document),
        )

        ROLES = {'Authenticated'}
        self.assertEqual(
            ROLES,
            set(api.group.get_roles(groupname='ploneboat', obj=folder)),
        )
        self.assertEqual(
            ROLES,
            set(api.group.get_roles(group=group, obj=folder)),
        )
        self.assertEqual(
            ROLES,
            set(api.group.get_roles(groupname='ploneboat', obj=document)),
        )
        self.assertEqual(
            ROLES,
            set(api.group.get_roles(group=group, obj=document)),
        )

    def test_local_roles_no_inheritance(self):
        """Test possibility to disregard roles
        for inherited groups."""
        api.group.create(groupname='ploneboat')
        portal = api.portal.get()
        folder = api.content.create(
            container=portal,
            type='Folder',
            id='folder_one',
            title='Folder One',
        )
        document = api.content.create(
            container=folder,
            type='Document',
            id='document_one',
            title='Document One',
        )
        api.group.grant_roles(
            groupname='ploneboat',
            roles=['Reviewer', 'Editor'],
            obj=document,
        )
        document.manage_setLocalRoles('AuthenticatedUsers', ('Reader',))
        self.assertNotIn(
            'Reader',
            api.group.get_roles(groupname='ploneboat', inherit=False, obj=document),  # noqa: E501
        )
