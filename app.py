from flask import (
    Flask,
    request,
    jsonify,
    render_template,
    session,
    redirect,
    url_for,
    flash,
)
import pyodbc
from datetime import datetime

app = Flask(__name__)

app.secret_key = "secret_key"
servidor = "NotDay"
banco_de_dados = "Gerenciamento-TI"
usuario_db = ""
senha_db = ""
tabela_funcionarios = "dbo.GFfuncionarios"
tabela_usuarios = "dbo.usuarios"
tabela_historico = "dbo.GFhistorico"
tabela_impressoras = "dbo.GFimpressoras"
tabela_chamados = "dbo.GFchamados"
data_atual = datetime.now().strftime("%d/%m/%Y")
horario_atual = datetime.now().strftime("%H:%M:%S")

# ----- C O N E X Ã O ------------------------------------------------------------------------------------------------------------------------------------------------


def conectar(servidor, banco_de_dados, usuario_db, senha_db):
    try:
        conn = pyodbc.connect(
            f"DRIVER={{SQL Server}};SERVER={servidor};DATABASE={banco_de_dados};UID={usuario_db};PWD={senha_db}"
        )
        return conn
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {str(e)}")
        return None


# ----- I D ------------------------------------------------------------------------------------------------------------------------------------------------


def id(servidor, banco_de_dados, usuario_db, senha_db, tabela_historico):
    try:
        conexao = conectar(servidor, banco_de_dados, usuario_db, senha_db)
        cursor = conexao.cursor()
        consulta_sql = f"SELECT MAX(ID) FROM {tabela_historico}"
        cursor.execute(consulta_sql)
        resultado = cursor.fetchone()
        return (resultado[0]) if resultado and resultado[0] is not None else 1

    except Exception as e:
        print(f"Erro ao obter o último número de inspeção: {str(e)}")
        return None
    finally:
        cursor.close()
        conexao.close()


# ----- P L A N T A ------------------------------------------------------------------------------------------------------------------------------------------------


def planta(servidor, banco_de_dados, usuario_db, senha_db, tabela_usuarios):
    try:
        conexao = conectar(servidor, banco_de_dados, usuario_db, senha_db)
        cursor = conexao.cursor()
        consulta_sql = f"SELECT Planta FROM {tabela_usuarios}"
        cursor.execute(consulta_sql)
        resultado = cursor.fetchone()
        return (resultado[0]) if resultado and resultado[0] is not None else 1

    except Exception as e:
        print(f"Erro ao obter a planta: {str(e)}")
        return None
    finally:
        cursor.close()
        conexao.close()


# ----- R E D I R E C I O N A D O R E S ------------------------------------------------------------------------------------------------------------------------------------------------


@app.route("/")
def PagLogin():
    return render_template("login.html")


@app.route("/menu")
def menu():
    return render_template("menu.html")


@app.route("/menu_comum")
def menu_comum():
    return render_template("menu_comum.html")


@app.route("/cadastro")
def cadastro():
    return render_template("cadastro.html")


@app.route("/usuarios")
def usuarios():
    historico = historicouser()
    return render_template("usuarios.html", historico=historico)


@app.route("/colaboradores")
def rota_colaboradores():
    matricula = session.get("matricula")
    col = colaboradores()
    return render_template("colaboradores.html", col=col)


@app.route("/colaboradores_comum")
def rota_colaboradores_comum():
    matricula = session.get("matricula")
    col = colaboradores()
    return render_template("colaboradores_comum.html", col=col)


@app.route("/impressoras")
def impressoras():
    imp = impressorasBD()
    return render_template("impressoras.html", historico=imp)


@app.route("/historico")
def historico():
    hist = historico()
    return render_template("historico.html", hist=hist)


# ----- L O G I N ----------------------------------------------------------------------------------------------------------------------------------------------------------


def verificar_credenciais(matricula, senha):
    try:  # conexão com banco de dados
        conn = pyodbc.connect(
            f"DRIVER={{SQL Server}};SERVER={servidor};DATABASE={banco_de_dados};UID={usuario_db};PWD={senha_db}"
        )
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT ID, Nome, Matricula, Senha, Planta, TIPrivilegios FROM {tabela_usuarios} WHERE Matricula = ? AND Senha = ?",
            (matricula, senha),
        )
        usuario = cursor.fetchone()
        conn.close()
        return usuario if usuario else "Credenciais inválidas"
    except Exception as e:
        print(f"Erro ao verificar credenciais: {str(e)}")
        return "Erro ao verificar credenciais"


@app.route("/login", methods=["POST"])
def login():  # verifica se o usuário existe no banco de dados e retorna uma "sessão" com os dados do usuário
    if request.method == "POST":
        matricula = request.form.get("login")
        senha = request.form.get("senha")

        result = verificar_credenciais(matricula, senha)

        if isinstance(result, str):
            flash(result, "danger")
            return render_template("login.html")
        else:
            session["usuario_id"] = result[0]
            session["nome_colaborador"] = result[1]
            session["matricula"] = result[2]
            session["planta"] = result[4]
            session["privilegios"] = result[5]

            print (session["privilegios"])
            print (session["planta"])

            conn = pyodbc.connect(
                f"DRIVER={{SQL Server}};SERVER={servidor};DATABASE={banco_de_dados};UID={usuario_db};PWD={senha_db}"
            )
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT TIPrivilegios, Planta FROM {tabela_usuarios} WHERE Matricula = ?",
                (matricula,),
            )
            privilegios, planta = cursor.fetchone()
            conn.close()

            if privilegios == "admin" and planta == "ALL":
                session["menu_type"] = "menu"
            elif privilegios == "Usuário especial" and planta == "B":
                session["menu_type"] = "menu"
            elif privilegios == "Usuário comum" and planta == "B":
                session["menu_type"] = "menu"
            elif privilegios == "Usuário especial" and planta == "A":
                session["menu_type"] = "menu"
            elif privilegios == "Usuário comum" and planta == "A":
                session["menu_type"] = "menu"
            elif privilegios == "Usuário especial" and planta == "C":
                session["menu_type"] = "menu"
            elif privilegios == "Usuário comum" and planta == "C":
                session["menu_type"] = "menu"
            else:
                flash(
                    "Você não tem permissão para acessar esse sistema, caso precise de acesso, entre em contato com o seu gestor ou com a TI",
                    "Sem acesso!",
                )
                return redirect(url_for("PagLogin"))

            session["historico_type"] = (
                "historico_atualizado"
                if "Usuário especial" in privilegios[0]
                else "historico"
            )
            return redirect(
                url_for(session["menu_type"], planta=planta, privilegios=privilegios)
            )


@app.route("/logout")
def logout():  # função para encerrar a sessão
    session.pop("usuario_id", None)
    return redirect(url_for("PagLogin"))


# ----- I N S E R I R   U S U A R I O ----------------------------------------------------------------------------------------------------------------------------------------------------------


def IsrUserHis(servidor, banco_de_dados, usuario_db, senha_db, tabela_historico, dados):
    try:
        conexao = conectar(servidor, banco_de_dados, usuario_db, senha_db)
        cursor = conexao.cursor()
        inserir_user = f"INSERT INTO {tabela_historico} ({','.join(dados.keys())}) VALUES ({','.join(['?'] * len(dados.values()))})"
        cursor.execute(inserir_user, list(dados.values()))
        conexao.commit()
        return {"status": "Usuário cadastrado com sucesso!"}
    except Exception as e:
        return {"status": f"Erro ao cadastrar usuário: {str(e)}"}
    finally:
        conexao.close()


