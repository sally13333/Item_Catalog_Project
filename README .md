# Full Stack Web Developer Nanodegree Program
## Project :Item Catalog 
***
***

# Contents:

  - Item Catalog application
  - Requirements
  - Prepare The Software 
  - Structure of Application :
  - Python Codes
  -  JSON endpoints
  - Running the Item catalog 

  
***
&nbsp;   
#### Item catalog:
>an application that provides a list of items within a variety of categories and integrate third party user registration and authentication. Authenticated users should have the ability to post, edit, and delete their own items.

You will be creating this project essentially from scratch, no templates have been provided for you. This means that you have free reign over the HTML, the CSS, and the files that include the application itself utilizing Flask.
&nbsp;
***
#### Requirements:
>if you want use vagrant to run this project you have to install
  - [Vagrant ](https://www.vagrantup.com/downloads.html)
  - [VirtualBox ](https://www.virtualbox.org/wiki/Download_Old_Builds_5_1)
>Alternatively if you did not want  to rely on Vagrant, you could  set-up and run the project in an environment of your choosing. In this case the requirements would be:
  - [Python 3](https://www.python.org/downloads/)
  - [PostgreSQL](https://www.postgresql.org/download/)
  - [psycopg2](https://pypi.org/project/psycopg2/)
***
#### Prepare The Software 
##### 1- Download the VM configuration
There are a couple of different ways you can download the VM configuration.

You can download and unzip this file:[ FSND-Virtual-Machine.zip ](https://www.vagrantup.com/downloads.html)  This will give you a directory called FSND-Virtual-Machine. It may be located inside your Downloads folder.

Alternately, you can use Github to fork and clone the repository https://github.com/udacity/fullstack-nanodegree-vm.

Either way, you will end up with a new directory containing the VM files. Change to this directory in your terminal with `cd`. Inside, you will find another directory called vagrant. Change directory to the vagrant directory

##### 2- Start the virtual machine
on your terminal, inside the vagrant subdirectory, run the command `vagrant up`. This will cause Vagrant to download the Linux operating system and install it. This may take quite a while (many minutes) depending on how fast your Internet connection .
When `vagrant up` is finished running, you will get your shell prompt back. At this point, you can run `vagrant ssh` to log in to your newly installed Linux VM!
***
#### Structure of Application :
>inside `vagrant` directory the you must have the following :    
- `vagrant`
    - catalog
      
        - database_setup.py (contain all class and relations to build database)
        - seeder.py (contain fake data)
        - application.py (contain all method to implement application) 
        - client_secrets.json(contain the client ID, client secret, and other  OAuth 2.0 parameters.)
    - static (contain css file)
    - templates (contains all veiws for application )
 ***
***
## python codes:
##### 1- creating the Database :
> we will create database and in `database_setup.py ` using class method  and object concept and sqlalchamy libraries .
we have three class :
- User( contain `user` table ,describe user attribute)
- Categories (contain `categories` table ,describe categories attribute)
- CategoriesItem( contain `categories_item` table ,describe items attribute)
> in each class we will determine each column(type,size,constraint...) and relation with  other tables depending on our needs if you have not creating  a database  before you can use this [link](https://auth0.com/blog/sqlalchemy-orm-tutorial-for-python-developers/) to get a Tutorial about it also ,we will add serelize function to get information to our JSON endpoints -which arrange our database in summury way .
```python
# first import all sqlalchemy library that we will use 
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

# bulid User class method 
class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))

#build Categories class method  
class Categories(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
        }

#build CategoriesItem class method  
class CategoriesItem(Base):
    __tablename__ = 'categories_item'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(250))
    course = Column(String(250))
    categories_id = Column(Integer, ForeignKey('categories.id'))
    categories = relationship(Categories)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'description': self.description,
            'id': self.id,
            'course': self.course,
        }
engine = create_engine('sqlite:///categories.db')
Base.metadata.bind = engine
Base.metadata.create_all(engine)

```
***
##### 2-Fake Database

 >After we create database ,we fill `seeder.py`by calling class method with Fake data to appeare in our pages ,then we will use two command to insert to database 1-`session.add( )`2-` session.commit()`, here is an example
``` python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Categories, CategoriesItem, User

engine = create_engine('sqlite:///categories.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

User1 = User(name="Robo Barista", email="tinnyTim@udacity.com",
             picture='''https://pbs.twimg.com/profile_images/2671170543
             /18debd694829ed78203a5a36dd364160_400x400.png''')

session.add(User1)
session.commit()

c1 = Categories(user_id=1, name="Arab Designers")
session.add(c1)
session.commit()

session.commit()
User1 = User(name="Sally qassem", email="sallyqassem13333@gmail.com",
             picture='''https://www.logolynx.com/images/logolynx
             /0c/0c79eccd47ca898469ee2e9b12bbf907.jpeg''')
c2 = Categories(user_id=2, name="Foreigner Designers")
session.add(c2)
session.commit()
```

##### 3- applicatin.py:
> we depend on methods to implement backend for each view (html) file individully as we needed using flask platform and sqlalchemy to build it 
```python 
from flask import Flask, render_template, request
from flask import redirect, jsonify, url_for, flash

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Categories, CategoriesItem, User

from flask import session as login_session
import random
import string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Item catalog "


# Connect to Database and create database session
engine = create_engine('sqlite:///categories.db?check_same_thread=False')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code, now compatible with Python3
    request.get_data()
    code = request.data.decode('utf-8')

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    # Submit request, parse response - Python3 compatible
    h = httplib2.Http()
    response = h.request(url, 'GET')[1]
    str_response = response.decode('utf-8')
    result = json.loads(str_response)

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += """
    style = "width: 300px;
             height: 300px;
             border-radius: 150px;
             -webkit-border-radius: 150px;
             -moz-border-radius: 150px;">
            """
    flash("you are now logged in as %s" % login_session['username'])
    return output
# User Helper Functions


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    print login_session['access_token']
    url = ('https://accounts.google.com/o/oauth2/revoke?token=%s'
           % login_session['access_token'])
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['user_id']
        del login_session['email']
        del login_session['picture']
        response = make_response(
            json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return redirect('/categories')
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response
# JSON APIs to view Categories item


@app.route('/categories/<int:categories_id>/categoriesitem/JSON')
def CategoriesItemJSON(categories_id):
    category = session.query(Categories).filter_by(id=categories_id).one()
    items = session.query(CategoriesItem).filter_by(
        categories_id=categories_id).all()
    return jsonify(CategoriesItems=[i.serialize for i in items])
# JSON APIs to view specific Categories item


@app.route('''/categories/<int:categories_id>/categoriesitem
/<int:categoriesitem_id>/JSON''')
def categoriesItemDetailJSON(categories_id, categoriesitem_id):
    CategoriesItem_Item = session.query(CategoriesItem).filter_by(
        id=categoriesitem_id).one()
    return jsonify(CategoriesItem_Item=CategoriesItem_Item.serialize)


# JSON APIs to view Categories
@app.route('/categories/JSON')
def categoriesJSON():
    category = session.query(Categories).all()
    return jsonify(categories=[r.serialize for r in category])


# Show all categories
@app.route('/')
@app.route('/categories/')
def showCategories():
    category = session.query(Categories).order_by(asc(Categories.name))
    latestitem = session.query(CategoriesItem).order_by(
        CategoriesItem.id.desc()).limit(5)
    if 'username' not in login_session:
        return render_template(
            'publiccategories.html', category=category, latestitem=latestitem)
    else:
        return render_template(
            'categories.html', category=category, latestitem=latestitem)


# Show a categoreis items
@app.route('/categoreis/<int:categories_id>/')
@app.route('/categoreis/<int:categories_id>/categoriesitem')
def showCategoriesItem(categories_id):
    category = session.query(Categories).order_by(asc(Categories.name))
    categories = session.query(Categories).filter_by(id=categories_id).one()
    items = session.query(CategoriesItem).filter_by(
        categories_id=categories_id).all()
    return render_template(
        'categoriesitem.html', items=items,
        categories=categories, category=category)


# Show  detail for specific item
@app.route('''/categories/<int:categories_id>/categoriesitem/
<int:categoriesitem_id>/items''')
def showCategoriesItemDetail(categories_id, categoriesitem_id):
    categories = session.query(Categories).filter_by(id=categories_id).one()
    item = session.query(CategoriesItem).filter_by(id=categoriesitem_id).one()
    if 'username' in login_session:   # make sure user login
        # make sure user is the owner
        if login_session['user_id'] == item.user_id:
            return render_template(
                'showCategoriesItemDetail.html',
                item=item, categories=categories)
    else:
        return render_template(
            'showpublicCategoriesItemDetail.html',
            item=item, categories=categories)


# Create a new  item
@app.route('''/categories/<int:categories_id>
/categoriesitem/new/''', methods=['GET', 'POST'])
def newCategoriesItem(categories_id):
    if 'username' not in login_session:  # make sure user login
        return redirect('/login')
    categories = session.query(Categories).filter_by(id=categories_id).one()
    if request.method == 'POST':
        newItem = CategoriesItem(
            name=request.form['name'],
            description=request.form['description'],
            course=request.form['course'],
            categories_id=categories_id,
            user_id=login_session["user_id"])
        session.add(newItem)
        session.commit()
        flash('New categories %s Item Successfully Created' % (newItem.name))
        return redirect(url_for(
            'showCategoriesItem', categories_id=categories_id))
    else:
        return render_template(
            'newcategoriesitem.html', categories_id=categories_id)


# Edit  item
@app.route('''/categories/<int:categories_id>
/categoriesitem/<int:categoriesitem_id>/edit''', methods=['GET', 'POST'])
def editCategoriesItem(categories_id, categoriesitem_id):
    if 'username' in login_session:  # make sure user login
        editedItem = session.query(CategoriesItem).filter_by(
            id=categoriesitem_id).one()
        categories = session.query(Categories).filter_by(
            id=categories_id).one()
        # make sure user is the owner
        if login_session['user_id'] == editedItem.user_id:
            if request.method == 'POST':
                if request.form['name']:
                    editedItem.name = request.form['name']
                if request.form['description']:
                    editedItem.description = request.form['description']
                if request.form['course']:
                    editedItem.course = request.form['course']
                session.add(editedItem)
                session.commit()
                flash('Item Successfully Edited')
                return redirect(url_for(
                    'showCategoriesItem', categories_id=categories_id))
            else:
                return render_template(
                    'editcategoriesitem.html', categories_id=categories_id,
                    categoriesitem_id=categoriesitem_id, item=editedItem)
        else:
            flash('you do not have the access to delete this item')
            return redirect(url_for(
                'showCategoriesItem', categories_id=categories_id))
    else:
        return redirect('/login')


# Delete a menu item
@app.route('''/categories/<int:categories_id>
/categoriesitem/<int:categoriesitem_id>/delete''', methods=['GET', 'POST'])
def deleteCategoriesItem(categories_id, categoriesitem_id):
    if 'username'in login_session:   # make sure user login
        categories = session.query(Categories).filter_by(
            id=categories_id).one()
        itemToDelete = session.query(CategoriesItem).filter_by(
            id=categoriesitem_id).one()
        # make sure user is the owner
        if login_session['user_id'] == itemToDelete.user_id:
            if request.method == 'POST':
                session.delete(itemToDelete)
                session.commit()
                flash('Course Item Successfully Deleted')
                return redirect(url_for(
                    'showCategoriesItem', categories_id=categories_id))
            else:
                return render_template(
                    'deletecategoriesitem.html', item=itemToDelete,
                    categories_id=categories_id,
                    categoriesitem=categoriesitem_id)
        else:
            flash('you do not have the access to delete this item ')
            return redirect(url_for(
                'showCategoriesItem', categories_id=categories_id))
    else:
        return redirect('/login')

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
```
***
 ### JSON endpoints
 >This concept  turn object data in easily serializeable formata for categories, all itemsor specific one for example:
 - view Categories
 ``` python 
 # from database_setup.py 
  @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
        }
# from application.py
# JSON APIs to view Categories
@app.route('/categories/JSON')
def categoriesJSON():
    category = session.query(Categories).all()
    return jsonify(categories=[r.serialize for r in category])
``` 
 output of` http://localhost:8000/categories/JSON `will be: 
 ```{
  "categories": [
    {
      "id": 1, 
      "name": "Arab Designers"
    }, 
    {
      "id": 2, 
      "name": "Foreigner Designers"
    }
  ]
}
```
 ***
### Running the Item catalog 
Once it is up and running, type `vagrant ssh`. This will log your terminal into the virtual machine, and you'll get a Linux shell prompt. When you want to log out, type exit at the shell prompt. To turn the virtual machine off (without deleting anything), type vagrant halt. If you do this, you'll need to run vagrant up again before you can log into it.

Now that you have Vagrant up and running type vagrant ssh to log into your VM. Change directory to the /vagrant directory by typing `cd /vagrant`. This will take you to the shared folder between your virtual machine and host machine then type  `cd catalog`.

Type `ls` to ensure that you are inside the directory that contains application.py, database_setup.py, and two directories named 'templates' and 'static'

Now Type `python application.py` to run the Flask web server. In your browser visit `http://localhost:8000` to view the item catalog app. You should be able to view, add, edit, and delete menu items that you created before










