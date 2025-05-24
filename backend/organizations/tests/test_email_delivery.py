from django.core.mail import send_mail
from django.test import TestCase

class EmailDeliveryTest(TestCase):
    def test_send_email(self):
        sent = send_mail(
            'Asunto de prueba',
            'Este es un mensaje de prueba',
            'osmanileon92@gmail.com',
            ['osmanileon92@gmail.com'],  # Puedes cambiar por otro destinatario si lo deseas
            fail_silently=False,
        )
        self.assertEqual(sent, 1) 