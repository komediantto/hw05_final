from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from posts.models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(
            username='Bob',
            password='tibetritualknife'
        )
        cls.group = Group.objects.create(
            title='Группа',
            slug='test-slug'
        )
        cls.post = Post.objects.create(
            text='Ваш текст',
            group=cls.group,
            author_id=cls.author.id
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='Petuh')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author = StaticURLTests.author
        self.post = StaticURLTests.post
        self.Bob = Client()
        self.Bob.force_login(self.author)

    def test_homepage(self):
        """Страница / доступна любому пользователю."""
        # Делаем запрос к главной странице и проверяем статус
        response = self.guest_client.get('/')
        # Утверждаем, что для прохождения теста код должен быть равен 200
        self.assertEqual(response.status_code, 200)

    def test_post_added_url_exist_at_desired_location(self):
        """Страница добавления поста доступна любому пользователю."""
        response = self.authorized_client.get('/new/')
        self.assertEqual(response.status_code, 200)

    def test_group_page_url_exist_at_desired_location(self):
        """Страница group доступна любому пользователю."""
        response = self.authorized_client.get('/group/test-slug/')
        self.assertEqual(response.status_code, 200)

    def test_profile_page_url_exist_at_desired_location(self):
        """Страница профиля доступна любому пользователю."""
        response = self.guest_client.get(f'/{self.user.username}/')
        self.assertEqual(response.status_code, 200)

    def test_post_page_url_exist_at_desired_location(self):
        """Страница поста доступна любому пользователю."""
        response = self.guest_client.get(
            f'/{self.author.username}/{self.post.id}/')
        self.assertEqual(response.status_code, 200)

    def test_post_edit_page_url_for_anonymous(self):
        """Страница редактирования поста перенаправляет анонима."""
        response = self.guest_client.get(
            f'/{self.author.username}/{self.post.id}/edit/')
        self.assertRedirects(
            response,
            f'/auth/login/?next=/{self.author.username}/{self.post.id}/edit/')

    def test_post_edit_page_url_for_author(self):
        """Страница редактирования поста доступна автору."""
        response = self.Bob.get(
            f'/{self.author.username}/{self.post.id}/edit/')
        self.assertEqual(response.status_code, 200)

    def test_post_edit_page_url_for_any_authorized_user(self):
        """Страница редактирования поста недоступна не автору."""
        response = self.authorized_client.get(
            f'/{self.author.username}/{self.post.id}/edit/')
        self.assertRedirects(
            response, f'/{self.author.username}/{self.post.id}/')

    def test_follow_page_for_guest_client(self):
        response = self.guest_client.get('/follow/')
        self.assertRedirects(
            response, '/auth/login/?next=/follow/'
        )

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            f'/{self.author.username}/{self.post.id}/edit/':
            'post_create_and_edit.html',
            '/new/': 'post_create_and_edit.html',
            '': 'index.html',
            '/group/test-slug/': 'group.html',
            '/follow/': 'follow.html'
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.Bob.get(url)
                self.assertTemplateUsed(response, template)

    def test_404(self):
        response = self.guest_client.get('/wrong_url/')
        self.assertEqual(response.status_code, 404)
