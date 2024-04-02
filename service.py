# O service.py é responsável por executar ações em segundo plano

from kivy.utils import platform
import time
from jnius import autoclass, cast
import configparser
import sqlite3
from datetime import datetime


####################################---VÁRIAVEIS---####################################
# Variaveis que executam comandos sql
sql_postgre     = None
sql_sqlite      = None

# Variaveis que configuram o sql
sqlite_conn     = None
postgre_conn    = None


# Váriaveis que controlam ações sobre os apps
bloqueio_1 = False # Bloqueio da primeira fila de horários bloqueados "de 00:00 até 00:00"
bloqueio_2 = False # Bloqueio da segunda fila de horários bloqueados "de 00:00 até 00:00"
bloqueio_3 = False # Bloqueio da terceira fila de horários bloqueados "de 00:00 até 00:00"
bloqueio_4 = False # Bloqueio da quarta fila de horários bloqueados "de 00:00 até 00:00"
iniciado = False
tempo_inicial = 0
#######################################################################################


def connect_sql():
    global sql_sqlite, sqlite_conn
    try:
        # --- SQLITE --- #
        sqlite_conn = sqlite3.connect('administrador.db')
        sql_sqlite = sqlite_conn.cursor()
        sqlite_conn.commit()
    except:
        pass



# Função para salvar ou atualizar o valor de uma variável em um arquivo de configuração
#########################################################################################################
def save_config_value(filename, section, variable_name, variable_value):
    config = configparser.ConfigParser()
    config.read(filename)
    if section not in config:
        config.add_section(section)
    config.set(section, variable_name, str(variable_value))
    with open(filename, 'w') as config_file:
        config.write(config_file)
#########################################################################################################



# Função para ler o valor de uma variável de um arquivo de configuração
#########################################################################################################
def read_config_value(filename, section, variable_name):
    config = configparser.ConfigParser()
    config.read(filename)
    if section in config and variable_name in config[section]:
        return config.get(section, variable_name)
    else:
        return None
#########################################################################################################



# Função responsável por detectar o app aberto no momento
#########################################################################################################
def get_current_foreground_app():
    if platform == 'android':
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        PythonService = autoclass('org.kivy.android.PythonService')
        Context = autoclass('android.content.Context')
        System = autoclass('java.lang.System')
        ActivityManager = autoclass('android.app.ActivityManager')
        UsageStatsManager = autoclass('android.app.usage.UsageStatsManager')

        activity = PythonActivity.mActivity
        if activity is None:
            activity = PythonService.mService

        if activity:
            activity_manager = activity.getSystemService(Context.ACTIVITY_SERVICE)
            if activity_manager:
                usage_stats_manager = activity.getSystemService(Context.USAGE_STATS_SERVICE)
                if usage_stats_manager:
                    current_time = System.currentTimeMillis()
                    usage_stats = usage_stats_manager.queryUsageStats(UsageStatsManager.INTERVAL_DAILY, current_time - 1000 * 10, current_time)
                    
                    if usage_stats:
                        sorted_stats = sorted(usage_stats, key=lambda x: x.getLastTimeUsed(), reverse=True)
                        current_app = sorted_stats[0].getPackageName()
                        return current_app
                    else:
                        pass
                else:
                    print("Gerenciador de estatísticas de uso não disponível.")
            else:
                print("Gerenciador de atividades não disponível.")
        else:
            print("Atividade Python não disponível.")
#########################################################################################################


# Volta para a tela inicial do android mesmo em segundo plano
#########################################################################################################
def bloquear_aplicativo():
    if platform == 'android':
        # Obter o contexto atual do aplicativo
        context = autoclass('android.app.ActivityThread').currentApplication().getApplicationContext()
        # Criar um Intent para abrir a tela inicial
        Intent = autoclass('android.content.Intent')
        home_intent = Intent(Intent.ACTION_MAIN)
        home_intent.addCategory(Intent.CATEGORY_HOME)
        home_intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)  # Adicionar a flag FLAG_ACTIVITY_NEW_TASK
        # Iniciar o Intent
        context.startActivity(home_intent)
#########################################################################################################



