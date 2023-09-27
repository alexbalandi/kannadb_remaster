# Kannadb Remaster

Random Linus Codes

![Built with Cookiecutter Django](https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg)(https://github.com/pydanny/cookiecutter-django/)

**License:** MIT

## New kannadb life

This is Avestus speaking. This repo was forked from [Linus' repo](https://github.com/LinusMain/linus) to give a new life to kannadb. Find @alexbalandi on Feh discord for any bugs or suggestions.

Currently hosted at [https://kannadb.up.railway.app/](https://kannadb.up.railway.app/)

For me personally, kannadb provides a good way to search for all instances of some useful effect (like `allies within 2 spaces can move to a space within 2 spaces`) and I plan to improve it a bit and potentially add more features like that.

The repo was adapted to use `railway.json` for railway config, `Dockerfile` as the way to build container, `run.sh` as the actual run script, `pyproject.toml` for managing all dependencies with poetry. `example.env` from now on will contain all the env vars that are actually passed for railway deployment (right now we are using PostgressSQL as main db and Redis for cache), so that we never get lost again.

If you plan on working on the repo, please use `pip3 install pre-commit` then `pre-commit install` inside the repo to make sure all auto-formatting hooks are respected.
