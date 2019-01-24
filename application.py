#!/usr/bin/env python3
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