def inserir_usuario(
    servidor, banco_de_dados, usuario_db, senha_db, tabela_usuarios, dados
):
    try:
        conexao = conectar(servidor, banco_de_dados, usuario_db, senha_db)
        cursor = conexao.cursor()
        inserir_user = f"INSERT INTO {tabela_usuarios} ({','.join(dados.keys())}) VALUES ({','.join(['?'] * len(dados.values()))})"
        cursor.execute(inserir_user, list(dados.values()))
        conexao.commit()
        return {"status": "Usuário cadastrado com sucesso!"}
    except Exception as e:
        return {"status": f"Erro ao cadastrar usuário: {str(e)}"}
    finally:
        conexao.close()


@app.route("/cadastrar", methods=["POST"])
def cadastrar():
    try:
        data = request.get_json()
        nome = data.get("nome")
        matricula = data.get("matricula")
        turno = "ADM"
        password = data.get("senha")
        privilegios = data.get("privilegios")
        planta = session.get("planta", "Planta Padrão")
        nome_colaborador = session.get("nome_colaborador", "Nome Padrão")

        privilegiosUser = session.get("privilegios", "Sem acesso")

        if privilegiosUser == "admin":
            planta = data.get("planta")
        else:
            planta = session.get("planta", "Planta Padrão")

        resultado1 = inserir_usuario(
            servidor,
            banco_de_dados,
            usuario_db,
            senha_db,
            tabela_usuarios,
            dados={
                "Nome": nome,
                "Turno": turno,
                "Matricula": matricula,
                "Senha": password,
                "TIPrivilegios": privilegios,
                "Planta": planta,
            },
        )

        resultado2 = IsrUserHis(
            servidor,
            banco_de_dados,
            usuario_db,
            senha_db,
            tabela_historico,
            {
                "Nome": nome_colaborador,
                "Dia": data_atual,
                "Horario": horario_atual,
                "CampoModificado": "Cadastro de Usuário",
                "Antigo": ".",
                "Novo": f"{nome} / Matricula: {matricula}",
                "Planta": planta,
            },
        )

        if resultado2.get("status") == "Histórico registrado com sucesso!":
            return jsonify(
                {"resultado": resultado1, "resultado2": resultado2.get("status")}
            )
        else:
            return jsonify({"status": resultado2.get("status", "Erro desconhecido")})
    except Exception as e:
        return jsonify(
            {"status": f"Erro ao processar os dados do formulário: {str(e)}"}
        )


# ----- A P A G A R   U S U A R I O ----------------------------------------------------------------------------------------------------------------------------------------------------------


def DelUserHis(servidor, banco_de_dados, usuario_db, senha_db, tabela_historico, dados):
    try:
        conexao = conectar(servidor, banco_de_dados, usuario_db, senha_db)
        cursor = conexao.cursor()
        inserir_user = f"INSERT INTO {tabela_historico} ({','.join(dados.keys())}) VALUES ({','.join(['?'] * len(dados.values()))})"
        cursor.execute(inserir_user, list(dados.values()))
        conexao.commit()
        return {"status": "Usuário apagado com sucesso!"}
    except Exception as e:
        return {"status": f"Erro ao apagar usuário: {str(e)}"}
    finally:
        conexao.close()


def DelUser(servidor, banco_de_dados, usuario_db, senha_db, tabela_usuarios, matricula):
    try:
        conexao = conectar(servidor, banco_de_dados, usuario_db, senha_db)
        cursor = conexao.cursor()
        planta = session.get("planta", "Planta Padrão")
        apagar_user = f"UPDATE {tabela_usuarios} SET TIPrivilegios = 'Sem acesso' WHERE Matricula = ?"
        cursor.execute(apagar_user, (matricula))
        conexao.commit()
        return {"status": "Usuário apagado com sucesso!"}
    except Exception as e:
        print(e)
        return {"status": f"Erro ao apagar usuário: {str(e)}"}
    finally:
        conexao.close()


@app.route("/apagar", methods=["POST"])
def apagar():
    try:
        data = request.get_json()
        matricula = data.get("matricula")
        nome_colaborador = session.get("nome_colaborador", "Nome Padrão")
        planta = session.get("planta", "Planta Padrão")

        resultado = DelUser(
            servidor, banco_de_dados, usuario_db, senha_db, tabela_usuarios, matricula
        )

        resultado2 = DelUserHis(
            servidor,
            banco_de_dados,
            usuario_db,
            senha_db,
            tabela_historico,
            {
                "Nome": nome_colaborador,
                "Dia": data_atual,
                "Horario": horario_atual,
                "CampoModificado": "Apagar Usuário",
                "Antigo": matricula,
                "Novo": ".",
                "Planta": planta,
            },
        )

        if resultado2.get("status") == "Histórico registrado com sucesso!":
            return jsonify(
                {"resultado": resultado, "resultado2": resultado2.get("status")}
            )
        else:
            return jsonify({"status": resultado2.get("status", "Erro desconhecido")})
    except Exception as e:
        return jsonify(
            {"status": f"Erro ao processar os dados do formulário: {str(e)}"}
        )


# ----- E D I T A R   U S U A R I O ----------------------------------------------------------------------------------------------------------------------------------------------------------


@app.route("/buscar_user", methods=["POST"])
def buscar_user():
    try:
        data = request.get_json()
        matricula = data.get("matriculaedit")
        conexao = conectar(servidor, banco_de_dados, usuario_db, senha_db)
        cursor = conexao.cursor()
        buscar_user = f"SELECT * FROM {tabela_usuarios} WHERE Matricula = ? AND TIPrivilegios != 'admin'"
        cursor.execute(buscar_user, (matricula,))
        resultado = cursor.fetchone()
        conexao.commit()

        if resultado:
            return jsonify(
                {
                    "nome_edit": resultado[1],
                    "matricula_edit": resultado[2],
                    "senha_edit": resultado[4],
                    "privilegio": resultado[7],
                }
            )
        else:
            return jsonify({"error": "Colaborador não encontrado."}), 404

    except Exception as e:
        print(e)
        return jsonify({"error": f"Erro ao buscar colaborador: {str(e)}"}), 500


def nome_user(
    servidor, banco_de_dados, usuario_db, senha_db, tabela_historico, matricula, nome
):
    try:
        conexao = conectar(servidor, banco_de_dados, usuario_db, senha_db)
        cursor = conexao.cursor()

        id_colaborador = id(
            servidor, banco_de_dados, usuario_db, senha_db, tabela_historico
        )

        atualizar_nome = f"UPDATE {tabela_historico} SET Nome = ? WHERE ID = ?"
        cursor.execute(atualizar_nome, (nome, id_colaborador))

        conexao.commit()
        return {"status": "Nome do colaborador atualizado com sucesso."}
    except Exception as e:
        print(e)
        return {"status": f"Erro ao atualizar nome do colaborador: {str(e)}"}
    finally:
        conexao.close()


@app.route("/edit_user", methods=["POST"])
def edit_user():
    data = request.get_json()
    nome_edit = data.get("nome_edit")
    matricula_edit = data.get("matricula_edit")
    senha_edit = data.get("senha_edit")
    privilegio = data.get("privilegio")
    matriculaeditaruser = data.get("matriculaeditaruser")

    dados = {
        "Nome": nome_edit,
        "Matricula": matricula_edit,
        "Senha": senha_edit,
        "TIPrivilegios": privilegio,
    }

    dados1 = {
        "Matriculaaeditar": matriculaeditaruser,
    }

    resultado = edit_usercol(
        servidor, banco_de_dados, usuario_db, senha_db, tabela_usuarios, dados, dados1
    )

    resultado2 = nome_user(
        servidor,
        banco_de_dados,
        usuario_db,
        senha_db,
        tabela_historico,
        matricula_edit,
        session.get("nome_colaborador", "Nome Padrão"),
    )

    if resultado2.get("status") == "Histórico registrado com sucesso!":
        return jsonify({"resultado": resultado, "resultado2": resultado2.get("status")})
    else:
        return jsonify({"status": resultado2.get("status", "Erro desconhecido")})


