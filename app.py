from flask import Flask, render_template, request, redirect, url_for, session, flash, Response, send_file
from flask_sqlalchemy import SQLAlchemy 
import mysql.connector
from werkzeug.security import check_password_hash
from functools import wraps
import csv
import io
import pandas as pd
import pdfkit


app = Flask(__name__)
app.secret_key = 'une_cle_tres_secrete' 
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:hiba1234@localhost/pack_informatique'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

path_to_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
config = pdfkit.configuration(wkhtmltopdf=path_to_wkhtmltopdf)




# Définition du décorateur de sécurité personnalisé
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        
        if 'user_id' not in session: 
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function



@app.route('/export/pdf')
@login_required
def export_pdf():
    conn = get_db_connection()
    df = pd.read_sql("SELECT * FROM machine", conn)
    conn.close()
    
    
    html_content = """
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; }
            h1 { text-align: center; color: #059669; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th { background-color: #059669; color: white; padding: 10px; border: 1px solid #ddd; }
            td { padding: 8px; border: 1px solid #ddd; text-align: center; font-size: 12px; }
            tr:nth-child(even) { background-color: #f2f2f2; }
        </style>
    </head>
    <body>
        <h1>Inventaire du Parc</h1>
        """ + df.to_html(index=False, classes='table') + """
    </body>
    </html>
    """
    
   
    pdf = pdfkit.from_string(html_content, False, configuration=config, options={'page-size': 'A4', 'orientation': 'Landscape'})
    
    return send_file(io.BytesIO(pdf), mimetype='application/pdf', download_name='inventaire.pdf', as_attachment=True)







@app.route('/export/csv')
@login_required
def export_csv():
    conn = get_db_connection()
    df = pd.read_sql("SELECT * FROM machine", conn)
    conn.close()
    
    
    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()), mimetype='text/csv', download_name='inventaire.csv', as_attachment=True)


@app.route('/export/excel')
@login_required
def export_excel():
    conn = get_db_connection()
    df = pd.read_sql("SELECT * FROM machine", conn)
    conn.close()
    df = df.fillna('None')
    
    df = df.astype(str)
    
    output = io.BytesIO()
    
   
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Inventaire')
        
        workbook  = writer.book
        worksheet = writer.sheets['Inventaire']
        
        
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#059669', 
            'font_color': 'white',
            'border': 3
        })
        
       
        cell_format = workbook.add_format({'border': 1})
        
        
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            
       
        for i, col in enumerate(df.columns):
       
           max_len = max(df[col].map(len).max(), len(col)) + 2
           worksheet.set_column(i, i, max_len)
            
    output.seek(0)
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', download_name='inventaire_parc.xlsx', as_attachment=True)


def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='hiba1234', 
        database='pack_informatique'
    )



@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    print(f"Request Method: {request.method}")
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        print(f"Form Data received - User: {username}, Pass: {password}")
        
        conn = get_db_connection()
      
        cursor = conn.cursor(dictionary=True) 
        
        
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        
        if user:
           
            if str(user['password']) == str(password):
                session['user_id'] = user['id']
                return redirect(url_for('dashboard')) 
            else:
                error = "Mot de passe incorrect."
        else:
            error = "Utilisateur inexistant."
            
    return render_template('login.html', error=error)



@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
   
    cursor.execute("SELECT type_ordinateur, COUNT(*) as count FROM machine GROUP BY type_ordinateur")
    stats_types = cursor.fetchall()
    
   
    cursor.execute("SELECT COUNT(*) as total FROM machine")
    total_result = cursor.fetchone()
    total_machines = total_result['total'] if total_result else 0
    
    cursor.close()
    conn.close()
    
    return render_template('dashboard.html', stats_types=stats_types, total_machines=total_machines)


