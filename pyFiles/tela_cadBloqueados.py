from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivy.clock import mainthread
from kivymd.app import MDApp
from datetime import datetime
import threading
import time
import configparser

##########################################---VARIÁVEIS---##########################################
usuarios = [] # Usuários bloqueados salvos
idades = [] # Idades dos usuários bloqueados salvos

user_adm_logado = None # Váriavel que mostra o usuário do adm atualmente logado

# Variaveis que executam comandos sql
sql_postgre  = None
sql_sqlite   = None

# Variaveis que configuram o sql
sqlite_conn  = None
postgre_conn = None
###################################################################################################



# Função para salvar ou atualizar o valor de uma variável em um arquivo de configuração
###################################################################################################
def save_config_value(filename, section, variable_name, variable_value):
    config = configparser.ConfigParser()
    config.read(filename)
    if section not in config:
        config.add_section(section)
    config.set(section, variable_name, str(variable_value))
    with open(filename, 'w') as config_file:
        config.write(config_file)
###################################################################################################



# Função para ler o valor de uma variável de um arquivo de configuração
###################################################################################################
def read_config_value(filename, section, variable_name):
    config = configparser.ConfigParser()
    config.read(filename)
    if section in config and variable_name in config[section]:
        return config.get(section, variable_name)
    else:
        return None




