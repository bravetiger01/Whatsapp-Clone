from flask import Flask,redirect,render_template,url_for,session


app = Flask(__name__)
app.secret_key = 'mysecretkey'

if '__main__' == '__name__':
    app.run(debug=True)