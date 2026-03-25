# Python AI Backend Template


## Getting Started

### Setup 

```
conda create -n <env_name> python=3.11
conda activate <env_name>

pip install -r requirements.txt
```

install mypy types:
```
mypy --install-types
```

install the precommit hooks:
```
pre-commit install
```

### Development

Fireup the fastapi server
```
./scripts/run-dev.sh
```

to run other python files directly make sure to  change working directory to `src/`

For running script from the root:
```
PYTHONPATH=./src python src/somescript.py
```

#### VScode Specific setup

Install the following extensions for a **smooth** development experience
- `ms-python.python`
- `ms-python.pylint`
- `ms-python.vscode-pylance`
- `ms-python.black-formatter`
- `ms-python.mypy-type-checker`

#### HTML TAG

Add this tag into the head section of html to upgrade all HTTP requests to HTTPS, 

```
<meta http-equiv="Content-Security-Policy" content="upgrade-insecure-requests">
```

#### Development checklist
- [x] Place all environment variables under `.env`
- [x] Make sure pylint score is above `9/10`
- [x] All Source files `.py`/`.ipynb` files should be under `src` and no other extension is allowed
- [x] keep all data/binary files/datasets/model weights under the data directory
- [x] Be carefull when adding file to the root of the project, when adding files to root, make sure it is exempted in the root `.gitignore`
- [x] Add sufficient examples under `src/examples` showcasing differnt usecases independently with resonable defaults
- [x] Be varry of the yellow/red squiggly underlining by the linter. Make sure there are no warnings/errors from the linter
- [x] for all prefix all routers with `/api/v<VERSION>` e.g `/api/v1`. 



### Production

```
./scripts/run.sh
```

## Docs

```
Access `<HOST>:<PORT>/api/docs` or ``<HOST>:<PORT>/api/redocs`` to access API documentation (OpenAPI)
```

## Project Structure

```
.
├── data/                      # all non code files/data goes here
│   └── model_weights/         # example directory to place weights
├── deploy/
├── Dockerfile
├── examples                   # scripts to run example. some example may require preconfigureing  things in a bash script combined with python scripts in the src/example directory
├── requirements.txt           #all application requirement. version must be fixed
├── scripts/                   # all application related scripts goes here
├── src
|   |── deps/                  # external code/git sub modules can go here
|   |── notebooks/             # ipython/jupyter notebooks
│   ├── app
│   │   ├── main.py            # the main application server entrypoint 
│   │   └── routers/           # all apis/routes goes here
│   ├── application_context.py # global shareable objects e.g database connection
│   ├── config.py              # application configuration 
│   ├── examples               # python scripts showcasing differnet usecases within the application
│   ├── models/                # sample directory where you can place ai model code. on this level you can add any number of directories depending on the need of the application
│   ├── scripts                # python script that may perform some independent tasks e.g preprocessing data/ downloading data etc
│   │   └── test_script.py
│   └── utils.py               # all utility funtions in this common module
```



## Linters and Formaters
Pylint is being using for linting purposes. pylintrc is based on [Google Python Style guide](https://google.github.io/styleguide/pyguide.html)

Black is the default formater used. vscode also uses black as the default formater as described in the .vscode/setting.json

TODO: add black as a precommit hook

## Semantic Versioing and Commit Linting

Commit message format is default to [Conventional Commit](https://www.conventionalcommits.org/en/about/)

[commitzen](https://commitizen-tools.github.io/commitizen/) is used for git commit linting combined with `pre-commit` commit hook.


`python-semantic-release` package is used for semantic release. this may need further configuring to setup with CI properly 

For checking the next version:
```
semantic-release version --print
```
for further option see `semantic-release --help`



## Authentication
Basic auth is setup

It is not recommended to generate token from this service
user external dedicated auth providers 

When setting up user related information from tokens in routes,
you can setup a database or get that information from an external 
service

For testing endpoint with the `POST multi-part` form data credentials at the token endpoint `/api/v1/user/token`:

```
username: ai
password: secret
```

token auth can also be done through the openapi swagger doc `Authorize` button on the web

### Custom Auth provider
You can provide your own custom auth providers
For this template a static auth provider is provided 
which verifies and extract the user id/username from the token


After implementing the `AuthProviderBase` for your custom auth provider  you can add it to the `AuthFactory` instance

middlewares will use the appropriate auth provider 
from the envirnment variable `AUTH_CURRENT_PROVIDER` whose
value must be  from the defined `AuthProvider` enumeration

When extending the custom auth provider, add the appropriate enumeration key/value as well


## Testing
TODO


## Author
- [Muhammad Harris](https://www.linkedin.com/in/harris-perceptron/)