# Item card da tela e suas funcionalidades
###################################################################################################
class CardItem(MDCard):
    dialog         = None
    barra_1        = False
    barra_2        = False
    data_mensagem  = None
    nome_mensagem  = None
    check_1        = False
    check_2        = False

    def __init__(self, text_name="", text_date="", *args, **kwargs):
        super().__init__(*args, **kwargs)
        threading.Thread(target=self.start_loop_window).start()
        if text_name != '' and text_date != '':
            # Converter de volta para texto no novo formato
            novo_data_texto = datetime.strptime(text_date, '%d/%m/%Y').strftime('%d/%m/%Y')
            # novo_data_texto = datetime.strptime(text_date, '%d/%m/%Y').strftime('%Y/%m/%d')

            self.ids.text_field1.text = text_name
            self.ids.text_field2.text = novo_data_texto
        else:
            self.ids.checkbox_salvar_blo.active = False
        
        # Threading criada para checar o texto escrito nos Textfields
        threading.Thread(target=self.start_check_text).start()
    
    # Função que inicia os loopings do app
    def start_loop_window(self):
        while MDApp.get_running_app():
            time.sleep(0.05)
            self.check_disable_textfield()

    # Looping que checa se o textfield do cadastro do bloqueado pode ou não ser utilizado
    @mainthread
    def check_disable_textfield(self):
        if self.ids.checkbox_salvar_blo.active == True:
            self.ids.text_field1.disabled = True
            self.ids.text_field2.disabled = True

    # Remove bloqueados especificos do banco de dados
    def remove(self):
        self.parent.remove_widget(self)
        try:
            sql_sqlite.execute(f"DELETE FROM bloqueados WHERE nome_blo = '{self.ids.text_field1.text}'")
            sql_sqlite.execute(f"DELETE FROM bloqueados WHERE idade_blo = '{self.ids.text_field2.text}'")
            sql_sqlite.execute(f"DELETE FROM usuarios_selecionados WHERE bloqueados_ativos = '{self.ids.text_field1.text}'")
            sqlite_conn.commit()
            print("#---BLOQUEADO REMOVIDO---#")
            print(self.ids.text_field1.text)
            print(self.ids.text_field2.text)
            print("#--------------------------#\n")
        except:
            pass
        
    # Permite editar o usuário bloqueado que já está cadastrado
    def check_remove(self):
        self.ids.checkbox_salvar_blo.active = False
        self.ids.text_field1.disabled = False
        self.ids.text_field2.disabled = False
        if sql_sqlite:
            try:
                sql_sqlite.execute(f"DELETE FROM bloqueados WHERE nome_blo = '{self.ids.text_field1.text}'")
                sql_sqlite.execute(f"DELETE FROM bloqueados WHERE idade_blo = '{self.ids.text_field2.text}'")
                sqlite_conn.commit()
            except:
                pass
    
    # Função responsavel por checar informações invalidas e adicionar bloqueados
    def add_bloqueados(self, checkbox, value):
        if value:
            self.checar_nome()
            self.ids.text_field1.disabled = True
            self.ids.text_field2.disabled = True
            if self.check_1 == True and self.check_2 == True:
                if value and len(self.ids.text_field1.text) > 0 and len(self.ids.text_field2.text) > 0:
                    if sql_sqlite != None:
                        sql_sqlite.execute(f"INSERT INTO BLOQUEADOS (nome_blo, idade_blo) VALUES ('{self.ids.text_field1.text}', '{self.ids.text_field2.text}')")
                        sqlite_conn.commit()
                        sql_sqlite.execute(f"INSERT INTO usuarios_selecionados (bloqueados_ativos) VALUES ('{self.ids.text_field1.text}')")
                        sqlite_conn.commit()
                        print("#---BLOQUEADO ADICIONADO---#")
                        print(self.ids.text_field1.text)
                        print(self.ids.text_field2.text)
                        print("#--------------------------#\n")
            else:
                self.ids.text_field1.disabled = False
                self.ids.text_field2.disabled = False

        else:
            if sql_sqlite != None:
                sql_sqlite.execute(f"DELETE FROM bloqueados WHERE nome_blo = '{self.ids.text_field1.text}'")
                sql_sqlite.execute(f"DELETE FROM bloqueados WHERE idade_blo = '{self.ids.text_field2.text}'")
                sql_sqlite.execute(f"DELETE FROM usuarios_selecionados WHERE bloqueados_ativos = '{self.ids.text_field1.text}'")
                sqlite_conn.commit()
                sql = (f"DELETE FROM usuarios_selecionados WHERE bloqueados_ativos = ?")
                sql_sqlite.execute(sql, (self.ids.text_field1.text,))
                sqlite_conn.commit()
                print("#---BLOQUEADO REMOVIDO---#")
                print(self.ids.text_field1.text)
                print(self.ids.text_field2.text)
                print("#--------------------------#\n")

    # Função que checa a formatação da data e diz se é válida
    def checar_data(self, data):
        def obter_data(data):
            try:
                data_nascimento = datetime.strptime(data, "%d/%m/%Y") #Define o formato da data
                data_limite = datetime(1900, 1, 1)  # Defina a data limite aqui
                if data_nascimento > datetime.now(): # Não pode ser maior que a data atual
                    return False, "A data de nascimento não pode ser no futuro."
                if data_nascimento < data_limite:
                    return False, "A data de nascimento é anterior a 1900 e não é válida."
                    #Calcula a idade
                idade = datetime.now().year - data_nascimento.year - ((datetime.now().month, datetime.now().day) < (data_nascimento.month, data_nascimento.day))
                return True, f"Idade: {idade} anos"
            except ValueError:
                return False, "Formato de data inválido. Use o formato DD/MM/AAAA."
        if data:
            valido, mensagem = obter_data(f"{data}")
            if valido:
                self.ids.text_field2.error = False
                self.data_mensagem = ""
                self.check_2 = True
            else:
                self.data_mensagem = "Data de nascimento inválida. " + mensagem
                self.ids.text_field2.error = True
                self.check_2 = False
                self.show_alerta(self.data_mensagem)
                self.ids.checkbox_salvar_blo.active = False
        else:
            self.data_mensagem = "Data de nascimento inválida. Formato de data inválido. Use o formato DD/MM/AAAA.\nE digite uma data válida!"

    # Função que checa a formatação do nome
    def checar_nome(self):
        def validar_nome(nome):
            if len(nome) >=10:
                return True
            else:
                return False
        if validar_nome(self.ids.text_field1.text):
            self.ids.text_field1.error = False
            self.check_1 = True
            self.checar_data(self.ids.text_field2.text)
        else:
            self.nome_mensagem = "Nome precisa ter no mínimo 10 caracteres!"
            self.ids.text_field1.error = True
            self.check_1 = False
            self.show_alerta(self.nome_mensagem)
            self.ids.checkbox_salvar_blo.active = False

    # Inicia uma thread na função "set_text()"
    def start_check_text(self):
        while MDApp.get_running_app():
            time.sleep(0.01)
            self.set_text()
    
    # Função que cria um Popup de aviso
    def show_alerta(self, mensagem):
        self.dialog = None
        if not self.dialog:
            self.dialog = MDDialog(
                text=f"{mensagem}",
                buttons=[
                    MDFlatButton(
                        text="OK",
                        theme_text_color="Custom",
                        on_release=lambda x:self.close_dialog()
                    ),
                ],
            )
        self.dialog.open()
    
    def close_dialog(self):
        try:
            self.dialog.dismiss(force=True)
            self.dialog = None
        except:
            pass
    
    # Função sendo executada em loop por um thread que formata o texto em tempo real para a formatação de data
    @mainthread
    def set_text(self):
        try:
            data_nasc = self.ids.text_field2
            self.data_text_1 = data_nasc.text
            if len(data_nasc.text) >= 2 and self.barra_1 == False:
                self.barra_1 = True
                self.ids.text_field2.text = (f"{self.data_text_1}/")
            if len(data_nasc.text) >= 5 and self.barra_2 == False:
                self.barra_2 = True
                self.ids.text_field2.text = (f"{self.data_text_1}/")
            if len(data_nasc.text) < 2 > 1:
                self.barra_1 = False
            if len(data_nasc.text) < 5 > 4:
                self.barra_2 = False
        except:
            pass
