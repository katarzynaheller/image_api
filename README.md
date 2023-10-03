# image_api
An API that allow registered users to upload an image in PNG or JPG format

## How to run:
1. Prepare env:
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

1. Run migrations via: `python manage.py migrate`
1. Run server via: `python manage.py runserver`
1. Add superuser via: `python manage.py createsuperuser`
1. Login as admin: `http://127.0.0.1:8000/admin/`
1. Define tier at `http://127.0.0.1:8000/admin/image_api/accounttier/add/`
1. Create user at `http://127.0.0.1:8000/admin/auth/user/`
1. Add user profile at `http://127.0.0.1:8000/admin/image_api/userprofile/add/`, select created user and defined tier
1. Login as user at: `http://127.0.0.1:8000/dj-rest-auth/login/`.
1. Now you can upload images via `http://127.0.0.1:8000/user-images/`
1. You can view uploaded images.
1. Run tests via `python manage.py test`

## Design decisions:
- dynamic images are stored as .jpeg files (to save memory space)
- while uploading image validation logic checks for min_width and min_height (to avoid blurred effect)
- to generate dynamic image only height value is required, width is calculated according to image aspect ratio
- storage backed is defined as DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage" (need to be changed for production)