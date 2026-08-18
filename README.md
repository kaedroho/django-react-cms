# Django/React CMS Demo

This repository contains a clone of Wordpress built with Django and React using [Django Bridge](https://django-bridge.org) to connect them.

This demonstrates how to build an application with all logic implemented in Django views and React components used for rendering.

[See the demo live here](https://demo.django-bridge.org)

## Content types are rows in the database, not Python classes

The most Django-Bridge-y thing in here: a **content type** is a `name` plus a JSON schema stored in
a table. `djangopress/pages/schema.py` turns that schema into a real Django `Form` class at request
time, and Django Bridge serialises the form to React like any other.

The React client has never heard of a "Blog post". It renders the fields it is given. So adding a
field to a content type — through the admin UI, at runtime — changes the page editor with **no code
change, no migration and no deploy**. Adding a whole new *kind* of field is one entry in
`FIELD_TYPES` plus (sometimes) one small React component, and every content type gets it.

In a REST or GraphQL app this needs a bespoke dynamic-form-schema protocol on the wire and a form
generator on the client. Here it falls out of the architecture.

Pages also have drafts, revisions and publishing. *Save draft* and *Publish* are two submit buttons
on the same plain Django form posting to the same view; the branch is `"publish" in request.POST`.

## Running it

To get a sense of what Django Bridge is like to develop with, give it a try in one of the following ways.
I'd recommend editing [one of the frontend views](https://github.com/kaedroho/django-react-cms/blob/main/client/src/views/Home.tsx) and see it instantly re-render with your changes!
Or, if you're more of a backend dev, have a look at the [backend views](https://github.com/kaedroho/django-react-cms/blob/main/server/djangopress/pages/views.py) that supply the data for the frontend views to render.

[![Open in Gitpod](https://gitpod.io/button/open-in-gitpod.svg)](https://gitpod.io/#https://github.com/kaedroho/django-react-cms)

### With Docker compose

The easiest way to get this up and running is to use `docker compose`, a subcommand of Docker. Make sure you have Docker installed then run:

```
make setup
make superuser
make start
```

Then Djangopress should be running on [localhost:8000](http://localhost:8000)

### Without Docker compose

It's possible to run this without docker compose as well, you will need to have Python 11 and Node JS installed locally.

First open two terminals.

In the first terminal, run the following to install and start the Vite server, which builds and serves the built JavaScript code containing the frontend:

```
cd client
npm install
npm run dev
```

This should start a server at [localhost:5173](http://localhost:5173), there shouldn't be anything here, this will be used by the Django server to fetch freshly built JavaScript.

In the second terminal, run the following to install Django, create the database, create a user, then start the Django devserver:

```
cd server
poetry install
poetry run python manage.py migrate
poetry run python manage.py createsuperuser
poetry run python manage.py runserver
```

Then Djangopress should be running on [localhost:8000](http://localhost:8000)

### Demo content

Log in once (which creates your space), then:

```
python manage.py create_demo_content
```

That seeds three content types — Blog post, Landing page and Event — and a handful of pages in
draft, live and "live + draft" states, so there's something to poke at straight away.

### Tests

```
cd server
python manage.py test djangopress
```

Worth a read even if you don't run them: `djangopress/pages/tests.py` tests a whole CMS publish
flow with a plain Django `TestCase`. `response.props` hands back the *Python* objects the view
passed to React, so there's no JSON parsing, no mock service worker and no React test renderer
anywhere in the file.