###################################################################################################
        


# CLASSE DA TELA CADASTRO DE BLOQUEADOS
###################################################################################################
class Tela_CadBloqueados(MDScreen):
    switch = False
    switch_on_enter = False
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        threading.Thread(target=self.start_check_blo).start()
    
    def on_pre_enter(self):
        # Se não houver bloqueado adicionado essa parte é responsável por checar e adicionar o card
        if sql_sqlite != None:
            if self.switch_on_enter == False:
                self.switch_on_enter = True
                sql_sqlite.execute("SELECT nome_blo FROM bloqueados")
                linhas = sql_sqlite.fetchall()
                if linhas == []:
                    self.add_user_bloq()
        # Obtem os nomes dos bloqueados salvos para adicionar na tela quando o usuário entrar
        if self.switch == False:
            try:
                if sql_sqlite != None:
                    # Obter nome
                    sql_sqlite.execute("SELECT nome_blo FROM bloqueados")
                    linhas = sql_sqlite.fetchall()
                    for linha in linhas:
                        for i in linha:
                            usuarios.append(i)
                            
                    # Obter idade
                    sql_sqlite.execute("SELECT idade_blo FROM bloqueados")
                    linhas = sql_sqlite.fetchall()
                    for linha in linhas:
                        for i in linha:
                            idades.append(i)
                    self.switch = True
            except Exception as e:
                print(e)
            if usuarios != None:
                for nome, idade in zip(usuarios, idades):
                    self.ids.content.add_widget(CardItem(nome, f'{idade}'))
    
                
    def start_check_blo(self):
        while MDApp.get_running_app():
            time.sleep(0.5)
            self.check_blo()
        
    @mainthread
    def check_blo(self):
        if sql_sqlite != None:
            sql_sqlite.execute("SELECT nome_blo FROM BLOQUEADOS")
            # Recupere o resultado usando fetchone()
            resultado = sql_sqlite.fetchone()
            # Verifique se a consulta retornou resultados
            if resultado is not None:
                # O valor id_adm está na primeira coluna do resultado
                id_blo = resultado[0]
                if id_blo == None:
                    id_blo = 0
                try:
                    pass
                    # self.ids.float_layout.remove_widget(self.ids.bloq_button_window)
                    # self.ids.float_layout.remove_widget(self.ids.background_bloq_button_window)
                except:
                    pass
            else:
                pass

    def add_user_bloq(self):
        self.ids.content.add_widget(CardItem('', ''))
###################################################################################################