<div align="center">

  # Vent
  
  Vent is a Django-based student complaint management system built for handling campus-related complaints in a structured way. Students can create accounts, verify their email, submit complaints either anonymously or with their identity attached, and monitor the progress of their non-anonymous submissions. Admins can review all complaints, filter them, assign responsibility, and update complaint status from a dedicated dashboard.
  
  [![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
  [![Django 5.2](https://img.shields.io/badge/Django-5.2-092E20?style=flat-square&logo=django&logoColor=white)](https://djangoproject.com)
  [![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=flat-square&logo=mysql&logoColor=white)](https://mysql.com)
  [![Django Templates](https://img.shields.io/badge/Django_Templates-092E20?style=flat-square&logo=django&logoColor=white)](https://docs.djangoproject.com/en/stable/topics/templates/)

<div align="center">

## What It Does

### Student

- Register an account with full name, email, username, and optional student ID
- Verify email before logging in
- Log in with either username or email address
- Submit non-anonymous complaints linked to the student account
- Submit anonymous complaints without linking them to a student profile
- Upload supporting files such as documents or images
- View recent complaints from the student dashboard
- Track previously submitted non-anonymous complaints

### Admin

- Access a separate complaint management dashboard at `/admin/`
- View both anonymous and non-anonymous complaints
- Filter complaints by type, category, status, and assignment
- Search complaints by title, description, student username, or email
- Update complaint status
- Assign a department or person to a complaint
- Use Django's built-in admin at `/django-admin/` for model-level management

## Tech Stack

- Python 3.12
- Django 5.2
- MySQL
- Django Templates

## Utility Command

This project includes a cleanup command for duplicate user emails:

```bash
python manage.py cleanup_duplicate_users --dry-run
```

Remove `--dry-run` to deactivate duplicate accounts while keeping the newest one active.

## Notes

- The custom complaint dashboard uses `/admin/`, not Django's default admin route.
- Django's built-in admin has been moved to `/django-admin/`.
- Students can only track their non-anonymous complaints through the app.
- Anonymous complaints are visible to admins but are not linked to a student account.

## Testing

```bash
python manage.py test
```

Current test files are placeholders, so automated coverage is minimal.