# Obtem o status do bloqueio do app atual
#########################################################################################################
def obter_status_bloqueio(package_app):
    # Consulta SQL para selecionar o status do aplicativo com base no nome
    sql_sqlite.execute("SELECT tip_bloq_apl FROM aplic_bloc WHERE codigo_apl = ?", (package_app,))
    # Obter o resultado da consulta
    resultado = sql_sqlite.fetchone()
    # Verificar se encontrou o aplicativo e retornar o status
    if resultado:
        return resultado[0]
    else:
        return "Aplicativo não encontrado"
#########################################################################################################


# Função que obtem o nome do pacote pelo nome do app exibido
#########################################################################################################
def obter_pacote(nome_do_app):
    if platform == 'android':
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        PackageManager = autoclass('android.content.pm.PackageManager')
        Intent = autoclass('android.content.Intent')

        package_manager = PythonActivity.mActivity.getPackageManager()
        intent = Intent(Intent.ACTION_MAIN, None)
        intent.addCategory(Intent.CATEGORY_LAUNCHER)
        apps_list = package_manager.queryIntentActivities(intent, 0)

        for app in apps_list:
            if app.loadLabel(package_manager) == nome_do_app:
                return app.activityInfo.packageName
        return None
#########################################################################################################


if __name__ == "__main__":
    print("[ + ] Service foi iniciado!")
    connect_sql()
    while True:
        time.sleep(0.5)
        pacote_aberto_atualmente = get_current_foreground_app()

        # Obter a hora atual
        hora_atual_1 = datetime.now()
        # Formatar e imprimir apenas a hora e os minutos
        hora_e_minutos_atuais = hora_atual_1.strftime("%H:%M")

        # Sempre que for 00:00 será resetado o tempo de bloqueio
        if hora_e_minutos_atuais == "00:00":
            iniciado = False
            tempo_inicial = 0

        # Checa se o nome do aplicativo que o adm quer bloquear está na lista de apps para serem bloqueados
        sql_sqlite.execute("SELECT codigo_apl FROM aplic_bloc")
        linhas = sql_sqlite.fetchall()
        for linha in linhas:
            for pacote_para_bloquear in linha:
                # Checar se o app aberto atualmente é o app que o adm deseja bloquear

                if f'{pacote_aberto_atualmente}' != "cecotein.informatica.cespreitaapp.informatica":
                    # Obtém o status do app que deve ser bloqueado para saber seu tipo de bloqueio, por exemplo: "bloquear indeterminadamente, bloquear por horário etc"
                    status_bloqueio = obter_status_bloqueio(pacote_para_bloquear)


                    # Bloqueia o app por tempo indeterminado até o adm desbloquear
                    #####################################
                    if status_bloqueio == "BLOQUEADO_INDETERMINADO":
                        if f'{pacote_aberto_atualmente}' == f'{pacote_para_bloquear}':
                            bloquear_aplicativo()
                    #####################################


                    #####################################
                    if status_bloqueio == "DESBLOQUEADO":
                        pass
                    #####################################


                    #####################################
                    if status_bloqueio == "HORAS_DE_USO":
                        if read_config_value("conf/config.ini", "STATE", "hora_atual_bloc_switch") == "False":
                            if f'{pacote_aberto_atualmente}' == f'{pacote_para_bloquear}':
                                # Se o app que está bloqueado for aberto, começa a contar o tempo restante
                                if not iniciado:
                                    iniciado = True
                                    tempo_inicial = time.time()
                                if iniciado:
                                    tempo_passado = time.time() - tempo_inicial
                                else:
                                    tempo_passado = 0
                                horas = int(tempo_passado // 3600)
                                minutos = int((tempo_passado % 3600) // 60)
                                tempo_decorrido = f"{horas:02d}:{minutos:02d}"

                                sql_sqlite.execute("SELECT nome_apl FROM aplic_bloc WHERE codigo_apl = ?", (pacote_para_bloquear,))
                                resultado = sql_sqlite.fetchone()
                                # Verificar se encontrou um resultado
                                if resultado:
                                    nome_app = resultado[0]
                                    horas_de_bloqueio = read_config_value("conf/lista_apps_config.ini", f"{nome_app}", "btn1")

                                try:
                                    horas_de_bloqueio_int = int(horas_de_bloqueio[0:2])
                                    minutos_de_bloqueio_int = int(horas_de_bloqueio[3:5])
                                    # Verifica se chegou no horário de desbloquear o aplicativo
                                    if tempo_decorrido >= horas_de_bloqueio:
                                        bloquear_aplicativo()
                                        if horas >= horas_de_bloqueio_int and minutos >= minutos_de_bloqueio_int:
                                            bloquear_aplicativo()
                                    else:
                                        pass
                                        # save_config_value("conf/config.ini", "STATE", "hora_atual_bloc_switch", "True")
                                except:
                                    pass
                    #####################################


                    #####################################
                    if status_bloqueio == "LIBERAR_POR_HORARIO":
                        if read_config_value("conf/config.ini", "STATE", "bloquear_horarios") == "False":
                            # Obter o inicio do primeiro horario do bloqueio
                            if sql_sqlite:
                                sql_sqlite.execute("SELECT nome_apl FROM aplic_bloc WHERE codigo_apl = ?", (pacote_para_bloquear,))
                                resultado = sql_sqlite.fetchone()
                                if resultado:
                                    nome_app = resultado[0]
                                    inicio_bloqueio_1     = read_config_value("conf/lista_apps_config.ini", f"{nome_app}", "btn2")
                                    termino_do_bloqueio_1 = read_config_value("conf/lista_apps_config.ini", f"{nome_app}", "btn3")
                                    inicio_bloqueio_2     = read_config_value("conf/lista_apps_config.ini", f"{nome_app}", "btn4")
                                    termino_do_bloqueio_2 = read_config_value("conf/lista_apps_config.ini", f"{nome_app}", "btn5")
                                    inicio_bloqueio_3     = read_config_value("conf/lista_apps_config.ini", f"{nome_app}", "btn6")
                                    termino_do_bloqueio_3 = read_config_value("conf/lista_apps_config.ini", f"{nome_app}", "btn7")
                                    inicio_bloqueio_4     = read_config_value("conf/lista_apps_config.ini", f"{nome_app}", "btn8")
                                    termino_do_bloqueio_4 = read_config_value("conf/lista_apps_config.ini", f"{nome_app}", "btn9")

                            # Obter a hora atual
                            hora_atual_2 = datetime.now()
                            # Formatar e imprimir apenas a hora e os minutos
                            hora_minutos_2 = hora_atual_2.strftime("%H:%M")
                            
                            # Verifica se chegou no horário de desbloquear o aplicativo
                            if inicio_bloqueio_1 == hora_minutos_2:
                                bloqueio_1 = True
                            if hora_minutos_2 == termino_do_bloqueio_1:
                                bloqueio_1 = False  

                            if inicio_bloqueio_2 == hora_minutos_2:
                                bloqueio_2 = True
                            if hora_minutos_2 == termino_do_bloqueio_2:
                                bloqueio_2 = False
                                
                            if inicio_bloqueio_3 == hora_minutos_2:
                                bloqueio_3 = True
                            if hora_minutos_2 == termino_do_bloqueio_3:
                                bloqueio_3 = False
                                
                            if inicio_bloqueio_4 == hora_minutos_2:
                                bloqueio_4 = True
                            if hora_minutos_2 == termino_do_bloqueio_4:
                                bloqueio_4 = False

                            if bloqueio_1 == True:
                                # if pacote_aberto_atualmente == pacote_para_bloquear:
                                bloquear_aplicativo()
                            elif bloqueio_2 == True:
                                # if pacote_aberto_atualmente == pacote_para_bloquear:
                                bloquear_aplicativo()
                            elif bloqueio_3 == True:
                                # if pacote_aberto_atualmente == pacote_para_bloquear:
                                bloquear_aplicativo()
                            elif bloqueio_4 == True:
                                # if pacote_aberto_atualmente == pacote_para_bloquear:
                                bloquear_aplicativo()
                            # save_config_value("conf/config.ini", "STATE", "bloquear_horarios", "True")
                    #####################################
                    