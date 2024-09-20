import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import uuid


# Funções para interagir com o banco de dados
def criar_tabela_usuarios():
    conn = sqlite3.connect('usuario.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS usuarios(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def criar_tabela_despesas_receitas():
    conn = sqlite3.connect('usuario.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS despesas_receitas(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            descricao TEXT,
            valor REAL NOT NULL,
            data TEXT,
            mes INTEGER,
            ano INTEGER,
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
        )
    ''')
    conn.commit()
    conn.close()

def listar_usuarios():
    conn = sqlite3.connect('usuario.db')
    c = conn.cursor()
    c.execute("SELECT id, nome, email FROM usuarios")
    usuarios = c.fetchall()
    conn.close()
    return usuarios

def cadastrar_usuario(nome, email, senha):
    try:
        conn = sqlite3.connect('usuario.db')
        c = conn.cursor()
        c.execute('''
            INSERT INTO usuarios (nome, email, senha)
            VALUES (?, ?, ?)
        ''', (nome, email, senha))
        conn.commit()
        conn.close()
        return True, f"Usuário {nome} cadastrado com sucesso!"
    except sqlite3.IntegrityError:
        return False, "Erro: O email já está cadastrado."

def cadastrar_despesas_receitas(usuario_id, tipo, descricao, valor, mes, ano):
    try:
        conn = sqlite3.connect('usuario.db')
        c = conn.cursor()
        data_atual = datetime.now()
        data_formatada = data_atual.strftime('%Y-%m-%d')
        c.execute('''
            INSERT INTO despesas_receitas (usuario_id, tipo, descricao, valor, data, mes, ano)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (usuario_id, tipo, descricao, valor, data_formatada, mes, ano))
        conn.commit()
        conn.close()
        return True, f"{tipo.capitalize()} cadastrada com sucesso!"
    except Exception as e:
        return False, f"Erro ao cadastrar {tipo}: {e}"

def calcular_saldo(usuario_id, mes, ano):
    conn = sqlite3.connect('usuario.db')
    c = conn.cursor()

    c.execute('''
        SELECT tipo, descricao, valor FROM despesas_receitas
        WHERE usuario_id = ? AND mes = ? AND ano = ?
    ''', (usuario_id, mes, ano))
    registros = c.fetchall()
    conn.close()

    receita_total = sum([item[2] for item in registros if item[0] == 'receita']) or 0
    despesa_total = sum([item[2] for item in registros if item[0] == 'despesa']) or 0

    saldo = receita_total - despesa_total
    return saldo

def listar_registros(usuario_id, mes, ano):
    conn = sqlite3.connect('usuario.db')
    c = conn.cursor()
    c.execute('''
        SELECT tipo, descricao, valor, data FROM despesas_receitas
        WHERE usuario_id = ? AND mes = ? AND ano = ?
    ''', (usuario_id, mes, ano))
    registros = c.fetchall()
    conn.close()
    return registros

# Função para criar gráfico de receitas e despesas por mês
def criar_grafico(usuario_id, ano):
    conn = sqlite3.connect('usuario.db')
    df_despesas_receitas = pd.read_sql_query("SELECT * FROM despesas_receitas", conn)
    conn.close()
    
    if df_despesas_receitas.empty:
        st.error("Nenhum dado de despesas ou receitas encontrado.")
        return
    
    df_filtrado = df_despesas_receitas[(df_despesas_receitas['usuario_id'] == usuario_id) & (df_despesas_receitas['ano'] == ano)]
    
    if df_filtrado.empty:
        st.warning(f"Nenhuma transação encontrada para o ano {ano} e o usuário selecionado.")
        return
    
    df_agrupado = df_filtrado.groupby(['mes', 'tipo'])['valor'].sum().unstack(fill_value=0)
    
    fig, ax = plt.subplots()
    df_agrupado.plot(kind='bar', ax=ax)
    plt.title(f'Receitas e Despesas por Mês - Ano {ano}')
    plt.xlabel('Mês')
    plt.ylabel('Valor (R$)')
    plt.xticks(rotation=0)
    
    st.pyplot(fig)

# Página de gráficos
def pagina_graficos():
    st.title("Gráficos de Receitas e Despesas")
    
    usuarios = listar_usuarios()
    if not usuarios:
        st.error("Nenhum usuário cadastrado.")
        return
    
    usuario_selecionado = st.selectbox(
        "Selecione o usuário",
        [f"ID: {user[0]}, Nome: {user[1]}" for user in usuarios]
    )
    usuario_id = int(usuario_selecionado.split(", ")[0].split(": ")[1])
    
    ano = st.number_input("Selecione o ano", min_value=2000, max_value=datetime.now().year, step=1)
    
    if st.button("Gerar Gráfico"):
        criar_grafico(usuario_id, ano)

# Página principal para cadastro e saldo
def pagina_principal():
    st.title("Despesas e Receitas")
    
    with st.form("user_input_main"):
        st.header("Selecione o usuário")
        usuarios = listar_usuarios()
        
        if not usuarios:
            st.error("Nenhum usuário cadastrado. Cadastre um usuário primeiro.")
        else:
            usuario_selecionado = st.selectbox(
                "Usuário", 
                [f"ID: {user[0]}, Nome: {user[1]}" for user in usuarios]
            )
            usuario_id = int(usuario_selecionado.split(", ")[0].split(": ")[1])
    
            st.header("Adicione uma despesa ou receita")
            tipo = st.selectbox("Tipo", ["receita", "despesa"])
            descricao = st.text_input("Descrição")
            valor = st.number_input("Valor", min_value=0.0, step=0.01)
    
            st.header("Selecione o mês e ano para calcular o saldo")
            mes = st.selectbox("Mês", [i for i in range(1, 13)])
            ano = st.number_input("Ano", min_value=2000, max_value=datetime.now().year, step=1)
    
            submitted = st.form_submit_button("Cadastrar despesa/receita e calcular saldo")
    
    if submitted:
        cadastrar_despesas_receitas(usuario_id, tipo, descricao, valor, mes, ano)
        saldo = calcular_saldo(usuario_id, mes, ano)
        st.header("Resultado")
        st.write(f"O saldo do usuário no mês {mes}/{ano} é: R$ {saldo:.2f}")

# Função para exibir footer
def adicionar_footer():
    footer = """
    <style>
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #f1f1f1;
        color: #333;
        text-align: center;
        padding: 10px;
    }
    </style>
    <div class="footer">
        <p>Este aplicativo é propriedade de @Ftech - Todos os direitos reservados © 2024</p>
        <p>Contatos : <a href="fernandoalextech@gmail.com">fernandoalextech@gmail.com</a> | </p>
    </div>
    """
    st.markdown(footer, unsafe_allow_html=True)

# Criar menu de navegação
paginas = {
    "Página Principal": pagina_principal,
    "Gráficos de Receitas e Despesas": pagina_graficos,
}

# Barra lateral para navegação
st.sidebar.title("Navegação")
selecao_pagina = st.sidebar.radio("Selecione uma página", list(paginas.keys()))

# Carregar a página selecionada
paginas[selecao_pagina]()

# Adicionar o footer
adicionar_footer()
