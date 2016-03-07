On debian / jessie

    sudo apt-get install python3.4-dev python3-psycopg2 python3-sqlalchemy
    sudo apt-get install python3-pip python3-voluptuous

Cloning and installing

    git clone http://www.github.com/jjhoo/putiikki.git
    cd putiikki
    pip3 install --user --no-use-wheel --upgrade -r requirements.txt
    pip3 install --user --upgrade .

Creating the database, assuming that the user account is allowed to create the database

    createdb --encoding=UTF8 --locale=en_GB.UTF-8 -T template0 putiikki


Travis-ci: [![Build status](https://travis-ci.org/jjhoo/putiikki.svg?branch=master)](https://travis-ci.org/jjhoo/putiikki)

Code coverage: [![codecov.io](https://codecov.io/github/jjhoo/putiikki/coverage.svg?branch=master)](https://codecov.io/github/jjhoo/putiikki?branch=master)
