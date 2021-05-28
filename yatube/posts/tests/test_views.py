import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Follow, Group, Post

User = get_user_model()


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(dir=settings.BASE_DIR))
class PostPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Petuh')
        cls.author = User.objects.create_user(username='Author')
        cls.group = Group.objects.create(
            title='Группа',
            slug='test-slug'
        )
        cls.another_group = Group.objects.create(
            title='Другая группа',
            slug='another-test-slug'
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Text',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Собираем в словарь пары "имя_html_шаблона: reverse(name)"
        templates_pages_names = {
            reverse('posts:index'): 'index.html',
            reverse('posts:new_post'): 'post_create_and_edit.html',
            reverse('posts:group', kwargs={'slug': 'test-slug'}): 'group.html',
            reverse('about:author'): 'about/author.html',
            reverse('about:tech'): 'about/tech.html',
            reverse('posts:post_edit', kwargs={
                'username': f'{self.post.author}',
                'post_id': f'{self.post.id}'}): 'post_create_and_edit.html',
        }
        # Проверяем, что при обращении к name
        # вызывается соответствующий HTML-шаблон
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response.context['page'][0].text, 'Text')
        self.assertEqual(response.context['page'][0].author, self.user)
        self.assertEqual(response.context['page'][0].group, self.group)
        self.assertEqual(response.context['page'][0].image, self.post.image)

    def test_group_page_show_correct_context(self):
        """Шаблон group сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:group', kwargs={'slug': 'test-slug'}))
        self.assertEqual(response.context['group'].title, 'Группа')
        self.assertEqual(response.context['page'][0].text, 'Text')
        self.assertEqual(response.context['page'][0].author, self.user)
        self.assertEqual(response.context['page'][0].group, self.group)
        self.assertEqual(response.context['page'][0].image, self.post.image)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон редактирования поста сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={
                'username': f'{self.post.author}',
                'post_id': f'{self.post.id}'}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_group_pages_not_show_new_post(self):
        """Новый пост не попал в неправильную группу"""
        response = self.authorized_client.get(
            reverse('posts:group', kwargs={'slug': 'another-test-slug'}))
        self.assertTrue(self.post not in response.context['page'])

    def test_new_post_page_show_correct_context(self):
        """Шаблон new_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:new_post'))
        # Словарь ожидаемых типов полей формы:
        # указываем, объектами какого класса должны быть поля формы
        form_fields = {
            # При создании формы поля модели типа TextField
            # преобразуются в CharField с виджетом forms.Textarea
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        # Проверяем, что типы полей формы в словаре context
        # соответствуют ожиданиям
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(form_field, expected)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом"""
        response = self.guest_client.get(reverse(
            'posts:profile', kwargs={'username': self.user.username}))
        self.assertEqual(response.context['page'][0], self.post)
        self.assertEqual(response.context['author'], self.user)
        self.assertEqual(response.context['page'][0].image, self.post.image)

    def test_post_page_show_correct_context(self):
        """Шаблон post сформирован с правильным контекстом"""
        response = self.guest_client.get(reverse('posts:post', kwargs={
            'username': self.user.username,
            'post_id': self.post.id
        }))
        self.assertEqual(response.context['post'], self.post)
        self.assertEqual(response.context['author'], self.user)
        self.assertEqual(response.context['post'].image, self.post.image)

    def test_about_author_page_for_guest(self):
        response = self.guest_client.get(reverse('about:author'))
        self.assertEqual(response.status_code, 200)

    def test_about_tech_page_for_guest(self):
        response = self.guest_client.get(reverse('about:tech'))
        self.assertEqual(response.status_code, 200)

    def test_cache(self):
        response_before = self.authorized_client.get(
            reverse('posts:index')).content
        Post.objects.create(
            text='test cache',
            author=self.user,
        )
        response_after = self.authorized_client.get(
            reverse('posts:index')).content
        cache.clear()
        response_without_cache = self.authorized_client.get(
            reverse('posts:index')).content
        self.assertEqual(response_before, response_after)
        self.assertNotEqual(response_after, response_without_cache)

    def test_user_can_subscribe(self):
        """Авторизованный пользователь может подписываться
        на других пользователей."""
        subscription_before = self.author.following.filter(
            user=self.user).exists()
        self.authorized_client.get(reverse(
            'posts:profile_follow', args=['Author']))
        subscription_after = self.author.following.filter(
            user=self.user).exists()
        self.assertFalse(subscription_before)
        self.assertTrue(subscription_after)

    def test_user_can_unsubscribe(self):
        """Авторизованный пользователь может отписываться
        от других пользователей."""
        Follow.objects.create(
            user=self.user,
            author=self.author,
        )
        subscription_before = self.author.following.filter(
            user=self.user).exists()
        self.authorized_client.get(reverse(
            'posts:profile_unfollow', args=['Author']))
        subscription_after = self.author.following.filter(
            user=self.user).exists()
        self.assertTrue(subscription_before)
        self.assertFalse(subscription_after)

    def test_new_post_contains_in_followers_feed(self):
        # делаем подписку
        Follow.objects.create(
            user=self.user,
            author=self.author,
        )
        Post.objects.create(
            text='LoL',
            author=self.author,
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        posts_in_user_feed = len(response.context['page'])
        self.assertEqual(posts_in_user_feed, 1)

    def test_new_post_not_contains_in_nonfollowers_feed(self):
        Post.objects.create(
            text='KeK',
            author=self.author,
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        posts_in_user_feed = len(response.context['page'])
        self.assertEqual(posts_in_user_feed, 0)

    def test_non_authorized_user_cant_add_comment(self):
        comments_before = Comment.objects.count()
        form_data = {'text': 'test comment', }
        self.guest_client.post(
            reverse(
                'posts:add_comment', args=[self.user.username, self.post.id]),
            data=form_data,
            follow=True,
        )
        comments_after = Comment.objects.count()
        self.assertEqual(comments_before, comments_after)

    def test_authorized_user_can_add_comment(self):
        Comment.objects.all().delete()
        form_data = {'text': 'test comment', }
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment', args=[self.user.username, self.post.id]),
            data=form_data,
            follow=True,
        )
        comments_count = len(response.context['comments'])
        self.assertEqual(comments_count, 1)
        comment = response.context['comments'][0]
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.post, self.post)
        self.assertEqual(comment.author, self.user)


class PaginatorViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="user")
        cls.group = Group.objects.create(
            title="Название группы",
            slug="test-slug",
            description="тестовый текст"
        )
        for i in range(13):
            Post.objects.create(
                text=f"Тестовый текст {i}",
                author=cls.user,
                group=cls.group
            )

    def setUp(self):
        self.guest_client = Client()

    def test_index_first_page_contains_ten_records(self):
        """Передаётся 10 записей на странице"""
        response = self.guest_client.get(reverse("posts:index"))
        self.assertEqual(len(response.context.get("page").object_list), 10)

    def test_paginator_second_page(self):
        response = self.guest_client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context.get('page').object_list), 3)