def edit_usercol(
    servidor, banco_de_dados, usuario_db, senha_db, tabela_usuarios, dados, dados1
):
    try:
        data = request.get_json()
        matricula = data.get("matriculaeditaruser")
        matricula = matricula.strip("'")
        conexao = conectar(servidor, banco_de_dados, usuario_db, senha_db)
        cursor = conexao.cursor()

        # Obter valores antes de serem atualizados na tabela do banco
        cursor.execute(
            f"SELECT * FROM {tabela_usuarios} WHERE Matricula = ?", (matricula,)
        )
        dados_originais = cursor.fetchone()

        # Cria um dicionário pra armazenar as colunas e o campo que vai ser atualizado
        campos_atualizados = {}

        # Verificar quais campos foram atualizados
        for campo, valor_novo in dados.items():
            valor_original = getattr(dados_originais, campo, None)
            if valor_original is not None and valor_original != valor_novo:
                campos_atualizados[campo] = valor_novo

        # Consulta SQL para atualizar apenas os campos modificados
        if campos_atualizados:
            if "Matricula" in campos_atualizados:
                query_update = (
                    f"UPDATE {tabela_usuarios} SET Matricula = ? WHERE Matricula = ?"
                )
                valores_atualizados = [
                    campos_atualizados["Matricula"],
                    dados1["Matriculaaeditar"],
                ]
                print(
                    f"O campo 'Matricula' foi atualizado para: {campos_atualizados['Matricula']}"
                )
            else:
                query_update = f"UPDATE {tabela_usuarios} SET {', '.join([f'{campo} = ?' for campo in campos_atualizados.keys()])} WHERE Matricula = ?"
                valores_atualizados = list(campos_atualizados.values()) + [
                    dados1["Matriculaaeditar"]
                ]

            cursor.execute(query_update, valores_atualizados)
            conexao.commit()
            return {"status": "Usuário editado com sucesso!"}
        else:
            return {"status": "Nenhum campo foi alterado."}

    except Exception as e:
        print(e)
        return {"status": f"Erro ao editar usuário: {str(e)}"}
    finally:
        conexao.close()


# ----- A D I C I O N A R   C O L A B O R A D O R ----------------------------------------------------------------------------------------------------------------------------------------------------------


def AddColHist(servidor, banco_de_dados, usuario_db, senha_db, tabela_historico, dados):
    try:
        conexao = conectar(servidor, banco_de_dados, usuario_db, senha_db)
        cursor = conexao.cursor()
        inserir_user = f"INSERT INTO {tabela_historico} ({','.join(dados.keys())}) VALUES ({','.join(['?'] * len(dados.values()))})"
        cursor.execute(inserir_user, list(dados.values()))
        conexao.commit()
        return {"status": "Colaborador cadastrado com sucesso!"}
    except Exception as e:
        return {"status": f"Erro ao cadastrar colaborador: {str(e)}"}
    finally:
        conexao.close()


def add_col(servidor, banco_de_dados, usuario_db, senha_db, tabela_funcionarios, dados):
    try:
        conexao = conectar(servidor, banco_de_dados, usuario_db, senha_db)
        cursor = conexao.cursor()
        inserir_user = f"INSERT INTO {tabela_funcionarios} ({','.join(dados.keys())}) VALUES ({','.join(['?'] * len(dados.values()))})"
        cursor.execute(inserir_user, list(dados.values()))
        conexao.commit()
        return {"status": "Colaborador cadastrado com sucesso!"}
    except Exception as e:
        return {"status": f"Erro ao cadastrar colaborador: {str(e)}"}
    finally:
        conexao.close()


@app.route("/add_colaborador", methods=["POST"])
def add_colaborador():
    try:
        data = request.get_json()
        nome = data.get("nome")
        sobrenome = data.get("sobrenome")
        matricula = data.get("matricula")
        SetorCC = data.get("SetorCC")
        email = data.get("email")
        turno = data.get("turno")
        n_telefone = data.get("numero_telefone")
        model_cell = data.get("modelo_celular")
        cell_empresa = data.get("celular_empresarial")
        imei = data.get("imei") 
        sn_celular = data.get("sn_celular")
        nome_maq = data.get("nome_maquina")
        maquina_sn = data.get("maquina_sn")
        nome_monitor = data.get("nome_monitor")
        monitor_sn = data.get("monitor_sn")
        mac_ethernet = data.get("mac_ethernet")
        mac_wifi = data.get("mac_wifi")
        instalacao = data.get("instalacao")
        anydesk = data.get("anydesk")
        maquina_antiga = data.get("maquina_antiga")
        sn_antiga = data.get("sn_antiga")
        locados = data.get("locados")
        fabricante = data.get("fabricante")
        modelo = data.get("modelo")
        ram = data.get("ram")
        planta = data.get("planta")

        if planta is None or planta == "":
            planta = session.get("planta", "Planta Padrão")

        resultado = add_col(
            servidor,
            banco_de_dados,
            usuario_db,
            senha_db,
            tabela_funcionarios,
            {
                "Nome": nome,
                "Sobrenome": sobrenome,
                "Matricula": matricula,
                "SetorCC": SetorCC,
                "E_mail": email,
                "Turno": turno,
                "Numero_Telefone": n_telefone,
                "Modelo_Celular": model_cell,
                "Celular_Empresarial": cell_empresa,
                "Imei": imei,
                "Celular_SN": sn_celular,
                "Nome_Maquina": nome_maq,
                "Maquina_SN": maquina_sn,
                "Nome_Monitor": nome_monitor,
                "Monitor_SN": monitor_sn,
                "MAC_Ethernet": mac_ethernet,
                "MAC_WiFi": mac_wifi,
                "Instalacao": instalacao,
                "Anydesk": anydesk,
                "Maquina_Antiga": maquina_antiga,
                "SN_Antiga": sn_antiga,
                "Locados": locados,
                "Fabricante": fabricante,
                "Modelo": modelo,
                "RAM": ram,
                "Planta": planta,
            },
        )
        resultado2 = AddColHist(
            servidor,
            banco_de_dados,
            usuario_db,
            senha_db,
            tabela_historico,
            {
                "Nome": session.get("nome_colaborador", "Nome Padrão"),
                "Dia": data_atual,
                "Horario": horario_atual,
                "CampoModificado": "Cadastro de Colaborador",
                "Antigo": ".",
                "Novo": f"{nome} / {matricula}",
                "Planta": planta,
            },
        )

        if resultado2.get("status") == "Histórico registrado com sucesso!":
            return jsonify(
                {"resultado": resultado, "resultado2": resultado2.get("status")}
            )
        else:
            return jsonify({"status": resultado2.get("status", "Erro desconhecido")})
    except Exception as e:
        return jsonify(
            {"status": f"Erro ao processar os dados do formulário: {str(e)}"}
        )


# ----- R E M O V E R   C O L A B O R A D O R ----------------------------------------------------------------------------------------------------------------------------------------------------------


