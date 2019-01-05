import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine("postgres://mnjgpkzbmgzcun:2264b70bc5c20265dc896ed2493e7f63d0ca49db2a616c2e8d816af90256b8aa@ec2-107-22-169-45.compute-1.amazonaws.com:5432/d5msbufqcan70k")
db = scoped_session(sessionmaker(bind=engine))

def main():
    f = open("books.csv", "r")
    reader = csv.reader(f)
    next(reader)
    for isbn, title, author, year in reader:
        db.execute("INSERT INTO books(isbn, title, author, year) VALUES(:isbn, :title, :author, :year)",
         {"isbn": isbn, "title": title, "author": author, "year": year})
        print(f"added {isbn} and {title} and {author} and {year} to the books")
        db.commit()
    
if __name__ == "__main__":
    main()