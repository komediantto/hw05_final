import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post

User = get_user_model()


class CreatePostFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.user = User.objects.create_user(username='Petuh')
        cls.group = Group.objects.create(
            title='Заголовок',
            slug='test-1',
            description='Описание'
        )
        cls.post = Post.objects.create(
            text='Белиберда бла бла',
            author=cls.user,
            group=cls.group
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif,
            content_type='image/gif'
        )
        self.client = Client()
        self.client.force_login(self.user)
        self.form_data = {
            'text': 'Йоу',
            'group': self.group.id,
            'image': self.uploaded
        }

        self.post_count = Post.objects.count()

    def testing_creating_post(self):
        response = self.client.post(
            reverse('posts:new_post'),
            data=self.form_data,
            follow=True
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Post.objects.count(), self.post_count + 1)
        self.assertRedirects(response, reverse('posts:index'))

    def test_post_edit_create_post_and_redirect(self):
        """Тест post_edit"""
        post_count = self.post_count
        response = self.client.post(
            reverse('posts:post_edit', args=[self.post.author, self.post.id]),
            data=self.form_data, follow=True)
        self.assertEqual(Post.objects.first().text, self.form_data['text'])
        self.assertEqual(Post.objects.count(), post_count)
        self.assertRedirects(response,
                             reverse('posts:post',
                                     args=[self.post.author, self.post.id]))