def DelColHis(servidor, banco_de_dados, usuario_db, senha_db, tabela_historico, dados):
    try:
        conexao = conectar(servidor, banco_de_dados, usuario_db, senha_db)
        cursor = conexao.cursor()
        inserir_user = f"INSERT INTO {tabela_historico} ({','.join(dados.keys())}) VALUES ({','.join(['?'] * len(dados.values()))})"
        cursor.execute(inserir_user, list(dados.values()))
        conexao.commit()
        return {"status": "Usuário apagado com sucesso!"}
    except Exception as e:
        return {"status": f"Erro ao apagar usuário: {str(e)}"}
    finally:
        conexao.close()


def del_col(
    servidor, banco_de_dados, usuario_db, senha_db, tabela_funcionarios, matricula
):
    try:
        conexao = conectar(servidor, banco_de_dados, usuario_db, senha_db)
        cursor = conexao.cursor()
        planta = session.get("planta", "Planta Padrão")
        apagar_user = (
            f"DELETE FROM {tabela_funcionarios} WHERE Matricula = ? AND Planta = ?"
        )
        cursor.execute(
            apagar_user,
            (
                matricula,
                planta,
            ),
        )
        conexao.commit()
        return {"status": "Colaborador apagado com sucesso!"}
    except Exception as e:
        print(e)
        return {"status": f"Erro ao apagar colaborador: {str(e)}"}
    finally:
        conexao.close()


@app.route("/del_colaborador", methods=["POST"])
def del_colaborador():
    try:
        data = request.get_json()
        matricula = data.get("matricula")
        planta = session.get("planta", "Planta Padrão")

        resultado = del_col(
            servidor,
            banco_de_dados,
            usuario_db,
            senha_db,
            tabela_funcionarios,
            matricula,
        )

        resultado2 = DelColHis(
            servidor,
            banco_de_dados,
            usuario_db,
            senha_db,
            tabela_historico,
            {
                "Nome": session.get("nome_colaborador", "Nome Padrão"),
                "Dia": data_atual,
                "Horario": horario_atual,
                "CampoModificado": "Apagar Colaborador",
                "Antigo": matricula,
                "Novo": ".",
                "Planta": planta,
            },
        )

        if resultado2.get("status") == "Histórico registrado com sucesso!":
            return jsonify(
                {"resultado": resultado, "resultado2": resultado2.get("status")}
            )
        else:
            return jsonify({"status": resultado2.get("status", "Erro desconhecido")})
    except Exception as e:
        return jsonify(
            {"status": f"Erro ao processar os dados do formulário: {str(e)}"}
        )


@app.route("/funcionario_desligado", methods=["POST"])
def funcionario_desligado():
    data = request.get_json()
    if "matriculaDaLinha" in data:
        matricula = data.get("matriculaDaLinha")
        checkbox_marcada = data.get("checkbox_marcada")  # Captura o estado da checkbox
        estado_atual = obter_estado_desligado(matricula)
        resultado = desligar_funcionario(
            matricula, checkbox_marcada
        )  # Passa o estado da checkbox
        resultado["desligados"] = estado_atual
        return jsonify(resultado)
    else:
        return jsonify({"status": "Matricula não encontrada no JSON."})


def desligar_funcionario(matricula, checkbox_marcada):
    try:
        conexao = conectar(servidor, banco_de_dados, usuario_db, senha_db)
        cursor = conexao.cursor()

        # Verifica se a checkbox está marcada
        if checkbox_marcada:
            # Se estiver marcada, define o valor da coluna como "sim"
            query = f"UPDATE {tabela_funcionarios} SET desligados = 'sim' WHERE Matricula = ?"
        else:
            # Se não estiver marcada, define o valor da coluna como "não"
            query = f"UPDATE {tabela_funcionarios} SET desligados = 'não' WHERE Matricula = ?"

        cursor.execute(query, (matricula,))
        conexao.commit()
        return {"status": "Funcionário desligado com sucesso!"}
    except Exception as e:
        return {
            "status": f"Erro ao desligar funcionário: {str(e)}",
            "exception": str(e),
        }
    finally:
        conexao.close()


@app.route("/obter_estado_desligado", methods=["POST"])
def obter_estado_desligado():
    data = request.get_json()
    if "matriculaDaLinha" in data:
        matricula = data.get("matriculaDaLinha")
        estado_atual = obter_estado_desligado(matricula)
        return jsonify({"desligados": estado_atual})
    else:
        return jsonify({"status": "Matricula não encontrada no JSON."})


def obter_estado_desligado(matricula):
    try:
        conexao = conectar(servidor, banco_de_dados, usuario_db, senha_db)
        cursor = conexao.cursor()
        query = f"SELECT desligados FROM {tabela_funcionarios} WHERE Matricula = ?"
        cursor.execute(query, (matricula,))
        estado_atual = cursor.fetchone()[0]  # Obtém o valor da coluna "desligados"
        return estado_atual
    except Exception as e:
        # Trate o erro conforme necessário
        print(f"Erro ao obter estado de desligado: {str(e)}")
        return None
    finally:
        conexao.close()


# ----- E D I T A R   C O L A B O R A D O R ----------------------------------------------------------------------------------------------------------------------------------------------------------


@app.route("/buscar_col", methods=["POST"])
def buscar_col():
    try:
        data = request.get_json()
        matricula = data.get("matriculaedit")
        nome = data.get("nomeMatriculaEdit")
        sobrenome = data.get("sobrenomeMatriculaEdit")
        conexao = conectar(servidor, banco_de_dados, usuario_db, senha_db)
        cursor = conexao.cursor()
        buscar_user = f"SELECT * FROM {tabela_funcionarios} WHERE Nome = ? AND Sobrenome = ?"
        cursor.execute(buscar_user, (nome, sobrenome,))
        resultado = cursor.fetchone()
        conexao.commit()

        if resultado:
            return jsonify(
                {
                    "nome_edit": resultado[0],
                    "sobrenome_edit": resultado[1],
                    "matricula_edit": resultado[2],
                    "setor_edit": resultado[3],
                    "email_edit": resultado[4],
                    "turno_edit": resultado[5],
                    "numero_telefone_edit": resultado[6],
                    "modelo_celular_edit": resultado[7],
                    "celular_empresarial_edit": resultado[8],
                    "nome_maquina_edit": resultado[9],
                    "maquina_sn_edit": resultado[10],
                    "nome_monitor_edit": resultado[11],
                    "monitor_sn_edit": resultado[12],
                    "mac_ethernet_edit": resultado[13],
                    "mac_wifi_edit": resultado[14],
                    "instalacao_edit": resultado[15],
                    "anydesk_edit": resultado[16],
                    "maquina_antiga_edit": resultado[17],
                    "sn_antiga_edit": resultado[18],
                    "locados_edit": resultado[19],
                    "fabricante_edit": resultado[20],
                    "modelo_edit": resultado[21],
                    "ram_edit": resultado[22],
                    "planta_edit": resultado[23],
                    "imei_edit": resultado[26],
                    "celular_sn_edit": resultado[27],
                }
            )
        else:
            return jsonify({"error": "Colaborador não encontrado."}), 404

    except Exception as e:
        print(e)
        return jsonify({"error": f"Erro ao buscar colaborador: {str(e)}"}), 500


@app.route("/buscar_colaborador", methods=["POST"])
def buscar_colaborador():
    try:
        data = request.get_json()
        matricula = data.get("delmat")
        nome = data.get("nomeuser")
        conexao = conectar(servidor, banco_de_dados, usuario_db, senha_db)
        cursor = conexao.cursor()
        buscar_user = f"SELECT Nome, Matricula FROM {tabela_funcionarios} WHERE Matricula = ? OR Nome = ?"
        cursor.execute(
            buscar_user,
            (
                matricula,
                nome,
            ),
        )
        resultado = cursor.fetchone()
        conexao.commit()

        if resultado:
            return jsonify(
                {
                    "nomeuser": resultado[0],
                    "delmat": resultado[1],
                }
            )
        else:
            return {"status": "Colaborador não encontrado."}

    except Exception as e:
        print(e)
        return {"status": f"Erro ao buscar colaborador: {str(e)}"}


