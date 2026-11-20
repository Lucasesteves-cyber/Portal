import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'mude-esta-chave-em-producao'

DB = 'database.db'


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.executescript('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL,
            perfil TEXT NOT NULL CHECK(perfil IN ('admin','funcionario')),
            ativo INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS avisos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            conteudo TEXT NOT NULL,
            data_criacao TEXT NOT NULL,
            usuario_id INTEGER NOT NULL,
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
        );
        CREATE TABLE IF NOT EXISTS eventos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            descricao TEXT,
            data_evento TEXT NOT NULL,
            usuario_id INTEGER NOT NULL,
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
        );
    ''')
    # cria admin default se nao existir
    cur = db.execute("SELECT id FROM usuarios WHERE perfil='admin' LIMIT 1")
    if cur.fetchone() is None:
        db.execute(
            "INSERT INTO usuarios (nome,email,senha,perfil) VALUES (?,?,?,?)",
            ('Administrador', 'admin@empresa.com', generate_password_hash('admin123'), 'admin')
        )
    db.commit()


@app.before_request
def before_request():
    init_db()
    g.usuario = None
    if 'usuario_id' in session:
        cur = get_db().execute('SELECT * FROM usuarios WHERE id=?', (session['usuario_id'],))
        g.usuario = cur.fetchone()


def login_required(view):
    from functools import wraps
    @wraps(view)
    def wrapped(*args, **kwargs):
        if 'usuario_id' not in session:
            return redirect(url_for('login'))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    from functools import wraps
    @wraps(view)
    def wrapped(*args, **kwargs):
        if 'usuario_id' not in session:
            return redirect(url_for('login'))
        if g.usuario['perfil'] != 'admin':
            flash('Acesso restrito a administradores.')
            return redirect(url_for('dashboard'))
        return view(*args, **kwargs)
    return wrapped


@app.route('/')
def index():
    if 'usuario_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        cur = get_db().execute('SELECT * FROM usuarios WHERE email=?', (email,))
        usuario = cur.fetchone()
        if usuario and check_password_hash(usuario['senha'], senha) and usuario['ativo']:
            session['usuario_id'] = usuario['id']
            session['perfil'] = usuario['perfil']
            flash('Bem-vindo, %s!' % usuario['nome'])
            return redirect(url_for('dashboard'))
        flash('Email ou senha invalidos.')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Voce saiu do sistema.')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    if g.usuario['perfil'] == 'admin':
        return redirect(url_for('admin_avisos'))
    return redirect(url_for('funcionario_avisos'))


# ---------- Admin: usuarios ----------
@app.route('/admin/usuarios')
@login_required
@admin_required
def admin_usuarios():
    cur = get_db().execute('SELECT * FROM usuarios ORDER BY id')
    usuarios = cur.fetchall()
    return render_template('admin_usuarios.html', usuarios=usuarios)


@app.route('/admin/usuarios/novo', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_novo_usuario():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        perfil = request.form['perfil']
        try:
            get_db().execute(
                'INSERT INTO usuarios (nome,email,senha,perfil) VALUES (?,?,?,?)',
                (nome, email, generate_password_hash(senha), perfil)
            )
            get_db().commit()
            flash('Usuario criado com sucesso.')
        except sqlite3.IntegrityError:
            flash('Email ja cadastrado.')
        return redirect(url_for('admin_usuarios'))
    return render_template('admin_novo_usuario.html')


@app.route('/admin/usuarios/<int:id>/toggle')
@login_required
@admin_required
def admin_toggle_usuario(id):
    usuario = get_db().execute('SELECT * FROM usuarios WHERE id=?', (id,)).fetchone()
    if usuario and usuario['perfil'] != 'admin':
        get_db().execute('UPDATE usuarios SET ativo=? WHERE id=?', (0 if usuario['ativo'] else 1, id))
        get_db().commit()
    return redirect(url_for('admin_usuarios'))


# ---------- Admin: avisos ----------
@app.route('/admin/avisos')
@login_required
@admin_required
def admin_avisos():
    cur = get_db().execute('''
        SELECT a.*, u.nome as autor FROM avisos a
        JOIN usuarios u ON a.usuario_id = u.id
        ORDER BY a.data_criacao DESC
    ''')
    avisos = cur.fetchall()
    return render_template('admin_avisos.html', avisos=avisos)


@app.route('/admin/avisos/novo', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_novo_aviso():
    if request.method == 'POST':
        titulo = request.form['titulo']
        conteudo = request.form['conteudo']
        from datetime import datetime
        data = datetime.now().strftime('%Y-%m-%d %H:%M')
        get_db().execute(
            'INSERT INTO avisos (titulo,conteudo,data_criacao,usuario_id) VALUES (?,?,?,?)',
            (titulo, conteudo, data, g.usuario['id'])
        )
        get_db().commit()
        flash('Aviso publicado.')
        return redirect(url_for('admin_avisos'))
    return render_template('admin_novo_aviso.html')


# ---------- Admin: calendario ----------
@app.route('/admin/calendario')
@login_required
@admin_required
def admin_calendario():
    cur = get_db().execute('''
        SELECT e.*, u.nome as autor FROM eventos e
        JOIN usuarios u ON e.usuario_id = u.id
        ORDER BY e.data_evento
    ''')
    eventos = cur.fetchall()
    return render_template('admin_calendario.html', eventos=eventos)


@app.route('/admin/calendario/novo', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_novo_evento():
    if request.method == 'POST':
        titulo = request.form['titulo']
        descricao = request.form['descricao']
        data_evento = request.form['data_evento']
        get_db().execute(
            'INSERT INTO eventos (titulo,descricao,data_evento,usuario_id) VALUES (?,?,?,?)',
            (titulo, descricao, data_evento, g.usuario['id'])
        )
        get_db().commit()
        flash('Evento adicionado.')
        return redirect(url_for('admin_calendario'))
    return render_template('admin_novo_evento.html')


# ---------- Funcionario: avisos ----------
@app.route('/funcionario/avisos')
@login_required
def funcionario_avisos():
    cur = get_db().execute('''
        SELECT a.*, u.nome as autor FROM avisos a
        JOIN usuarios u ON a.usuario_id = u.id
        ORDER BY a.data_criacao DESC
    ''')
    avisos = cur.fetchall()
    return render_template('funcionario_avisos.html', avisos=avisos)


# ---------- Funcionario: calendario ----------
@app.route('/funcionario/calendario')
@login_required
def funcionario_calendario():
    cur = get_db().execute('''
        SELECT e.*, u.nome as autor FROM eventos e
        JOIN usuarios u ON e.usuario_id = u.id
        ORDER BY e.data_evento
    ''')
    eventos = cur.fetchall()
    return render_template('funcionario_calendario.html', eventos=eventos)


# ---------- Funcionario: perfil ----------
@app.route('/funcionario/perfil')
@login_required
def funcionario_perfil():
    return render_template('funcionario_perfil.html', usuario=g.usuario)


if __name__ == '__main__':
    app.run(debug=True)
