from django.contrib.auth import get_user_model
from django.test import TestCase
from posts.models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(
            username='Bob',
            password='tibetritualknife'
        )
        cls.group = Group.objects.create(
            title='Группа',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            text='Ваш текст',
            group=cls.group,
            author_id=cls.author.id
        )

    def test_verbose_name(self):
        """Verbose_name совпадает с ожидаемым"""
        post = PostModelTest.post
        field_verboses = {
            'text': 'Ваш пост',
            'group': 'Выбери сообщество'
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name, expected)

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_help_texts = {
            'text': 'Ваш пост здесь',
            'group': 'Нужно выбрать сообщество'
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).help_text, expected)

    def test_object_name_is_title_field(self):
        """__str__ post - это строчка с содержимым post.title"""
        post = PostModelTest.post
        group = PostModelTest.group
        expected_object_name = post.text[:15]
        expected_group_name = group.title
        self.assertEqual(expected_object_name, str(post.text))
        self.assertEqual(expected_group_name, str(group.title))