def nome_colaborador(
    servidor, banco_de_dados, usuario_db, senha_db, tabela_historico, planta, nome
):
    planta = session.get("planta", "Planta Padrão")
    try:
        conexao = conectar(servidor, banco_de_dados, usuario_db, senha_db)
        cursor = conexao.cursor()

        id_colaborador = id(
            servidor, banco_de_dados, usuario_db, senha_db, tabela_historico
        )

        atualizar_nome = (
            f"UPDATE {tabela_historico} SET Nome = ?, Planta = ? WHERE ID = ?"
        )
        cursor.execute(atualizar_nome, (nome, planta, id_colaborador))

        conexao.commit()
        return {"status": "Dados do colaborador atualizado com sucesso."}
    except Exception as e:
        print(e)
        return {"status": f"Erro ao atualizar nome do colaborador: {str(e)}"}
    finally:
        conexao.close()


def editar_coluna(
    servidor, banco_de_dados, usuario_db, senha_db, tabela_funcionarios, dados, dados1
):
    try:
        conexao = conectar(servidor, banco_de_dados, usuario_db, senha_db)
        cursor = conexao.cursor()

        # Obter valores originais
        cursor.execute(
            f"SELECT * FROM {tabela_funcionarios} WHERE Matricula = ?",
            (dados["Matricula"],),
        )
        dados_originais = cursor.fetchone()

        campos_atualizados = {}

        for campo, valor_novo in dados.items():
            valor_original = getattr(dados_originais, campo, None)
            if valor_original != valor_novo:
                campos_atualizados[campo] = valor_novo

        if campos_atualizados:
            if "Matricula" in campos_atualizados:
                query_update = f"UPDATE {tabela_funcionarios} SET Matricula = ? WHERE Matricula = ?"
                valores_atualizados = [
                    campos_atualizados["Matricula"],
                    dados1["Matriculaaeditar"],
                ]
                print(
                    f"O campo 'Matricula' foi atualizado para: {campos_atualizados['Matricula']}"
                )
            else:
                query_update = f"UPDATE {tabela_funcionarios} SET {', '.join([f'{campo} = ?' for campo in campos_atualizados])} WHERE Matricula = ?"
                valores_atualizados = list(campos_atualizados.values()) + [
                    dados1["Matriculaaeditar"]
                ]

            cursor.execute(query_update, valores_atualizados)
            conexao.commit()
            return jsonify({"status": "Colaborador editado com sucesso!"})
        else:
            return jsonify({"status": "Nenhum campo foi alterado."})

    except Exception as e:
        return jsonify({"status": f"Erro ao editar colaborador: {e}"})

    finally:
        conexao.close()


@app.route("/edit_colaborador", methods=["POST"])
def edit_colaborador():
    data = request.get_json()
    try:
        dados = {
            "Nome": data.get("nome_edit"),
            "Sobrenome": data.get("sobrenome_edit"),
            "Matricula": data.get("matricula_edit"),
            "SetorCC": data.get("setor_edit"),
            "E_mail": data.get("email_edit"),
            "Turno": data.get("turno_edit"),
            "Numero_Telefone": data.get("numero_telefone_edit"),
            "Modelo_Celular": data.get("modelo_celular_edit"),
            "Celular_Empresarial": data.get("celular_empresarial_edit"),
            "Imei": data.get("imei_edit"),
            "Celular_SN": data.get("celular_sn_edit"),
            "Nome_Maquina": data.get("nome_maquina_edit"),
            "Maquina_SN": data.get("maquina_sn_edit"),
            "Nome_Monitor": data.get("nome_monitor_edit"),
            "Monitor_SN": data.get("monitor_sn_edit"),
            "MAC_Ethernet": data.get("mac_ethernet_edit"),
            "MAC_WiFi": data.get("mac_wifi_edit"),
            "Instalacao": data.get("instalacao_edit"),
            "Anydesk": data.get("anydesk_edit"),
            "Maquina_Antiga": data.get("maquina_antiga_edit"),
            "SN_Antiga": data.get("sn_antiga_edit"),
            "Locados": data.get("locados_edit"),
            "Fabricante": data.get("fabricante_edit"),
            "Modelo": data.get("modelo_edit"),
            "RAM": data.get("ram_edit"),
            "Planta": data.get("planta_edit"),
        }

        dados1 = {
            "Matriculaaeditar": data.get("matriculaaeditar"),
        }

        resultado = editar_coluna(
            servidor,
            banco_de_dados,
            usuario_db,
            senha_db,
            tabela_funcionarios,
            dados,
            dados1,
        )

        resultado2 = nome_colaborador(
            servidor,
            banco_de_dados,
            usuario_db,
            senha_db,
            tabela_historico,
            data.get("matricula_edit"),
            session.get("nome_colaborador", "Nome Padrão"),
        )

        if resultado2.get("status") == "Histórico registrado com sucesso!":
            return jsonify(
                {"resultado": resultado, "resultado2": resultado2.get("status")}
            )
        else:
            return jsonify({"status": resultado2.get("status", "Erro desconhecido")})
    except Exception as e:
        print(f"Erro no bloco except: {str(e)}")
        return jsonify(
            {"status": f"Erro ao processar os dados do formulário: {str(e)}"}
        )


# ----- C O L A B O R A D O R E S ----------------------------------------------------------------------------------------------------------------------------------------------------------


def colaboradores():
    planta = session.get("planta", "Planta Padrão")
    if planta == "ALL":
        try:
            conexao = conectar(servidor, banco_de_dados, usuario_db, senha_db)
            cursor = conexao.cursor()
            buscar_user = f"SELECT * FROM {tabela_funcionarios} ORDER BY Nome"
            cursor.execute(buscar_user)
            col = []
            columns = [
                column[0] for column in cursor.description
            ]  # extrai os nomes das colunas
            for row in cursor.fetchall():
                col.append(dict(zip(columns, row)))
            conexao.commit()
            return col
        except Exception as e:
            print(e)
            return {"status": f"Erro ao buscar colaboradores: {str(e)}"}
    else:
        try:
            conexao = conectar(servidor, banco_de_dados, usuario_db, senha_db)
            cursor = conexao.cursor()
            buscar_user = (
                f"SELECT * FROM {tabela_funcionarios} WHERE Planta = ? ORDER BY Nome"
            )
            cursor.execute(buscar_user, (planta,))
            col = []
            columns = [
                column[0] for column in cursor.description
            ]  # extrai os nomes das colunas
            for row in cursor.fetchall():
                col.append(dict(zip(columns, row)))
            conexao.commit()
            return col
        except Exception as e:
            print(e)
            return {"status": f"Erro ao buscar colaboradores: {str(e)}"}


# ----- H I S T O R I C O ----------------------------------------------------------------------------------------------------------------------------------------------------------


