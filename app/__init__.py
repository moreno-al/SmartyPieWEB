from flask import Flask

app = Flask(__name__, template_folder="/Users/alejandramoreno/Documents/Code/capstone2022/SmartyPieWEB/app/templates")

from app import routes
