from flask import Flask,request,render_template,redirect,url_for,send_file,flash
import swiftclient
import os
import os.path
import urllib
from Crypto.Cipher import DES
import base64
from Crypto import Random
iv = Random.get_random_bytes(8)

app = Flask(__name__)
app.secret_key = 'random string'
port = int(os.getenv('VCAP_APP_PORT', 8080))
app.config['ALLOWED_EXTENSIONS'] = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']
#Creating connection to Bluemix
def file_container_connection():
    auth_url = ""
    password = ""
    project_id = ""
    user_id = ""
    region_name = ""
    container_conn=swiftclient.Connection(key=password,authurl=auth_url,auth_version='3',os_options={"project_id":project_id,"user_id":user_id,"region_name":region_name})
    return container_conn

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/upload',methods=['POST'])
def add_to_container():
    container_conn = file_container_connection()

    cont_name = "tasneem"
    container_conn.put_container(cont_name)
    file_name=request.files['file']

    if file_name.filename== '':
        flash("No Selected File")
        return render_template('index.html')
    if file_name and allowed_file(file_name.filename):
        text=file_name.read()
        length_text=len(text)
        if length_text <= 1000000 :
            encrypted_text=encryption(text)
            container_conn.put_object(cont_name, file_name.filename, contents= encrypted_text,content_type='text/plain')
            tfilename,file_size,filemoddate=display_files()
            return render_template('download.html', tfilename=tfilename, file_size=file_size,
                           filemoddate=filemoddate)
        else:
            flash("Length of file should be upto 1 MB only")
            return render_template('index.html')

@app.route('/download',methods=['POST'])
def download_file():

        container_conn = file_container_connection()
        cont_name = "tasneem"

        if request.form['download_file']:
            x = request.form.get("download_file")
            print x
            obj = container_conn.get_object(cont_name, x)
            decoded_content = decryption(obj[1])
            f = open(x, 'w')
            f.write(decoded_content)
            f.close()
            print "downloaded"
            print os.path.abspath(x)
            return send_file(os.path.abspath(x), attachment_filename=x, as_attachment=True)

@app.route('/delete',methods=['POST'])
def delete_from_container():
    container_conn = file_container_connection()
    cont_name = "tasneem"
    if request.form['delete_file_remotely']:
        xfile = request.form.get("delete_file_remotely")

        first_word, second_word = xfile.split(' ', 1)
        print second_word
        container_conn.delete_object(cont_name, second_word)
        tfilename, file_size, filemoddate = display_files()
        return render_template('download.html', tfilename=tfilename, file_size=file_size,
                               filemoddate=filemoddate)



@app.route('/search_file',methods=['POST'])
def search_file_name():
    tfilename = list()
    file_size = list()
    filemoddate = list()
    container_conn = file_container_connection()
    cont_name = "tasneem"
    name = request.form['yourname']
    for container in container_conn.get_account()[1]:
        for data in container_conn.get_container(container['name'])[1]:
            if data['name'] == name:
                tfilename.append(format(data['name']))
                file_size.append(format(data['bytes']))
                filemoddate.append(format(data['last_modified']))
        if not tfilename:
            print "Hi No Files"
            flash("No File on Cloud")
            return redirect(url_for('index'))
        else:
            return render_template('download.html', tfilename=tfilename, file_size=file_size,
                           filemoddate=filemoddate)



def display_files():
    tfilename = list()
    file_size = list()
    filemoddate = list()
    container_conn = file_container_connection()
    for container in container_conn.get_account()[1]:
        for data in container_conn.get_container(container['name'])[1]:
            tfilename.append(format(data['name']))
            file_size.append(format(data['bytes']))
            filemoddate.append(format(data['last_modified']))
            print 'object: {0}t size: {1}t date: {2}'.format(data['name'], data['bytes'], data['last_modified'])
        return tfilename,file_size,filemoddate


def encryption(privateInfo):
    des1 = DES.new('01234567', DES.MODE_CFB, iv)
    encoded=des1.encrypt(privateInfo)
    return encoded
def decryption(Encodedtext):
    des2 = DES.new('01234567', DES.MODE_CFB, iv)
    decoded_content=des2.decrypt(Encodedtext)
    return decoded_content
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)