import os

myconfig = {'SECRET_KEY':os.environ.get("SECKEY"), 
          'SQLALCHEMY_DATABASE_URI':"sqlite:///test.db",
          'SQLALCHEMY_TRACK_MODIFICATIONS':True
}
