#!/usr/bin/env python3
# coding: utf-8
# -*- coding: utf-8 -*-
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

