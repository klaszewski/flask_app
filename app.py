import os
from flask import Flask, flash, request, redirect, send_file
from werkzeug.utils import secure_filename
import pandas as pd
from joblib import dump,load
from sklearn.preprocessing import OrdinalEncoder

app = Flask(__name__)

model = load('model.pkl')
UPLOAD_FOLDER = ''
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'json'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        print(file)
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            print('---', file)
            flash('No selected file')
            return redirect(request.url)
        if file:# and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            df = pd.read_json(file)

            df['week_day'] = df['date'].dt.dayofweek
            df = df.drop('date', axis = 1)
            
            df['hour'] = df['time'].apply(lambda x: pd.to_datetime(x).hour + pd.to_datetime(x).minute/60)
            df = df.drop('time', axis = 1)

            site_names = ['lenta.ru', 'mail.google.com', 'slack.com', 'toptal.com', 'vk.com', 'youtube.com']

            hist = df['sites'].apply(pd.Series)
            sites = hist.apply(lambda x: x.str['site'])
            sites.fillna('', inplace=True)

            def order_sites(site):
                if site in site_names:
                    return site
                elif site == "":
                    return "none"
                else:
                    return "other"
            
            for i in sites.columns:
                df["order" + str(i)] = sites[i].apply(order_sites)

            def get_sites(s):
                list =[0] * len(site_names)
                for site in s:
                    if site['site'] in site_names:
                        idx = site_names.index(site['site'])
                        list[idx] += site['length']
                return pd.Series(list, index=site_names)

            df[site_names] = df['sites'].apply(lambda x: get_sites(x))
            df = df.drop('sites',axis = 1)
            X = df.reset_index(drop = True)
            enc = OrdinalEncoder()

            X_cat = X.select_dtypes(include = 'object').columns
            X[X_cat] = enc.fit_transform(X[X_cat])
            predict = model.predict(X)
            result = pd.DataFrame(predict)
            result.to_csv(filename, index=False)
            #safe_path = safe_join(app.config['UPLOAD_FOLDER'], result)
            return send_file(filename, 
                            mimetype = 'text/csv',
                            attachment_filename = 'result.json',
                            as_attachment = True)
    return '''
    <!doctype html>
    <center>
    <title>Upload new File</title>
    <h1>Upload new File to Catch Joe</h1>
    <form method=post enctype=multipart/form-data>
    <input type=file name=file>
    <input type=submit value=Upload>
    </form>
    </center>
    '''

if __name__ == "__main__":
    app.run(debug = True)