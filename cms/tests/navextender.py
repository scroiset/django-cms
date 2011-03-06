# -*- coding: utf-8 -*-
from __future__ import with_statement
from cms.api import create_page
from cms.models import Page
from cms.test_utils.testcases import CMSTestCase
from cms.test_utils.util.context_managers import SettingsOverride
from cms.test_utils.util.menu_extender import TestMenu
from django.conf import settings
from django.template import Template
from menus.menu_pool import menu_pool

class NavExtenderTestCase(CMSTestCase):
    def setUp(self):
        
        with SettingsOverride(CMS_MODERATOR = False):
            menu_pool.clear(settings.SITE_ID)
            
            if not menu_pool.discovered:
                menu_pool.discover_menus()
            self.old_menu = menu_pool.menus
            menu_pool.menus = {'CMSMenu':self.old_menu['CMSMenu'], 'TestMenu':TestMenu()}
          
    def tearDown(self):
        menu_pool.menus = self.old_menu
        
    def create_some_nodes(self):
        """
        Build the following tree:
        
        page1
            page2
                page3
        page4
            page5
        """
        with SettingsOverride(CMS_MODERATOR = False):
            self.page1 = create_page("page1", "nav_playground.html", "en",
                                     published=True, in_navigation=True)
            self.page2 = create_page("page2", "nav_playground.html", "en",
                                     parent=Page.objects.get(pk=self.page1.pk),
                                     published=True, in_navigation=True)
            self.page3 = create_page("page3", "nav_playground.html", "en",
                                     parent=Page.objects.get(pk=self.page2.pk),
                                     published=True, in_navigation=True)
            self.page4 = create_page("page4", "nav_playground.html", "en",
                                     published=True, in_navigation=True)
            self.page5 = create_page("page5", "nav_playground.html", "en",
                                     parent=Page.objects.get(pk=self.page4.pk),
                                     published=True, in_navigation=True)
        
    def test_01_menu_registration(self):
        with SettingsOverride(CMS_MODERATOR = False):
            self.assertEqual(len(menu_pool.menus), 2)
            self.assertEqual(len(menu_pool.modifiers) >=4, True)
        
    def test_02_extenders_on_root(self):
        with SettingsOverride(CMS_MODERATOR = False):
            self.create_some_nodes()
            page1 = Page.objects.get(pk=self.page1.pk)
            page1.navigation_extenders = "TestMenu"
            page1.save()
            context = self.get_context()
            
            tpl = Template("{% load menu_tags %}{% show_menu 0 100 100 100 %}")
            tpl.render(context) 
            nodes = context['children']
            self.assertEqual(len(nodes), 2)
            self.assertEqual(len(nodes[0].children), 4)
            self.assertEqual(len(nodes[0].children[3].children), 1)
            page1.in_navigation = False
            page1.save()
            tpl = Template("{% load menu_tags %}{% show_menu %}")
            tpl.render(context) 
            nodes = context['children']
            self.assertEqual(len(nodes), 5)
        
    def test_03_extenders_on_root_child(self):
        with SettingsOverride(CMS_MODERATOR = False):    
            self.create_some_nodes()
            page4 = Page.objects.get(pk=self.page4.pk)
            page4.navigation_extenders = "TestMenu"
            page4.save()
            context = self.get_context()
            tpl = Template("{% load menu_tags %}{% show_menu 0 100 100 100 %}")
            tpl.render(context) 
            nodes = context['children']
            self.assertEqual(len(nodes), 2)
            self.assertEqual(len(nodes[1].children), 4)
        
    def test_04_extenders_on_child(self):
        """
        TestMenu has 4 flat nodes
        """
        with SettingsOverride(CMS_MODERATOR = False):
            self.create_some_nodes()
            page1 = Page.objects.get(pk=self.page1.pk)
            page1.in_navigation = False
            page1.save()
            page2 = Page.objects.get(pk=self.page2.pk)
            page2.navigation_extenders = "TestMenu"
            page2.save()
            menu_pool.clear(settings.SITE_ID)
            context = self.get_context()
            tpl = Template("{% load menu_tags %}{% show_menu 0 100 100 100 %}")
            tpl.render(context) 
            nodes = context['children']
            self.assertEqual(len(nodes), 2)
            self.assertEqual(len(nodes[0].children), 4)
            self.assertEqual(nodes[0].children[1].get_absolute_url(), "/" )
        
    def test_05_incorrect_nav_extender_in_db(self):
        with SettingsOverride(CMS_MODERATOR = False):
            self.create_some_nodes()
            page2 = Page.objects.get(pk=self.page2.pk)
            page2.navigation_extenders = "SomethingWrong"
            page2.save()
            context = self.get_context()
            tpl = Template("{% load menu_tags %}{% show_menu %}")
            tpl.render(context) 
            nodes = context['children']
            self.assertEqual(len(nodes), 2)