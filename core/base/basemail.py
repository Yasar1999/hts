import os
import threading
from django.core.mail import EmailMessage
from django.conf import settings
import requests
from django.http import HttpResponse
from django.template.loader import get_template

from base.generic_functions import get_traceback


class BaseMails:

    @classmethod
    def send_mail(cls, subject, recipients, template_name, template_data, attachment=None,
                  attachments_full_path=None, data_attachments=list(), cc_to=[], bcc_to=[]):
        """" Sends email for the provided details """
        '''Attachment is Optional Parameters. Attachments should be dist its contains url and extensions'''

        from_email = settings.EMAIL_HOST_USER
        html = get_template(template_name)
        html_content = html.render(template_data)
        if recipients and len(recipients) > 0:
            recipients = list(set(recipients))
            if None in recipients:
                recipients.remove(None)

        try:
            mail = EmailMessage(subject, html_content, to=recipients, from_email=from_email, cc=cc_to, bcc=bcc_to)
            mail.content_subtype = 'html'
            if attachment is not None:
                mail.attach_file(settings.BASE_DIR + '/' + attachment['url'], attachment['extensions'])

            elif attachments_full_path is not None:
                try:
                    response = requests.get(attachments_full_path)

                    if response.status_code == 200:
                        file_data = response.content

                        file_name = os.path.basename(attachments_full_path)
                        mail.attach(file_name, file_data)
                    else:
                        print(f"Failed to retrieve the object. Status code: {response.status_code}")

                except requests.exceptions.RequestException as e:
                    print("Error:", e)

            """ Attaching data as files into email """
            for attachment in data_attachments:
                mail.attach(filename=attachment['filename'],
                            content=attachment['content'].decode('utf-8'),
                            mimetype=attachment['mimetype'])
            return mail.send(fail_silently=True)

        except Exception as e:
            exception = get_traceback(e)
            return HttpResponse(exception)


def send_email_in_thread(subject, recipients, template_name, template_data):
    try:
        my_thread = threading.Thread(target=BaseMails.send_mail, args=(subject, recipients, template_name, template_data))
        my_thread.start()

    except Exception as e:
        print(e)