@app.route('/ajouter', methods=['GET', 'POST'])
@login_required 
def ajouter():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
     

    cursor = conn.cursor(dictionary=True)
    # AJOUTEZ CELA POUR DÉBOGUER :
    cursor.execute("SELECT DATABASE()")
    db_name = cursor.fetchone()
    print(f"--- JE SUIS CONNECTÉ À LA BASE : {db_name} ---")
    if request.method == 'POST':
       
        departement_id = request.form.get('departement_id')
        utilisateur = request.form.get('utilisateur')
        type_ordinateur = request.form.get('type_ordinateur')
        marque_ordinateur = request.form.get('marque_ordinateur')
        type_ecran = request.form.get('type_ecran')
        marque_ecran = request.form.get('marque_ecran')
        ram = request.form.get('ram')
        cpu_processeur = request.form.get('cpu_processeur')
        adresse_ip = request.form.get('adresse_ip')
        adresse_mac = request.form.get('adresse_mac')
        systeme_exploitation = request.form.get('systeme_exploitation')

       
        query = """INSERT INTO machine 
            (departement_id, utilisateur, type_ordinateur, marque_ordinateur, 
             type_ecran, marque_ecran, ram, cpu_processeur, adresse_ip, 
             adresse_mac, systeme_exploitation) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""


        cursor.execute(query, (
              departement_id, utilisateur, type_ordinateur, marque_ordinateur, 
               request.form.get('type_ecran'), request.form.get('marque_ecran'), 
               request.form.get('ram'), request.form.get('cpu_processeur'), 
               request.form.get('adresse_ip'), request.form.get('adresse_mac'), 
               request.form.get('systeme_exploitation')
))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('liste_machines'))

   
    cursor.execute("SELECT * FROM departements")
    services = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('ajouter.html', services=services)

@app.route('/modifier/<int:id>', methods=['GET', 'POST'])
@login_required
def modifier(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM departements")
    services = cursor.fetchall()
    if request.method == 'POST':
       
        data = {
            'departement_id': request.form.get('departement_id'),
            'utilisateur': request.form.get('utilisateur'),
            'type_ordinateur': request.form.get('type_ordinateur'),
            'marque_ordinateur': request.form.get('marque_ordinateur'),
            'type_ecran': request.form.get('type_ecran'),
            'marque_ecran': request.form.get('marque_ecran'),
            'ram': request.form.get('ram'),
            'cpu_processeur': request.form.get('cpu_processeur'),
            'adresse_ip': request.form.get('adresse_ip'),
            'adresse_mac': request.form.get('adresse_mac'),
            'systeme_exploitation': request.form.get('systeme_exploitation')
        }
        
      
        query = """UPDATE machine SET 
                    departement_id=%s, utilisateur=%s, type_ordinateur=%s, marque_ordinateur=%s,
                    type_ecran=%s, marque_ecran=%s, ram=%s, cpu_processeur=%s, 
                    adresse_ip=%s, adresse_mac=%s, systeme_exploitation=%s 
                    WHERE id=%s"""
        
        
        cursor.execute(query, (
            data['departement_id'], data['utilisateur'], data['type_ordinateur'], 
            data['marque_ordinateur'], data['type_ecran'], data['marque_ecran'], 
            data['ram'], data['cpu_processeur'], data['adresse_ip'], 
            data['adresse_mac'], data['systeme_exploitation'], id
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        flash("Machine modifiée avec succès !")
        return redirect(url_for('liste_machines'))

    
    cursor.execute("SELECT * FROM machine WHERE id = %s", (id,))
    machine = cursor.fetchone()
    
    cursor.close()
    conn.close()
    return render_template('modifier.html', m=machine, services=services)
  
@app.route('/statistiques')
@login_required
def statistiques():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    
    cursor.execute("SELECT type_ordinateur, COUNT(*) as count FROM machine GROUP BY type_ordinateur")
    data = cursor.fetchall()
    
    labels = [row['type_ordinateur'] for row in data] if data else []
    values = [row['count'] for row in data] if data else []
    
    cursor.close()
    conn.close()
    return render_template('statistiques.html', labels=labels, values=values)

@app.route('/liste')
@login_required
def liste_machines():
    search = request.args.get('search', '')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    
    query = """
        SELECT m.*, d.nom_departement, d.nom_service 
        FROM machine m
        JOIN departements d ON m.departement_id = d.id
        WHERE m.est_supprime = 0
    """
    
    
    if search:
        search_term = f"%{search}%"
        query += """ 
            AND (m.utilisateur LIKE %s 
            OR d.nom_departement LIKE %s 
            OR d.nom_service LIKE %s)
        """
        cursor.execute(query, (search_term, search_term, search_term))
    else:
        cursor.execute(query)
        
    machines = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('liste.html', machines=machines, search=search)


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))







# --- Définition du modèle (DOIT ÊTRE AU-DESSUS) ---
class Machine(db.Model):
    __tablename__ = 'machine'
    id = db.Column(db.Integer, primary_key=True)
    departement_id = db.Column(db.Integer)
    utilisateur = db.Column(db.String(100))
    type_ordinateur = db.Column(db.String(100))
    # ... ajoute les autres colonnes que tu vois dans ta capture ...
    est_supprime = db.Column(db.Boolean, default=False) # C'est la colonne que tu viens d'ajouter
# --- Ta route (DOIT ÊTRE EN DESSOUS) ---

@app.route('/corbeille')
@login_required
def corbeille():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Force la sélection de la base avant la requête
    cursor.execute("USE pack_informatique") 
    
    # Exécute la requête
    cursor.execute("SELECT * FROM machine WHERE est_supprime = 1")
    machines_supprimees = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('corbeille.html', machines_supprimees=machines_supprimees)


@app.route('/supprimer/<int:id>')
@login_required
def supprimer_machine(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE machine SET est_supprime = 1 WHERE id = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('liste_machines'))
@app.route('/restaurer/<int:id>')
@login_required
def restaurer_machine(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE machine SET est_supprime = 0 WHERE id = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('corbeille'))

@app.route('/supprimer_definitif/<int:id>')
@login_required
def supprimer_definitif(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM machine WHERE id = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('corbeille'))


if __name__ == '__main__':
    app.run(debug=True)