def historico(planta=None):
    planta = planta or session.get("planta", "Planta Padrão")
    if planta != "ALL":
        try:
            conexao = conectar(servidor, banco_de_dados, usuario_db, senha_db)
            cursor = conexao.cursor()
            buscar = f"SELECT * FROM {tabela_historico} WHERE Planta = ? ORDER BY ID"
            cursor.execute(buscar, (planta,))
            print(planta)
            col = []
            columns = [column[0] for column in cursor.description]

            for row in cursor.fetchall():
                col.append(dict(zip(columns, row)))

            conexao.commit()
            return col
        except Exception as e:
            print(e)
            return {"status": f"Erro ao buscar colaboradores: {str(e)}"}
    else:
        try:
            conexao = conectar(servidor, banco_de_dados, usuario_db, senha_db)
            cursor = conexao.cursor()
            buscar = f"SELECT * FROM {tabela_historico} ORDER BY ID"
            cursor.execute(buscar)
            col = []
            columns = [
                column[0] for column in cursor.description
            ]  # extrai os nomes das colunas
            for row in cursor.fetchall():
                col.append(dict(zip(columns, row)))
            conexao.commit()
            return col
        except Exception as e:
            print(e)
            return {"status": f"Erro ao buscar colaboradores: {str(e)}"}


def historicouser():
    try:
        conexao = conectar(servidor, banco_de_dados, usuario_db, senha_db)
        cursor = conexao.cursor()
        buscar = f"SELECT * FROM {tabela_usuarios} WHERE TIPrivilegios != 'Sem acesso' AND TIPrivilegios != 'admin' AND Planta = ? ORDER BY ID"
        cursor.execute(buscar, (session.get("planta", "Planta Padrão"),))
        col = []
        columns = [
            column[0] for column in cursor.description
        ]  # extrai os nomes das colunas
        for row in cursor.fetchall():
            col.append(dict(zip(columns, row)))
        conexao.commit()
        return col
    except Exception as e:
        print(e)
        return {"status": f"Erro ao buscar colaboradores: {str(e)}"}


# ----- I M P R E S S O R A S ----------------------------------------------------------------------------------------------------------------------------------------------------------


def impressorasBD():
    try:
        conexao = conectar(servidor, banco_de_dados, usuario_db, senha_db)
        cursor = conexao.cursor()
        buscar = f"SELECT * FROM {tabela_impressoras}"
        cursor.execute(buscar)
        col = []
        columns = [
            column[0] for column in cursor.description
        ]  # extrai os nomes das colunas
        for row in cursor.fetchall():
            col.append(dict(zip(columns, row)))
        conexao.commit()
        return col
    except Exception as e:
        print(e)
        return {"status": f"Erro ao buscar colaboradores: {str(e)}"}


# ----- A D I C I O N A R   I M P R E S S O R A S ----------------------------------------------------------------------------------------------------------------------------------------------------------


def addImpressora(
    servidor, banco_de_dados, usuario_db, senha_db, tabela_impressoras, dados
):
    try:
        conexao = conectar(servidor, banco_de_dados, usuario_db, senha_db)
        cursor = conexao.cursor()
        inserir_user = f"INSERT INTO {tabela_impressoras} ({','.join(dados.keys())}) VALUES ({','.join(['?'] * len(dados.values()))})"
        cursor.execute(inserir_user, list(dados.values()))
        conexao.commit()
        return {"status": "Colaborador cadastrado com sucesso!"}
    except Exception as e:
        return {"status": f"Erro ao cadastrar colaborador: {str(e)}"}
    finally:
        conexao.close()


@app.route("/add_impressora", methods=["POST"])
def add_impressora():
    try:
        data = request.get_json()
        nome = data.get("nome")
        modelo = data.get("modelo")
        local = data.get("local")
        link = data.get("link")
        planta = data.get("planta")

        if planta is None or planta == "":
            planta = session.get("planta", "Planta Padrão")

        resultado = addImpressora(
            servidor,
            banco_de_dados,
            usuario_db,
            senha_db,
            tabela_impressoras,
            {
                "Nome": nome,
                "Modelo": modelo,
                "Local": local,
                "Link": link,
                "Usuario": session.get("nome_colaborador", "Nome Padrão"),
                "Planta": planta,
            },
        )

        resultado2 = AddColHist(
            servidor,
            banco_de_dados,
            usuario_db,
            senha_db,
            tabela_historico,
            {
                "Nome": session.get("nome_colaborador", "Nome Padrão"),
                "Dia": data_atual,
                "Horario": horario_atual,
                "CampoModificado": "Cadastro de Impressora",
                "Antigo": ".",
                "Novo": f"{nome} / Modelo: {modelo}",
                "Planta": planta,
            },
        )

        if resultado2.get("status") == "Histórico registrado com sucesso!":
            return jsonify(
                {"resultado": resultado, "resultado2": resultado2.get("status")}
            )
        else:
            return jsonify({"status": resultado2.get("status", "Erro desconhecido")})
    except Exception as e:
        return jsonify(
            {"status": f"Erro ao processar os dados do formulário: {str(e)}"}
        )


# ----- E D I T A R   I M P R E S S O R A S ----------------------------------------------------------------------------------------------------------------------------------------------------------


@app.route("/buscar_imp", methods=["POST"])
def buscar_imp():
    try:
        data = request.get_json()
        nomeImpr = data.get("impressoraedit")
        print(nomeImpr)
        conexao = conectar(servidor, banco_de_dados, usuario_db, senha_db)
        cursor = conexao.cursor()
        buscar_user = f"SELECT * FROM {tabela_impressoras} WHERE Nome = ?"
        cursor.execute(buscar_user, (nomeImpr,))
        resultado = cursor.fetchone()
        conexao.commit()

        if resultado:
            return jsonify(
                {
                    "nome_edit": resultado[1],
                    "modelo_edit": resultado[2],
                    "local_edit": resultado[3],
                    "link_edit": resultado[4],
                    "planta_edit": resultado[6],
                }
            )
        else:
            return jsonify({"error": "Colaborador não encontrado."}), 404

    except Exception as e:
        print(e)
        return jsonify({"error": f"Erro ao buscar colaborador: {str(e)}"}), 500


@app.route("/edit_impressora", methods=["POST"])
def edit_impressora():
    data = request.get_json()
    nomeimpressoraedit = data.get("nomeimpressoraedit")
    nome_edit = data.get("nome_edit")
    modelo_edit = data.get("modelo_edit")
    local_edit = data.get("local_edit")
    link_edit = data.get("link_edit")
    planta_edit = data.get("planta_edit")

    dados = {
        "Nome": nome_edit,
        "Modelo": modelo_edit,
        "Local": local_edit,
        "Link": link_edit,
        "Planta": planta_edit,
    }

    dados1 = {
        "nomeimpressoraedit": nomeimpressoraedit,
    }

    resultado = edit_impressora_col(
        servidor,
        banco_de_dados,
        usuario_db,
        senha_db,
        tabela_impressoras,
        dados,
        dados1,
    )

    resultado2 = nome_impressora_historico(
        servidor,
        banco_de_dados,
        usuario_db,
        senha_db,
        tabela_impressoras,
        nomeimpressoraedit,
        session.get("nome_colaborador", "Nome Padrão"),
    )

    if resultado2.get("status") == "Histórico registrado com sucesso!":
        return jsonify({"resultado": resultado, "resultado2": resultado2.get("status")})
    else:
        return jsonify({"status": resultado2.get("status", "Erro desconhecido")})


def nome_impressora_historico(
    servidor, banco_de_dados, usuario_db, senha_db, tabela_impressoras, matricula, nome
):
    try:
        conexao = conectar(servidor, banco_de_dados, usuario_db, senha_db)
        cursor = conexao.cursor()

        id_colaborador = id(
            servidor, banco_de_dados, usuario_db, senha_db, tabela_impressoras
        )

        atualizar_nome = f"UPDATE {tabela_impressoras} SET Nome = ? WHERE ID = ?"
        cursor.execute(atualizar_nome, (nome, id_colaborador))

        conexao.commit()
        return {"status": "Nome do colaborador atualizado com sucesso."}
    except Exception as e:
        print(e)
        return {"status": f"Erro ao atualizar nome do colaborador: {str(e)}"}
    finally:
        conexao.close()


