from sqlalchemy import create_engine, orm
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, Float, Date, ForeignKey
import datetime
import psycopg2
import json

Base = declarative_base()

class News(Base):
    __tablename__ = 'news'

    id = Column(Integer, primary_key=True)
    category = Column(String)
    text = Column(String)
    ardnotify = orm.relationship("ArdNotify")
    
    def __repr__(self):
        return "<id={}, cat={}, text={}>".format(self.id, self.category, self.text)

class ArdNotify(Base):
    __tablename__ = 'ardnotify'

    id = Column(Integer, primary_key=True)
    server_id = Column(String, ForeignKey('guild.id', onupdate='CASCADE', ondelete='CASCADE'))
    news_id = Column(Integer, ForeignKey('news.id', onupdate='CASCADE', ondelete='CASCADE'))

class Guild(Base):
    __tablename__ = 'guild'

    id = Column(String, primary_key=True)
    name = Column(String)
    prefix = Column(String)
    is_nameread = Column(Boolean, default=False)
    ardnotify = orm.relationship("ArdNotify")
    dictionaly = orm.relationship("Dictionaly")

class User(Base):
    __tablename__ = 'user'

    id = Column(String, primary_key=True)
    name = Column(String)
    speaker = Column(String)
    speed = Column(Float, default=1)
    r_range = Column(Float, default=1.1)
    pitch = Column(Float, default=1.2)

class Dictionaly(Base):
    __tablename__ = 'dictionaly'

    id = Column(Integer, primary_key=True, autoincrement=True)
    word = Column(String)
    read = Column(String)
    server_id = Column(String, ForeignKey('guild.id', onupdate='CASCADE', ondelete='CASCADE'))

class CountRequest(Base):
    __tablename__ = 'countrequest'

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date)
    hour = Column(Integer)
    count = Column(Integer, default = 0)

url = 'postgresql+psycopg2://taro@localhost/taro_dsc'
engine = create_engine(url)

def main():
    Base.metadata.create_all(engine)

if __name__ == "__main__":
    main()

Session = orm.sessionmaker(bind=engine)
session = Session()

def add_news(cat, mess):
    news = News(category=cat, text=mess)

    session.add(news)
    session.commit()

def get_news():
    news = session.query(News)

    return news

def add_notify(news_id, guild_id):
    notified = ArdNotify(server_id=guild_id ,news_id=news_id)

    session.add(notified)
    session.commit()

def get_notify(guild_id):
    notifications = session.query(ArdNotify).filter_by(server_id=guild_id)

    return notifications

def add_guild(guild_id, name, prefix):
    guild = Guild(id=guild_id, name=name, prefix=prefix)

    session.add(guild)
    session.commit()

def set_prefix(guild_id, prefix):
    guild = session.query(Guild).filter_by(id=guild_id).one()
    guild.prefix = prefix

    session.commit()

def get_guild(guild_id):
    guilds = session.query(Guild).filter_by(id=guild_id).one_or_none()

    return guilds

def add_user(user_id, name, speaker):
    user = User(id=user_id, name=name, speaker=speaker)

    session.add(user)
    session.commit()

def set_user(user_id, speaker):
    user = session.query(User).filter_by(id=user_id).one()
    user.speaker = speaker

    session.commit()

def get_user(user_id):
    users = session.query(User).filter_by(id=user_id).one_or_none()

    return users

def add_dict(word, read, server_id):
    dictionary = session.query(Dictionaly).filter_by(word=word, server_id=server_id).one_or_none()
    if isinstance(dictionary, type(None)):
        dictionary = Dictionaly(word=word, read=read, server_id=server_id)

        session.add(dictionary)
        session.commit()
    else:
        set_dict(read, dictionary)

def set_dict(read, dictionary):
    dictionary.read = read

    session.commit()

def get_dict(server_id):
    dictionary = session.query(Dictionaly).filter_by(server_id=server_id)

    return dictionary

def del_dict(id, str_id):
    found_dict = session.query(Dictionaly).filter_by(id=id, server_id=str_id).one_or_none()
    
    if isinstance(found_dict, type(None)):
        return None
    else:
        session.delete(found_dict)

        session.commit()
        return True

def set_nameread(is_read, guild_id):
    found_guild = session.query(Guild).filter_by(id=guild_id).one_or_none()

    if isinstance(found_guild, type(None)):
        return None
    else:
        found_guild.is_nameread = is_read
        session.commit()

def set_readspeed(prm, id):
    found_user = session.query(User).filter_by(id=id).one_or_none()

    if isinstance(found_user, type(None)):
        return None
    else:
        found_user.speed = prm
        session.commit()

def set_readrange(prm, id):
    found_user = session.query(User).filter_by(id=id).one_or_none()

    if isinstance(found_user, type(None)):
        return None
    else:
        found_user.r_range = prm
        session.commit()

def set_readpitch(prm, id):
    found_user = session.query(User).filter_by(id=id).one_or_none()

    if isinstance(found_user, type(None)):
        return None
    else:
        found_user.pitch = prm
        session.commit()

def set_reqcount(date, time):
    found_rec = session.query(CountRequest).filter_by(date = date, hour = time).one_or_none()

    if isinstance(found_rec, type(None)):
        newct = CountRequest(date = date, hour = time)

        session.add(newct)
        session.commit()

        found_rec = session.query(CountRequest).filter_by(date = date, hour = time).one()
    
    found_rec.count += 1
    session.commit()