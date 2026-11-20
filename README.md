# 🏢 Portal Empresa

Sistema web interno (intranet leve) desenvolvido para monitorar, comunicar e orientar funcionários em ambiente corporativo, inspirado no modelo de "portal do aluno" utilizado por instituições de ensino.

---

## 👥 Perfis de Acesso

O sistema conta com dois níveis de permissão:

* **Admin / RH:** Cria e gerencia usuários (ativar/desativar), publica avisos internos e organiza o calendário de eventos da empresa.
* **Funcionário:** Realiza login, visualiza avisos publicados, consulta o calendário corporativo e acessa os dados do próprio perfil.

---

## 🚀 Tecnologias Utilizadas

* **Backend:** Python com [Flask](https://flask.palletsprojects.com/) (microframework web)
* **Banco de Dados:** SQLite (`database.db`, gerado automaticamente na primeira execução)
* **Segurança & Autenticação:** Werkzeug (`generate_password_hash` / `check_password_hash`) e cookies de sessão do Flask (`secret_key`)
* **Frontend:** HTML5, CSS3 e templates Jinja2

---

## 📁 Estrutura do Projeto

```text
Projeto - Empresa/
├── app.py                        # Aplicação principal (rotas, banco e regras de negócio)
├── requirements.txt              # Dependências do projeto (Flask, Werkzeug)
├── database.db                   # Banco de dados SQLite (gerado automaticamente)
├── static/
│   └── style.css                 # Estilização visual do portal
└── templates/
    ├── base.html                 # Layout base (cabeçalho, menu e rodapé)
    ├── login.html                # Tela de autenticação
    ├── admin_avisos.html         # Listagem de avisos (Admin)
    ├── admin_novo_aviso.html     # Cadastro de avisos (Admin)
    ├── admin_calendario.html     # Listagem de eventos (Admin)
    ├── admin_novo_evento.html    # Cadastro de eventos (Admin)
    ├── admin_usuarios.html       # Gerenciamento de funcionários (Admin)
    ├── admin_novo_usuario.html   # Cadastro de novo usuário (Admin)
    ├── funcionario_avisos.html   # Mural de avisos (Funcionário)
    ├── funcionario_calendario.html # Visualização de eventos (Funcionário)
    └── funcionario_perfil.html   # Dados cadastrais do usuário logado