def edit_impressora_col(
    servidor, banco_de_dados, usuario_db, senha_db, tabela_impressoras, dados, dados1
):
    try:
        nomeimpressora = dados1.get("nomeimpressoraedit")
        conexao = conectar(servidor, banco_de_dados, usuario_db, senha_db)
        cursor = conexao.cursor()

        # Obter valores antes de serem atualizados na tabela do banco
        cursor.execute(
            f"SELECT * FROM {tabela_impressoras} WHERE Nome = ?", (nomeimpressora,)
        )
        dados_originais = cursor.fetchone()

        # Cria um dicionário pra armazenar as colunas e o campo que vai ser atualizado
        campos_atualizados = {}

        # Verificar quais campos foram atualizados
        for campo, valor_novo in dados.items():
            valor_original = getattr(dados_originais, campo, None)
            if valor_original is not None and valor_original != valor_novo:
                campos_atualizados[campo] = valor_novo

        # Consulta SQL para atualizar apenas os campos modificados
        if campos_atualizados:
            query_update = f"UPDATE {tabela_impressoras} SET {', '.join([f'{campo} = ?' for campo in campos_atualizados.keys()])} WHERE Nome = ?"
            valores_atualizados = list(campos_atualizados.values()) + [nomeimpressora]

            cursor.execute(query_update, valores_atualizados)
            conexao.commit()
            return {"status": "Usuário editado com sucesso!"}
        else:
            return {"status": "Nenhum campo foi alterado."}

    except Exception as e:
        print(e)
        return {"status": f"Erro ao editar usuário: {str(e)}"}
    finally:
        conexao.close()


# ----- R E M O V E R   I M P R E S S O R A S ----------------------------------------------------------------------------------------------------------------------------------------------------------


def del_impressora_col(
    servidor,
    banco_de_dados,
    usuario_db,
    senha_db,
    tabela_impressoras,
    nomeimpressora,
    planta,
):
    try:
        conexao = conectar(servidor, banco_de_dados, usuario_db, senha_db)
        cursor = conexao.cursor()
        apagar_user = f"DELETE FROM {tabela_impressoras} WHERE Nome = ? AND Planta = ?"
        cursor.execute(apagar_user, (nomeimpressora, planta))
        conexao.commit()
        return {"status": "Impressora apagada com sucesso!"}
    except Exception as e:
        print(e)
        return {"status": f"Erro ao apagar impressora: {str(e)}"}
    finally:
        conexao.close()


@app.route("/del_impressora", methods=["POST"])
def del_impressora():
    try:
        data = request.get_json()
        nomeimpressora = data.get("nomeimpressora")
        planta = session.get("planta", "Planta Padrão")

        resultado = del_impressora_col(
            servidor,
            banco_de_dados,
            usuario_db,
            senha_db,
            tabela_impressoras,
            nomeimpressora,
            planta,
        )

        resultado2 = DelColHis(
            servidor,
            banco_de_dados,
            usuario_db,
            senha_db,
            tabela_historico,
            {
                "Nome": session.get("nome_colaborador", "Nome Padrão"),
                "Dia": data_atual,
                "Horario": horario_atual,
                "CampoModificado": "Apagar Impressora",
                "Antigo": nomeimpressora,
                "Novo": ".",
                "Planta": planta,
            },
        )

        if resultado2.get("status") == "Histórico registrado com sucesso!":
            return jsonify(
                {"resultado": resultado, "resultado2": resultado2.get("status")}
            )
        else:
            return jsonify({"status": resultado2.get("status", "Erro desconhecido")})
    except Exception as e:
        return jsonify(
            {"status": f"Erro ao processar os dados do formulário: {str(e)}"}
        )


# ----- C H A M A D O S ----------------------------------------------------------------------------------------------------------------------------------------------------------


def chamadoss(servidor, banco_de_dados, usuario_db, senha_db, tabela_chamados, dados):
    try:
        conexao = conectar(servidor, banco_de_dados, usuario_db, senha_db)
        cursor = conexao.cursor()
        inserir_user = f"INSERT INTO {tabela_chamados} ({','.join(dados.keys())}) VALUES ({','.join(['?'] * len(dados.values()))})"
        cursor.execute(inserir_user, list(dados.values()))
        conexao.commit()
        return {"status": "Colaborador cadastrado com sucesso!"}
    except Exception as e:
        return {"status": f"Erro ao cadastrar colaborador: {str(e)}"}
    finally:
        conexao.close()


@app.route("/add_chamado", methods=["POST"])
def add_chamado():
    try:
        data = request.get_json()
        n_chamado = data.get("n_chamado")
        SNEqp = data.get("SNEqp")
        dia = data.get("dia")
        tecnico = data.get("tecnico")
        observacoes = data.get("OBS")
        planta = data.get("planta")

        if planta is None or planta == "":
            planta = session.get("planta", "Planta Padrão")

        dados = {
            "N_Chamado": n_chamado,
            "SN_Equipamento": SNEqp,
            "Data": dia,
            "Tecnico": tecnico,
            "OBS": observacoes,
            "Planta": planta,
        }

        resultado = chamadoss(
            servidor,
            banco_de_dados,
            usuario_db,
            senha_db,
            tabela_chamados,
            dados,
        )

        resultado2 = AddColHist(
            servidor,
            banco_de_dados,
            usuario_db,
            senha_db,
            tabela_historico,
            {
                "Nome": session.get("nome_colaborador", "Nome Padrão"),
                "Dia": data_atual,
                "Horario": horario_atual,
                "CampoModificado": "Cadastro de Chamado",
                "Antigo": ".",
                "Novo": f"{n_chamado} / Equipamento: {SNEqp}",
                "Planta": planta,
            },
        )

        if resultado2.get("status") == "Histórico registrado com sucesso!":
            return jsonify(
                {"resultado": resultado, "resultado2": resultado2.get("status")}
            )
        else:
            print("Deu merda")
            return jsonify({"status": resultado2.get("status", "Erro desconhecido")})

    except Exception as e:
        return jsonify(
            {"status": f"Erro ao processar os dados do formulário: {str(e)}"}
        )


# =-0-0-0-0-0-0-0-0-0-0-0-0-0--0


@app.route("/buscar_chamado", methods=["POST"])
def buscar_chamado():
    try:
        planta = session.get("planta", "Planta Padrão")
        data = request.get_json()
        NumeroChamadoEdit = data.get("NumeroChamadoEdit")
        conexao = conectar(servidor, banco_de_dados, usuario_db, senha_db)
        cursor = conexao.cursor()
        if planta == "ALL":
            buscar_chamado = f"SELECT * FROM {tabela_chamados} WHERE N_Chamado = ?"
            cursor.execute(buscar_chamado, (NumeroChamadoEdit,))
        else:
            buscar_chamado = (
                f"SELECT * FROM {tabela_chamados} WHERE Planta = ? AND N_Chamado = ?"
            )
            cursor.execute(
                buscar_chamado,
                (
                    planta,
                    NumeroChamadoEdit,
                ),
            )

        resultado = cursor.fetchone()
        conexao.commit()

        if resultado:
            return jsonify(
                {
                    "snEquipamentoEdit": resultado[2],
                    "dataEdit": resultado[3],
                    "tecnicoEdit": resultado[4],
                    "OBSEdit": resultado[5],
                    "planta_edit": resultado[6],
                }
            )
        else:
            return jsonify({"error": "Colaborador não encontrado."}), 404

    except Exception as e:
        print(e)
        return jsonify({"error": f"Erro ao buscar colaborador: {str(e)}"}), 500


