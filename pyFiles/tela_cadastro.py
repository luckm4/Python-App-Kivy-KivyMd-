from kivymd.uix.screen import MDScreen
from validate_docbr import CPF , CNPJ
from datetime import datetime
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivy.clock import mainthread
from kivymd.app import MDApp
import threading
import re
import time



postgre_conn = None
sql_postgre  = None

sql_sqlite     = None
sqlite_conn    = None

user_adm_logado = None

# Variaveis de controle
nome_adm             = None
data_nasc_adm        = None
cpf_cnpj_adm         = None
senha_adm            = None
numero_celular_adm   = None
email_adm            = None

cpf = CPF()
cnpj = CNPJ()

debbug_mode = False



# CLASSE DA TELA DE CADASTRO
class TelaCadastro(MDScreen):
    # VARIAVEIS DESTA CLASSE
    switch_mostrar_senha = False
    dialog = None
    senha_mensagem      = ""
    data_mensagem       = ""
    cpf_cnpj_mensagem   = ""
    nome_mensagem       = ""
    email_mensagem      = ""
    user_exist_mensagem = ""
    numero_mensagem     = ""
    check_1 = False
    check_2 = False
    check_3 = False
    check_4 = False
    check_5 = False
    check_6 = False
    check_7 = False
    
    # VARIAVEL DE CONTROLE PARA A DATA
    barra_1 = False
    barra_2 = False

    # VARIAVEL DE CONTROLE PARA O NUMERO DE CELULAR
    barra_3 = False
    barra_4 = False
    barra_5 = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        threading.Thread(target=self.autocomplete_info).start()
    
    # TEMPORARIO
    def on_pre_enter(self):
        global debbug_mode
        if debbug_mode:
            self.ids.nome_adm.text = 'Teste ADM 1'
            self.ids.email_adm.text = 'teste@gmail.com'
            self.ids.numero_celular_adm.text = '(34)99249-4414'
            self.ids.senha_adm.text = 'aB2@'
            self.ids.cpf_cnpj_adm.text = '152.865.936-82'
            self.ids.data_aniversario_adm.text = '01/01/2001'
    
    def mostrar_senha(self):
        self.switch_mostrar_senha = not self.switch_mostrar_senha
        if self.switch_mostrar_senha:
            self.ids.senha_adm.password = True
            self.ids.show_hide_password_id.icon = 'eye-off'
        else:
            self.ids.senha_adm.password = False
            self.ids.show_hide_password_id.icon = 'eye'
    
    # Função que mostra o textfield na tela ao clicar para digitar, não deixa o teclado tapar ele
    def visualizar_textfield_clicar_numero(self, textfield, focused):
        if focused:
            self.ids.numero_celular_adm.pos_hint = {"center_x": 0.5, "center_y": 0.46}
            self.ids.senha_adm.pos_hint = {"center_x": 0.5, "center_y": 0.54}
            self.ids.show_hide_password_id.pos_hint = {"center_x": 0.785, "center_y": 0.54}
            self.ids.cpf_cnpj_adm.pos_hint = {"center_x": 0.5, "center_y": 0.64}
            self.ids.data_aniversario_adm.pos_hint = {"center_x": 0.5, "center_y": 0.74}
            self.ids.nome_adm.pos_hint = {"center_x": 0.5, "center_y": 0.84}
            self.ids.label_cadastrar.opacity = 0
        else:
            self.ids.numero_celular_adm.pos_hint = {"center_x": 0.5, "center_y": 0.43}
            self.ids.senha_adm.pos_hint = {"center_x": 0.5, "center_y": 0.53}
            self.ids.show_hide_password_id.pos_hint = {"center_x": 0.785, "center_y": 0.54}
            self.ids.cpf_cnpj_adm.pos_hint = {"center_x": 0.5, "center_y": 0.63}
            self.ids.data_aniversario_adm.pos_hint = {"center_x": 0.5, "center_y": 0.73}
            self.ids.nome_adm.pos_hint = {"center_x": 0.5, "center_y": 0.83}
            self.ids.label_cadastrar.opacity = 1

    # Função que mostra o textfield na tela ao clicar para digitar, não deixa o teclado tapar ele
    def visualizar_textfield_clicar_email(self, textfield, focused):
        if focused:
            self.ids.email_adm.pos_hint = {"center_x": 0.5, "center_y": 0.46}
            self.ids.numero_celular_adm.pos_hint = {"center_x": 0.5, "center_y": 0.56}
            self.ids.senha_adm.pos_hint = {"center_x": 0.5, "center_y": 0.66}
            self.ids.show_hide_password_id.pos_hint = {"center_x": 0.785, "center_y": 0.66}
            self.ids.cpf_cnpj_adm.pos_hint = {"center_x": 0.5, "center_y": 0.76}
            self.ids.data_aniversario_adm.pos_hint = {"center_x": 0.5, "center_y": 0.86}
            self.ids.nome_adm.opacity = 0
            self.ids.label_cadastrar.opacity = 0
        else:
            self.ids.email_adm.pos_hint = {"center_x": 0.5, "center_y": 0.33}
            self.ids.numero_celular_adm.pos_hint = {"center_x": 0.5, "center_y": 0.43}
            self.ids.senha_adm.pos_hint = {"center_x": 0.5, "center_y": 0.53}
            self.ids.show_hide_password_id.pos_hint = {"center_x": 0.785, "center_y": 0.54}
            self.ids.cpf_cnpj_adm.pos_hint = {"center_x": 0.5, "center_y": 0.63}
            self.ids.data_aniversario_adm.pos_hint = {"center_x": 0.5, "center_y": 0.73}
            self.ids.nome_adm.opacity = 1
            self.ids.label_cadastrar.opacity = 1
    
    # Função que inicia uma thread na função: "set_text()"
    def autocomplete_info(self):
        global data_nasc_adm
        while MDApp.get_running_app():
            time.sleep(0.05)
            self.set_text()
    #FUNÇÃO QUE AJUDA A AUTOCOMPLETAR A DATA, CPF, CNPJ E NUMERO DE CELULAR
    @mainthread
    def set_text(self):
        # DATA
        if self.ids.data_aniversario_adm.text:
            data_nasc_adm = self.ids.data_aniversario_adm
            self.data_text_1 = data_nasc_adm.text
            if len(data_nasc_adm.text) == 2 and self.barra_1 == False:
                self.barra_1 = True
                self.ids.data_aniversario_adm.text = (f"{self.data_text_1}/")
            if len(data_nasc_adm.text) == 5 and self.barra_2 == False:
                self.barra_2 = True
                self.ids.data_aniversario_adm.text = (f"{self.data_text_1}/")
            if len(data_nasc_adm.text) < 2 > 1:
                self.barra_1 = False
            if len(data_nasc_adm.text) < 5 > 4:
                self.barra_2 = False
            
        # CPF
        if self.ids.cpf_cnpj_adm.text:
            self.data_text_2 = self.ids.cpf_cnpj_adm.text
            if len(self.ids.cpf_cnpj_adm.text) == 17:
                self.data_text_2 = self.data_text_2.replace(".", "").replace("-", "")
                self.ids.cpf_cnpj_adm.text = self.ids.cpf_cnpj_adm.text.replace(".", "").replace("-", "")
                self.ids.cpf_cnpj_adm.text = (f"{self.data_text_2[0:2]}.{self.data_text_2[2:5]}.{self.data_text_2[5:8]}/{self.data_text_2[8:12]}-{self.data_text_2[12:14]}")
            
            if len(self.ids.cpf_cnpj_adm.text) == 11:
                self.data_text_2 = self.data_text_2.replace(".", "").replace("/", "")
                self.ids.cpf_cnpj_adm.text = self.ids.cpf_cnpj_adm.text.replace(".", "").replace("/", "")
                self.ids.cpf_cnpj_adm.text = (f"{self.data_text_2[0:3]}.{self.data_text_2[3:6]}.{self.data_text_2[6:9]}-{self.data_text_2[9:11]}")
        
        # NUMERO DE CELULAR
        if self.ids.numero_celular_adm.text:
            self.data_text_3 = self.ids.numero_celular_adm.text
            if len(self.ids.numero_celular_adm.text) == 2 and self.barra_3 == False:
                self.barra_3 = True
                self.ids.numero_celular_adm.text = (f"({self.data_text_3})")
            if len(self.ids.numero_celular_adm.text) == 9 and self.barra_4 == False:
                self.barra_4 = True
                self.ids.numero_celular_adm.text = (f"{self.data_text_3}-")
            if len(self.ids.numero_celular_adm.text) < 2 > 1:
                self.barra_3 = False
            if len(self.ids.numero_celular_adm.text) > 2 < 3:
                self.barra_4 = False

    #========================================#

    # FUNÇÃO ADMINISTRADOR PARA ALERTAR O USUÁRIO AO PREENCHER O CADASTRO ERRADO
    def alerta(self, mensagem):
        if not self.dialog:
            self.dialog = MDDialog(
                text=f"{mensagem}",
                buttons=[
                    MDFlatButton(
                        text="OK",
                        theme_text_color="Custom",
                        on_release=lambda x:self.dialog.dismiss()
                    ),
                ],
            )
        self.dialog.open()

    # Função que é carregada ao apertar o botão cadastrar
    def cadastrar(self):
        # GLOBALIZA AS VARIAVEIS PARA QUE SEJAM ACESSADAS DENTRO DESTA FUNÇÃO
        global nome_adm, data_nasc_adm, cpf_cnpj_adm, senha_adm, numero_celular_adm, email_adm, sql_postgre, conn, sql_sqlite, sqlite_conn
        # OBTEM OS DADOS CADASTRADOS E ARMAZENA NAS VARIAVEIS GLOBAIS
        nome_adm             = self.ids.nome_adm.text
        data_nasc_adm        = self.ids.data_aniversario_adm.text
        cpf_cnpj_adm         = self.ids.cpf_cnpj_adm.text
        numero_celular_adm   = self.ids.numero_celular_adm.text
        senha_adm            = self.ids.senha_adm.text
        email_adm            = self.ids.email_adm.text

        # # Chama as funções para checar se todos os campos de cadastro estão válidos
        self.check_alerta()
    # FUNÇÃO QUE CHECA SE TODOS OS DADOS ESTÃO PREENCHIDOS, SENÃO ELA CHAMA A FUNÇÃO "alerta()" QUE EXIBE QUANDO O CADASTRO ESTÁ INCOMPLETO PARA O USUARIO
    def check_alerta(self):
        global nome_adm, data_nasc_adm, cpf_cnpj_adm, senha_adm, numero_celular_adm, email_adm, sql_sqlite, sql_postgre
        
        self.checar_nome()
        self.checar_data()
        self.checar_cpf_cnpj()
        self.checar_senha()
        self.checar_numero_cell()
        self.checar_email()
        if self.check_1 == False:
            self.dialog = None
            self.alerta(self.nome_mensagem)
        else:
            self.checar_data()
            if self.check_2 == False:
                self.dialog = None
                self.alerta(self.data_mensagem)
            else:
                self.checar_cpf_cnpj()
                if self.check_3 == False:
                    self.dialog = None
                    self.alerta(self.cpf_cnpj_mensagem)
                else:
                    self.checar_senha()
                    if self.check_4 == False:
                        self.dialog = None
                        self.alerta(self.senha_mensagem)
                    else:
                        self.checar_numero_cell()
                        if self.check_5 == False:
                            self.dialog = None
                            self.alerta(self.numero_mensagem)
                        else:
                            self.checar_email()
                            if self.check_6 == False:
                                self.dialog = None
                                self.alerta(self.email_mensagem)
                            else:
                                self.check_user()
                                if self.check_7 == False:
                                    self.dialog = None
                                    self.alerta(self.user_exist_mensagem)
                                else:
                                    # VERIFICA SE O CADASTRO ESTA CORRETO PARA INSERIR OS DADOS NO BANCO DE DADOS
                                    self.manager.current = "tela_login"
                                    data_formatada = None

                                    # INSERE OS DADOS DO CADASTRO NO BANCO DE DADOS
                                    try:
                                        data_formatada = datetime.strptime(data_nasc_adm, '%d/%m/%Y').strftime('%Y-%m-%d') 
                                        data_formatada = str(data_formatada)
                                    except Exception as e:
                                        print(e)
                                    if sqlite_conn != None:
                                        try:
                                            sql_sqlite.execute("SELECT nome_adm FROM ADMINISTRADOR")
                                            nome_adm_db = sql_sqlite.fetchall()
                                            for i in nome_adm_db:
                                                if nome_adm == nome_adm_db:
                                                    print("Nome ja existente, tente outro nome")
                                                    self.dialog = None
                                                    if not self.dialog:
                                                        self.dialog = MDDialog(
                                                            title = "Aviso!",
                                                            text = "Este nome de usuário já existe!",
                                                            buttons = [
                                                                MDFlatButton(text="Ok",
                                                                            on_release=self.dialog.dismiss())
                                                            ]
                                                        )
                                                    self.dialog.open()
                                                else:
                                                    sql_sqlite.execute(f'''INSERT INTO ADMINISTRADOR (nome_adm, cpf_cnpj_adm,
                                                                                                    data_nascimento_adm,
                                                                                                    senha_adm, numero_telefone_adm,
                                                                                                    email_adm) VALUES ('{nome_adm}','{cpf_cnpj_adm}', '{data_formatada}', '{senha_adm}', '{numero_celular_adm}', '{email_adm}')''')
                                                    sqlite_conn.commit()
                                            if nome_adm_db == [] or nome_adm_db == '':
                                                sql_sqlite.execute(f'''INSERT INTO ADMINISTRADOR (nome_adm, cpf_cnpj_adm,
                                                                                                data_nascimento_adm,
                                                                                                senha_adm, numero_telefone_adm,
                                                                                                email_adm) VALUES ('{nome_adm}','{cpf_cnpj_adm}', '{data_formatada}', '{senha_adm}', '{numero_celular_adm}', '{email_adm}')''')
                                                sqlite_conn.commit()
                                        except Exception as e:
                                            print(e)
    
    def checar_numero_cell(self):
        if len(self.ids.numero_celular_adm.text) > 14 or len(self.ids.numero_celular_adm.text) < 10:
            self.check_5 = False
            self.ids.numero_celular_adm.error = True
            self.numero_mensagem = "Número de telefone inválido!"
        else:
            self.ids.numero_celular_adm.error = False
            self.check_5 = True
            self.numero_mensagem = ""

    def check_user(self):
        global nome_adm, sqlite_conn, sql_sqlite
        if sqlite_conn != None:
            sql_sqlite.execute("SELECT nome_adm FROM administrador")
            resultado = sql_sqlite.fetchall()
            if resultado == []:
                self.user_exist_mensagem = ""
                self.ids.nome_adm.error = False
                self.check_7 = True
            else:
                for linha in resultado:
                    user_adm_db = linha[0]
                    sqlite_conn.commit()
                    if user_adm_db == nome_adm:
                        self.user_exist_mensagem = "Um usuário com o mesmo nome já está cadastrado!"
                        self.ids.nome_adm.error = True
                        self.check_7 = False
                    else:
                        self.user_exist_mensagem = ""
                        self.ids.nome_adm.error = False
                        self.check_7 = True
                                    
    # FUNÇÃO QUE CHECA SE A SENHA ESTÁ PREENCHIDA CORRETAMENTE
    def checar_senha(self):
        global senha_adm
        def validar_senha(senha):
            # Verificar se a senha tem pelo menos uma letra maiúscula e uma letra minúscula
            if not re.search(r'[A-Z]', senha) or not re.search(r'[a-z]', senha):
                return False, "A senha deve conter pelo menos uma letra maiúscula e uma letra minúscula."
            # Verificar se a senha contém pelo menos um número
            if not re.search(r'\d', senha):
                return False, "A senha deve conter pelo menos um número."
            # Verificar se a senha contém pelo menos um caractere especial
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', senha):
                return False, "A senha deve conter pelo menos um caractere especial."
            return True, "Senha válida."
        valida, mensagem = validar_senha(senha_adm)
        if valida:
            self.senha_mensagem = ""
            self.ids.senha_adm.error = False
            self.check_4 = True
        else:
            self.senha_mensagem = ("Senha inválida. " + "A senha deve conter pelo menos uma letra maiúscula, uma letra minúscula, um número e um caractere especial!")
            self.ids.senha_adm.error = True
            self.check_4 = False
    # FUNÇÃO QUE CHECA SE O NOME ESTÁ PREENCHIDO CORRETAMENTE
    def checar_nome(self):
        global nome_adm
        def validar_nome(nome):
            if len(nome) >=10:
                return True
            else:
                return False
        if validar_nome(nome_adm):
            self.ids.nome_adm.error = False
            self.nome_mensagem = "Nome valido"
            self.check_1 = True
        else:
            self.nome_mensagem = "Nome precisa ter no mínimo 10 caracteres!"
            self.ids.nome_adm.error = True
            self.check_1 = False
    # -----  FUNÇÃO QUE CHECA SE A DATA ESTÁ PREENCHIDA CORRETAMENTE  -----
    def checar_data(self):
        global data_nasc_adm
        def obter_data(data):
            try:
                data_nascimento = datetime.strptime(data, "%d/%m/%Y") #Define o formato da data
                data_limite = datetime(1900, 1, 1)  # Defina a data limite aqui
                if data_nascimento > datetime.now():       #Não pode ser maior que a data atual
                    return False, "A data de nascimento não pode ser no futuro."
                if data_nascimento < data_limite:
                    return False, "A data de nascimento é anterior a 1900 e não é válida."
                    #Calcula a idade
                idade = datetime.now().year - data_nascimento.year - ((datetime.now().month, datetime.now().day) < (data_nascimento.month, data_nascimento.day))
                return True, f"Idade: {idade} anos"
            except ValueError:
                return False, "Formato de data inválido. Use o formato DD/MM/AAAA."
        if data_nasc_adm:
            valido, mensagem = obter_data(f"{data_nasc_adm}")
            if valido:
                self.ids.data_aniversario_adm.error = False
                self.data_mensagem = ""
                self.check_2 = True
            else:
                self.data_mensagem = "Data de nascimento inválida. " + mensagem
                self.ids.data_aniversario_adm.error = True
                self.check_2 = False
        else:
            self.data_mensagem = "Data de nascimento inválida. Formato de data inválido. Use o formato DD/MM/AAAA."
            self.ids.data_aniversario_adm.error = True
            self.check_2 = False

    # FUNÇÃO QUE CHECA SE O CPF/CNPJ ESTÁ PREENCHIDO CORRETAMENTE
    def checar_cpf_cnpj(self):
        global cpf_cnpj_adm
        if cpf_cnpj_adm:
            # Condição para ver se o CPF/CNPJ é válido ou inválido
            if cpf.validate(cpf_cnpj_adm) and len(cpf_cnpj_adm) == 14:
                self.ids.cpf_cnpj_adm.error = False
                self.cpf_cnpj_mensagem = ""
                self.check_3 = True
            elif cnpj.validate(cpf_cnpj_adm) and len(cpf_cnpj_adm) == 18:
                self.cpf_cnpj_mensagem = ""
                self.ids.cpf_cnpj_adm.error = False
                self.check_3 = True
            else:
                self.ids.cpf_cnpj_adm.error = True
                self.cpf_cnpj_mensagem = "CPF/CNPJ Inválido"
                self.check_3 = False
        else:
            self.ids.cpf_cnpj_adm.error = True
            self.check_3 = False
            self.cpf_cnpj_mensagem = "CPF/CNPJ Inválido"
    # FUNÇÃO QUE CHECA SE O EMAIL ESTÁ PREENCHIDO CORRETAMENTE
    def checar_email(self):
        global email_adm
        def validar_email(email):
            # Expressão regular para validar um endereço de e-mail simples
            padrao = r'^[\w\.-]+@[\w\.-]+$'
            if re.match(padrao, email):
                return True
            else:
                return False
        if validar_email(email_adm):
            self.check_6 = True
            self.email_mensagem = ""
            self.ids.email_adm.error = False
        else:
            self.ids.email_adm.error = True
            self.check_6 = False
            self.email_mensagem = "Endereço de e-mail inválido."