# =-0-0-0-0-0-0-0-0-0-0-0-0-0--0


@app.route("/chamados", methods=["GET"])
def chamados():
    try:
        planta = session.get("planta", "Planta Padrão")
        if planta == "ALL":
            conexao = conectar(servidor, banco_de_dados, usuario_db, senha_db)
            cursor = conexao.cursor()
            buscar_user = f"SELECT * FROM {tabela_chamados}"
            cursor.execute(buscar_user)
            col = []
            columns = [
                column[0] for column in cursor.description
            ]  # extrai os nomes das colunas
            for row in cursor.fetchall():
                col.append(dict(zip(columns, row)))
            conexao.commit()
            return col
        else:
            conexao = conectar(servidor, banco_de_dados, usuario_db, senha_db)
            cursor = conexao.cursor()
            buscar_user = f"SELECT * FROM {tabela_chamados} WHERE Planta = ?"
            cursor.execute(buscar_user, (planta,))
            col = []
            columns = [
                column[0] for column in cursor.description
            ]  # extrai os nomes das colunas
            for row in cursor.fetchall():
                col.append(dict(zip(columns, row)))
            conexao.commit()
            return col
    except Exception as e:
        print(e)
        return {"status": f"Erro ao buscar colaboradores: {str(e)}"}


# =-0-0-0-0-0-0-0-0-0-0-0-0-0--0


@app.route("/edit_chamado", methods=["POST"])
def edit_chamado():
    data = request.get_json()
    NumeroChamadoEdit = data.get("NumeroChamadoEdit")
    snEquipamentoEdit = data.get("snEquipamentoEdit")
    dataEdit = data.get("dataEdit")
    tecnicoEdit = data.get("tecnicoEdit")
    OBSEdit = data.get("OBSEdit")
    planta_edit = data.get("planta_edit")
    nome_colab_historico = session.get("nome_colaborador", "Nome Padrão")

    dados = {
        "SN_Equipamento": snEquipamentoEdit,
        "Data": dataEdit,
        "Tecnico": tecnicoEdit,
        "OBS": OBSEdit,
        "Planta": planta_edit,
    }

    dados1 = {
        "NumeroChamadoEdit": NumeroChamadoEdit,
    }

    resultado = edit_chamado_col(
        servidor,
        banco_de_dados,
        usuario_db,
        senha_db,
        tabela_chamados,
        dados,
        dados1,
    )

    resultado2 = n_chamado_historico(
        servidor,
        banco_de_dados,
        usuario_db,
        senha_db,
        tabela_historico,
        {
            "Nome": nome_colab_historico,
            "Dia": data_atual,
            "Horario": horario_atual,
            "CampoModificado": "Edição de Chamado",
            "Antigo": ".",
            "Novo": f"{snEquipamentoEdit} / Data: {dataEdit} / Tecnico: {tecnicoEdit} / OBS: {OBSEdit}",
            "Planta": planta_edit,
        },
    )

    if resultado2.get("status") == "Histórico registrado com sucesso!":
        return jsonify({"resultado": resultado, "resultado2": resultado2.get("status")})
    else:
        return jsonify({"status": resultado2.get("status", "Erro desconhecido")})


def n_chamado_historico(
    servidor, banco_de_dados, usuario_db, senha_db, tabela_historico, dados
):
    try:
        conexao = conectar(servidor, banco_de_dados, usuario_db, senha_db)
        cursor = conexao.cursor()

        inserir_historico = f"INSERT INTO {tabela_historico} ({','.join(dados.keys())}) VALUES ({','.join(['?'] * len(dados.values()))})"
        cursor.execute(inserir_historico, list(dados.values()))

        conexao.commit()
        return {"status": "Histórico registrado com sucesso."}
    except Exception as e:
        print(e)
        return {"status": f"Erro ao registrar histórico: {str(e)}"}
    finally:
        conexao.close()


def edit_chamado_col(
    servidor, banco_de_dados, usuario_db, senha_db, tabela_chamados, dados, dados1
):
    try:
        NumeroChamadoEdit = dados1.get("NumeroChamadoEdit")
        conexao = conectar(servidor, banco_de_dados, usuario_db, senha_db)
        cursor = conexao.cursor()

        # Obter valores antes de serem atualizados na tabela do banco
        cursor.execute(
            f"SELECT * FROM {tabela_chamados} WHERE N_Chamado = ?", (NumeroChamadoEdit,)
        )
        dados_originais = cursor.fetchone()

        # Cria um dicionário pra armazenar as colunas e o campo que vai ser atualizado
        campos_atualizados = {}

        # Verificar quais campos foram atualizados
        for campo, valor_novo in dados.items():
            valor_original = getattr(dados_originais, campo, None)
            if valor_original is not None and valor_original != valor_novo:
                campos_atualizados[campo] = valor_novo

        # Consulta SQL para atualizar apenas os campos modificados
        if campos_atualizados:
            query_update = f"UPDATE {tabela_chamados} SET {', '.join([f'{campo} = ?' for campo in campos_atualizados.keys()])} WHERE N_Chamado = ?"
            valores_atualizados = list(campos_atualizados.values()) + [
                NumeroChamadoEdit
            ]

            cursor.execute(query_update, valores_atualizados)
            conexao.commit()
            return {"status": "Usuário editado com sucesso!"}
        else:
            return {"status": "Nenhum campo foi alterado."}

    except Exception as e:
        print(e)
        return {"status": f"Erro ao editar usuário: {str(e)}"}
    finally:
        conexao.close()


# =-0-0-0-0-0-0-0-0-0-0-0-0-0--0


def del_chamado_col(
    servidor,
    banco_de_dados,
    usuario_db,
    senha_db,
    tabela_chamados,
    n_chamadoDel,
    planta,
):
    try:
        conexao = conectar(servidor, banco_de_dados, usuario_db, senha_db)
        cursor = conexao.cursor()
        apagar_user = (
            f"DELETE FROM {tabela_chamados} WHERE N_Chamado = ? AND Planta = ?"
        )
        cursor.execute(apagar_user, (n_chamadoDel, planta))
        conexao.commit()
        return {"status": "Impressora apagada com sucesso!"}
    except Exception as e:
        print(e)
        return {"status": f"Erro ao apagar impressora: {str(e)}"}
    finally:
        conexao.close()


@app.route("/del_chamado", methods=["POST"])
def del_chamado():
    try:
        data = request.get_json()
        n_chamadoDel = data.get("n_chamadoDel")
        planta = session.get("planta", "Planta Padrão")

        resultado = del_chamado_col(
            servidor,
            banco_de_dados,
            usuario_db,
            senha_db,
            tabela_chamados,
            n_chamadoDel,
            planta,
        )

        resultado2 = DelColHis(
            servidor,
            banco_de_dados,
            usuario_db,
            senha_db,
            tabela_historico,
            {
                "Nome": session.get("nome_colaborador", "Nome Padrão"),
                "Dia": data_atual,
                "Horario": horario_atual,
                "CampoModificado": "Apagar Chamado",
                "Antigo": n_chamadoDel,
                "Novo": ".",
                "Planta": planta,
            },
        )

        if resultado2.get("status") == "Histórico registrado com sucesso!":
            return jsonify(
                {"resultado": resultado, "resultado2": resultado2.get("status")}
            )
        else:
            return jsonify({"status": resultado2.get("status", "Erro desconhecido")})
    except Exception as e:
        return jsonify(
            {"status": f"Erro ao processar os dados do formulário: {str(e)}"}
        )


if __name__ == "__main__":
    app.run(debug=True)
